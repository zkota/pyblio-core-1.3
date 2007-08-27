"""
Interface to ISI Web of Knowledge.

"""

from twisted.web import client
from twisted.internet import defer
from twisted.python import failure

from Pyblio import Compat

import urllib, sys, logging

from gettext import gettext as _

from Pyblio.Exceptions import QueryError
from Pyblio.Parsers.Semantic.WOK import Reader
from Pyblio.External.HTTP import HTTPRetrieve
from Pyblio.External import IExternal


def _xml(data):
    """ Parse the result from the server, and immeditately catch
    possible errors."""

    tree = Compat.ElementTree.XML(data)

    err = tree.find('./error')
    if err is not None:
        raise QueryError(err.text)

    return tree

def _r_info(tree):
    """ Return (number of hits, number of searched records)."""

    stats = [ int(tree.findtext(f)) for f in
              ('./searchResults/recordsFound',
               './searchResults/recordsSearched') ]
    
    return stats, tree.findtext('./sessionID')


class WOK(IExternal):
    """ I represent a query session on the Web of Knowledge.

    The session is connected to a database whose schema is
    'org.pybliographer/wok/...'.

    """

    schema = 'org.pybliographer/wok/0.1'

    # This base URL is for IP-based authentification. Don't know how
    # other systems work.
    baseURL = "http://estipub.isiknowledge.com/esti/cgi"

    # Maximal number of results one can ask in a single result set.
    MAX_PER_BATCH = 100

    log = logging.getLogger('pyblio.external.wok')
    
    def __init__(self, db):
        self.reader = Reader()
        self.db = db

        self._pending = None
        self._debug = False
        return


    def _query(self, **args):

        assert not self._pending
        assert 'query' in args
        
        self._running = True
        
        data = {
            'databaseID': 'WOS',
            'rspType': 'xml',
            'method': 'searchRetrieve',
            'firstRec': '1',
            'numRecs': self.MAX_PER_BATCH,
            'depth': '',
            'editions': '',
            'fields': '',
            }

        data.update(args)

        self.log.debug('sending query %s' % repr(data))
        
        # ensure all arguments are utf8 encoded
        for k, v in data.items():
            if isinstance(v, unicode):
                data[k] = v.encode('utf-8')
                
        q = self.baseURL + '?' + urllib.urlencode(data)
        
        self._pending = HTTPRetrieve(q, method='GET')
        
        return self._pending.deferred


    def _done(self, data):
        """ Called in any case to mark the end of a pending request to
        the WOK server."""
        self._pending = None
        return data


    def count(self, query):
        """ Ask WOK for the number of results of a given query."""

        d = self._query(query=query, numRecs=1, Logout='yes')

        def process(tree):
            return _r_info(tree)[0][0]
        
        if self._debug:
            def show(data):
                sys.stderr.write(data)
                return data
            d = d.addCallback(show)

        return d.addBoth(self._done).\
               addCallback(_xml).\
               addCallback(process)

    
    def search(self, query, maxhits=500):
        """ Start a query on the WOK, and fill in the database with
        the matches.

         @arg  query: the query, in Web of Science format
         @type query: unicode string
         
         @return: a deferred that will fire when the query is
         finished.
        """

        assert not self._pending
        assert maxhits > 0

        self._first = 1
        self._to_fetch = None
        
        # Limit our initial query to the max per batch amount.
        data = {'query': query,
                'firstRec': self._first,
                'numRecs': min(self.MAX_PER_BATCH, maxhits)}

        # We know we won't have to continue this session.
        if maxhits < self.MAX_PER_BATCH:
            data['Logout'] = 'yes'
        
        results = defer.Deferred()

        rs = self.db.rs.new()
        rs.name = _('Imported from Web of Knowledge')


        def failed(failure):
            results.errback(failure)

        # We retrieve a first result containing the total, which might
        # lead to more hits afterward.
        def received(tree):
            stats, sessionID = _r_info(tree)
            found, total = stats

            if self._to_fetch is None:
                # Now, we know how much records we are supposed to fetch
                self._to_fetch = min(found, maxhits)
                
            self.log.debug('session %s: received batch (%d pending)' % (
                repr(sessionID), self._to_fetch))

            self.reader.parse(tree.find('./records'), self.db, rs)

            parsed = len(rs)
            missing = self._to_fetch - parsed
            
            # Are we supposed to continue the current query?
            if missing <= 0:
                # If not, the main deferred returns the result set and
                # the stats, as the DB itself has been modified in the
                # meantime.
                results.callback(found)
                return

            # We can ajust the query more tightly
            data['firstRec'] = 1 + parsed
            data['numRecs'] = min(self.MAX_PER_BATCH, missing)
            data['SID'] = sessionID

            if missing < self.MAX_PER_BATCH:
                data['Logout'] = 'yes'

            d = self._query(**data).addBoth(self._done)
            
            d.addCallback(_xml).\
                addCallback(received).\
                addErrback(failed)
            return
            
        # start the query process
        d = self._query(**data).addBoth(self._done)

        d.addCallback(_xml).\
            addCallback(received).\
            addErrback(failed)
        
        return results, rs
    

    def cancel(self):
        """ Cancel a running query. The database is not reverted to its
        original state."""
        if not self._pending:
            return

        self._pending.cancel()
        self._pending = None
        return
    
    
        
