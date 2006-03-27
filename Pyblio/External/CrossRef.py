"""
An asynchronous query module to get DOI numbers given publication information.

This module connects to http://crossref.org/ and tries to resolve DOI
numbers given fuzzy publication informations like journal title,
volume, year and start page.
"""

from twisted.web import client
from twisted.internet import reactor, defer
from twisted.python import failure

import random
import urllib

class DOIQuery(object):

    """ Query DOI numbers.

    Convenience module that properly groups queries to CrossRef in
    order to increase throughput.

    >>> cnx = DOIQuery(user=..., pwd=...)
    >>> for info in to_resolve:
    ...     cnx.journalSearch(...).addCallback(got_results)
    >>> cnx.finished()

    The actual queries take place when enough searches have been
    requested, or when the .finished() method is called.

    For each query, a list of possible DOIs is returned. It can
    possibly be empty if the citation could not be resolved.

    In case of a failure in the query protocol itself, the registered
    errback handlers are called for each query.
    """
    
    # Maximal number of queries to send in a single batch
    BATCH = 30

    baseURL = 'http://doi.crossref.org/servlet/query'
    
    def __init__(self, user, pwd):
        self.user = user
        self.pwd  = pwd

        self._pending = {}
        self._uid = 0
        self._queue = []
        return

    def _send(self):

        enqueued = self._queue
        self._queue = []

        data = {
            'usr': self.user,
            'pwd': self.pwd,
            'qdata': '\n'.join([x[1] for x in enqueued])
            }

        req = client.getPage(
            self.baseURL, method='POST',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            postdata=urllib.urlencode(data))


        def received(data):
            r = {}

            for line in data.split('\n'):
                line = line.strip()
                if not line: continue

                try:
                    parts = line.split('|')
                    key, doi = parts[-2:]

                    key = int(key)
                    doi = doi.strip()
                    
                except (IndexError, ValueError):
                    continue

                if doi:
                    r.setdefault(key, []).append(doi)

            # trigged the deferred of _all_ the clients of this batch
            for uid, q in enqueued:
                self._pending[uid].callback(r.get(uid, []))
                del self._pending[uid]

            return

        def failed(reason):
            for uid, q in enqueued:
                self._pending[uid].errback(reason)
                del self._pending[uid]
            return


        req.addCallback(received).addErrback(failed)
        return
    
    def _prepare(self, q):
        d = defer.Deferred()
        
        self._pending[self._uid] = d
        self._queue.append((self._uid, q))
        self._uid += 1


        if len(self._queue) >= self.BATCH:
            self._send()
            
        return d

    def finished(self):
        self._send()

    def journalSearch(self, issn='', title='',
                      author='', volume='',
                      issue='', startpage='',
                      year=''):
        
        q = '|'.join([
            issn, title, author, volume, issue, startpage,
            year, 'full_text', str(self._uid), ''])

        return self._prepare(q)
    

    def bookSearch(self, isbn='', serial='', title='', author='', volume='',
                   edition='', page='', year='', part=''):

        q = '|'.join([
            isbn, serial, title, author, volume, edition, page,
            year, part, 'full_text', str(self._uid), ''])

        return self._prepare(q)

