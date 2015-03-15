import csv

from dao import db_session
from models import (
    LegislativeCouncil, LegislativeAssembly
)

def create_csv(filename, rows, headers=None):
    with open(filename, "w+") as csvfile:
        writer = csv.writer(csvfile)
        if headers:
            writer.writerow(headers)
        writer.writerows(rows)

def create_assembly(filename):
    with db_session() as session:

        rows = session.query(LegislativeAssembly).all()
        create_csv(
            filename, (
                (
                    row.person.ballot_name,
                    row.person.locality,
                    row.district.name,
                    row.person.party.name if row.person.party else None,
                    row.person.phone,
                    row.person.mobile,
                    row.person.website,
                    row.person.email
                )

                for row in rows
            ),
            "ballot_name locality district party phone mobile website email".split()
        )

def create_council(filename):
    with db_session() as session:

        rows = session.query(LegislativeCouncil).all()
        create_csv(
            filename, (
                (
                    row.person.ballot_name,
                    row.person.locality,
                    row.group.identifier if row.group else None,
                    row.group.name if row.group else None,
                    row.person.party.name if row.person.party else None,
                    row.person.phone,
                    row.person.mobile,
                    row.person.website,
                    row.person.email
                )

                for row in rows
            ),
            "ballot_name locality group group_name party phone mobile website email".split()
        )


if __name__ == "__main__":
    create_assembly("assembly.csv")
    create_council("council.csv")
