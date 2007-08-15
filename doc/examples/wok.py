"""
Perform a query on the Web of Science.

Usage: wok.py <Query> <BIP file>

Example:

   python wok.py 'Author=(Gobry)' gobry.bip

"""

import sys

from twisted.internet import reactor

from Pyblio import Registry, Store
from Pyblio.External import WOK

query, output = sys.argv[1:]

# Create a database that is capable of storing Web of Science results.
Registry.load_default_settings()

s = Registry.getSchema('org.pybliographer/wok/0.1')
fmt = Store.get('file')

db = fmt.dbcreate(output, s)

# Initialize the connection to the database
wok = WOK.WOK(db)

# Perform a search. In return, we obtain the result set that will be
# filled in with the results, and a deferred that will fire once the
# query is over.
d, rs = wok.search(query)

def success(total):
    print "wok: successfully fetched %d records" % total
    db.save()

    reactor.stop()

def failure(failure):
    print "wok: sorry, the query failed"
    print failure

    reactor.stop()

# We register the actions to perform upon success and failure
d.addCallback(success).addErrback(failure)

# Showtime! This will exit when reactor.stop() is invoked above.
reactor.run()
