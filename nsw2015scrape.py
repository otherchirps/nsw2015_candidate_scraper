import os
import time

from collections import defaultdict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from models import (
    Base, Person, District, Party, Group, LegislativeAssembly,
    LegislativeCouncil
)

from dao import engine, db_session

# NOTE: requires phantomjs to be available
#   eg. npm install -g phantomjs

candidates_base_url = "http://candidates.elections.nsw.gov.au/"

def wait_asp_postback(driver):
    """ Eek! Hackety hack...

    Our target page is chock-full of ASP.NET ajax postbacks, instead of
    actual links.

    These are the main reason we've needed to resort to selenium to
    scrape in the first place: javascript execution.

    However, these are also horribly tricky for selenium to determine
    completion status.

    So, we can:
        1. wait some arbitrary amount of time, and/or
        2. use some asp.net specific hacks to see if their ajax calls
           are finished.

    There's already a max timeout in place, so this function performs
    the asp.net hack side of things.

    This under-the-hood workaround courtesy of:
        https://www.neustar.biz/blog/selenium-tips-wait-with-waitforcondition
    """
    result = driver.execute_script(
        "return window.Sys.WebForms.PageRequestManager.getInstance().get_isInAsyncPostBack() === false;"
    )
    print("> asp.net ajax finished: {0}".format(result))
    return result

class Task(object):

    MODEL = None
    HEADER_MAP = None

    def __init__(self, browser):
        self.browser = browser

    def run(self):
        self.navigate_all_candidates()

        with db_session() as session:
            for candidate_info in self.get_candidates(session):
                model = self.MODEL(**candidate_info)
                session.add(model)
                session.flush()
                self.update_progress(model)

    def get_candidates(self):
        """ Must return a dict(model.field: field_value)
        """
        raise NotImplementedError("subclass must provide")

    def navigate_home(self):
        print("[NAV] {}".format(candidates_base_url))
        self.browser.get(candidates_base_url)

    def navigate_all_candidates(self):
        self.navigate_home()
        print("[NAV] Waiting on page load")
        candidates_link = WebDriverWait(self.browser, 20).until(
            EC.presence_of_element_located(self.ALL_CANDIDATES_LINK)
        )
        print("[NAV] click")
        candidates_link.click()

        print("[NAV] show all...")
        show_all = WebDriverWait(self.browser, 20).until(
            EC.presence_of_element_located(self.SHOW_ALL_LINK)
        )
        print("[NAV] click")
        show_all.click()

        # Custom wait hack for the ASP.NET ajax shananigans.
        # If it takes more than 30 seconds.... bail.
        WebDriverWait(self.browser, 30).until(
            wait_asp_postback
        )
        print "[NAV] done."

    def parse_row(self, row):
        result = defaultdict(str)

        for cell in row.find_elements(By.XPATH, "./td[@headers]"):
            field_name = self.HEADER_MAP.get(cell.get_attribute("headers"), None)
            if field_name and cell.text:
                result[field_name] = cell.text

        return result

    def get_rows(self):
        for row in self.browser.find_elements(*self.CANDIDATE_ROWS):
            yield self.parse_row(row)

    def get_person(self, session, row):
        return self.get_or_create(
            session, Person,
            filters=[
                Person.ballot_name == row['ballot_name'],
                Person.locality == row['locality']
            ],
            ballot_name=row['ballot_name'],
            locality=row['locality'],
            phone=row['phone'],
            mobile=row['mobile'],
            website=row['website'],
            email=row['email']
        )

    def get_or_create(self, session, model, filters=None, **kwargs):
        try:
            if filters:
                query = session.query(model)
                for f in filters:
                    query = query.filter(f)
                result = query.one()
            else:
                raise NoResultFound
        except NoResultFound:
            result = model(**kwargs)
            session.add(result)
        return result


class LegislativeAssemblyTask(Task):
    ALL_CANDIDATES_LINK = (By.ID, "ctl00_cphContent_rptHomePage_ctl00_rptAreaType_ctl00_lbBySurname")
    SHOW_ALL_LINK = (By.XPATH, "//a[b[contains(text(), 'Show All')]]")
    CANDIDATE_ROWS = (By.XPATH, "//tr[contains(@id, '_rptCandidatesBySurnameRow_')]")

    MODEL = LegislativeAssembly

    HEADER_MAP = {
        'CANDIDATEBALLOTNAME': 'ballot_name',
        'LOCALITY': 'locality',
        'CONTESTAREACODE': 'district',
        'AFFILIATION': 'party',
        'PHONE': 'phone',
        'MOBILE': 'mobile',
        'WEBSITE': 'website',
        'EMAIL': 'email'
    }

    def get_candidates(self, session):

        for row in self.get_rows():

            district = None
            party = None
            candidate = None

            if row['district']:
                district = self.get_or_create(
                    session, District,
                    filters=[District.name == row['district']],
                    name=row['district']
                )

            if row['party']:
                party = self.get_or_create(
                    session, Party,
                    filters=[Party.name == row['party']],
                    name=row['party']
                )

            candidate = self.get_person(session, row)
            if party:
                candidate.party = party

            yield dict(
                person=candidate,
                district=district
            )

    def update_progress(self, candidate):
        print("assembly: {0.person.ballot_name}, {0.person.locality}".format(candidate))


class LegislativeCouncilTask(Task):
    ALL_CANDIDATES_LINK = (By.ID, "ctl00_cphContent_rptHomePage_ctl00_rptAreaType_ctl01_lbBySurname")
    SHOW_ALL_LINK = (By.XPATH, "//a[b[contains(text(), 'Show All')]]")
    CANDIDATE_ROWS = (By.XPATH, "//tr[contains(@id, '_rptCandidatesBySurnameRow_')]")

    MODEL = LegislativeCouncil

    HEADER_MAP = {
        'CANDIDATEBALLOTNAME': 'ballot_name',
        'LOCALITY': 'locality',
        'GROUPLABEL': 'group',
        'GROUPNAME': 'group_name',
        'AFFILIATION': 'party',
        'PHONE': 'phone',
        'MOBILE': 'mobile',
        'WEBSITE': 'website',
        'EMAIL': 'email'
    }

    def get_candidates(self, session):

        for row in self.get_rows():

            group = None
            party = None
            candidate = None

            if row['group']:
                group = self.get_or_create(
                    session, Group,
                    filters=[Group.identifier == row['group']],

                    identifier=row['group'],
                    name=row['group_name']
                )

            if row['party']:
                party = self.get_or_create(
                    session, Party,
                    filters=[Party.name == row['party']],
                    name=row['party']
                )

            candidate = self.get_person(session, row)
            if party:
                candidate.party = party

            yield dict(
                person=candidate,
                group=group
            )

    def update_progress(self, candidate):
        print("council: {0.person.ballot_name}, {0.person.locality} [{1}]".format(
            candidate, candidate.group.name if candidate.group else ''
        ))


def main():
    Base.metadata.create_all(engine)

    browser = webdriver.PhantomJS()
    browser.implicitly_wait(10)
    try:
        tasks = [
            LegislativeAssemblyTask,
            LegislativeCouncilTask
        ]
        for task in tasks:
            task(browser).run()
    finally:
        browser.quit()

if __name__ == "__main__":
    main()

