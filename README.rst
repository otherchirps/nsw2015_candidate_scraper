NSW 2015 Candidate Scraper
==========================

The candidate listing has been posted at http://candidates.elections.nsw.gov.au.

But... the webpage given isn't very scraper-friendly. All of the links to the listings
are rendered as javascript postbacks.

Workaround
----------

This script uses `selenium <https://selenium-python.readthedocs.org/index.html>`_, 
in conjunction with `PhantomJS <http://phantomjs.org/>`_, to render the page and work its 
javascript stuff.

There might be a better way... I'd love to know about it, if you've got it.

Requirements
------------

To run this you'll need:

* `Python <http://python.org>`_ (tested with 2.7)
* `pip <https://pip.pypa.io>`_
* `PhantomJS <http://phantomjs.org/>`_ 

Installation
------------

1. Get phantom installed::

   npm install -g phantomjs

2. Install the python requirements via pip (you'll probably want to do this in a `virtualenv <https://virtualenv.pypa.io>`_)::

   pip install -r requirements.txt

Running
-------

In the directory you've unpacked this script:

1. Scrape the site::

   python nsw2015scrape.py

This will generate a little `sqlite <https://sqlite.org>`_ database file (named "candidates.sqlite3"). 
You can use this directly, or view it with something like
`sqlitebrowser <http://sqlitebrowser.org/>`_, or

2. Generate the assembly & council CSV files::

   python nsw2015csv.py

This should spit out assembly.csv and council.csv.

License
-------

This script is a throwaway, written in a hurry to do one thing. 
Do what you'd like with it.  In case you really need a license though, I've released it under the MIT license (see the LICENSE file).


