"""
Perform a query on PubMed, and transform it in BibTeX.

Usage: pubmed2bibtex.py <Query> <BibTeX file>

Example:

   python pubmed2bibtex.py 'Gobry' gobry.bib

"""

import sys, logging

from twisted.internet import reactor

from Pyblio import Registry, Store, Adapter, init_logging
from Pyblio.External import PubMed

# Do you want some debug information?
#init_logging()
#log = logging.getLogger('pyblio')
#log.setLevel(logging.DEBUG)

query, output = sys.argv[1:]

# Create a database that is capable of storing Web of Science results.
Registry.load_default_settings()

s = Registry.getSchema('org.pybliographer/pubmed/0.1')

# Create a temporary in-memory database
fmt = Store.get('memory')
db = fmt.dbcreate(None, s)

# Initialize the connection to the database
remote = PubMed.PubMed(db)

# Perform a search. In return, we obtain the result set that will be
# filled in with the results, and a deferred that will fire once the
# query is over.
d, rs = remote.search(query, maxhits=20)

def success(total):
    print "pubmed: successfully fetched %d/%d records" % (len(db.entries), total)
    reactor.stop()

    # We filled db with pubmed data. To save it as BibTeX, we get an
    # adapter from PubMed to BibTeX
    bibtex = Adapter.adapt_schema(db, 'org.pybliographer/bibtex/0.1')

    # Now we have a "virtual" bibtex database, that we can actually
    # save as a BibTeX file
    from Pyblio.Parsers.Semantic.BibTeX import Writer

    w = Writer()
    w.write(open(output, 'w'), bibtex.entries, bibtex)
    return

def failure(failure):
    print "pubmed: sorry, the query failed"
    print failure

    reactor.stop()

# We register the actions to perform upon success and failure
d.addCallback(success).addErrback(failure)

# Showtime! This will exit when reactor.stop() is invoked above.
reactor.run()
