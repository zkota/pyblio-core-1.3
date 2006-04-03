"""
Interface to ISI Web of Knowledge.

"""

from twisted.web import client
from twisted.internet import defer, reactor
from twisted.python import failure

from cElementTree import ElementTree, XML

import urllib, sys

from Pyblio.Exceptions import QueryError

class _Getter(client.HTTPClientFactory):
    def __init__(self, *args, **kargs):
        client.HTTPClientFactory.__init__(self, *args, **kargs)

        self.running = []
        return
    
    def buildProtocol(self, addr):
        p = client.HTTPClientFactory.buildProtocol(self, addr)
        self.running.append(p)
        return p

    def cancel(self):
        self.running[-1].transport.loseConnection()
        return
    

class WOK(object):
    """ I represent a query session on the Web of Knowledge.

    The session is connected to a database whose schema is
    'org.pybliographer/wok/1.0'.

    """

    baseURL = "http://estipub.isiknowledge.com/esti/cgi"

    def __init__(self, db):
        self._sessionID = None
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
            'numRecs': '100',
            'depth': '',
            'editions': '',
            'fields': '',
            }

        data.update(args)
        
        if self._sessionID:
            data['sessionID'] = self._sessionID

        q = self.baseURL + '?' + urllib.urlencode(data)
        
        factory = _Getter(q, method='GET')

        scheme, host, port, path = client._parse(q)
        reactor.connectTCP(host, port, factory)

        self._pending = factory
        
        return factory.deferred


    def _failure(self, failure):
        self._pending = None
        return failure


    def count(self, query):
        """ Ask WOK for the number of results of a given query."""

        d = self._query(query=query, numRecs=1, Logout='yes')

        def process(tree):
            err = tree.find('./error')
            if err is not None:
                raise QueryError(err.text)

            # get the count and the total
            res = int(tree.findtext('./searchResults/recordsFound'))
            tot = int(tree.findtext('./searchResults/recordsSearched'))

            self._pending = None
            return (res, tot)
        
        if self._debug:
            def show(data):
                sys.stderr.write(data)
                return data
            d = d.addCallback(show)

        return d.addCallback(XML).\
               addCallback(process).\
               addErrback(self._failure)

    
    def search(self, query, maxhits=500):
        """ Start a query on the WOK, and fill in the database with
        the matches.

         @arg  query: the query, in Web of Science format
         @type query: unicode string
         
         @return: a deferred that will fire when the query is
         finished.
        """

        assert not self._pending

        data = {'query': query}
        
        if self._sessionID:
            data['sessionID'] = self._sessionID

        d = self._query(**data)

        # We retrieve a first result containing the total, which might
        # lead to more hits afterward.
        
        return

    def cancel(self):
        """ Cancel a running query. The database is not reverted to its
        original state."""
        if not self._pending:
            return

        self._pending.cancel()
        self._pending = None
        return
    
    
        
