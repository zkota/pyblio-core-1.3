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

import logging

from Pyblio import Store, Attribute


class DOIQuery(object):

    """ Query DOI numbers.

    Convenience module that properly groups queries to CrossRef in
    order to increase throughput.

    >>> cnx = DOIQuery(db, user=..., pwd=...)
    >>> for info in to_resolve:
    ...     cnx.journalSearch(...).addCallback(got_results)
    >>> cnx.finished()

    The 'db' parameter is a database from which the queries and
    results will be composed. It must conform to the

       'org.pybliographer/crossref/0.1'

    schema.
    
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


    log = logging.getLogger('pyblio.external.crossref')
    
    def __init__(self, db, user, pwd):
        self.db   = db
        self.user = user
        self.pwd  = pwd

        self._pending = {}
        self._uid = 0
        self._queue = []

        # This holds the pending batchs to submit to the remote system
        self._batch = []

        self._running = False
        
        self._finished = None
        self._stats = [0, 0]
        return

    def _make_batch(self):

        enqueued = self._queue
        self._queue = []

        self._batch.append(enqueued)
        
        if not self._running:
            self._running = True
            self._send()
        return

    def _send(self):

        try:
            enqueued = self._batch.pop()
        except IndexError:
            self._running = False
            return

        self.log.debug('sending a new batch to the server')
        
        data = {
            'usr': self.user,
            'pwd': self.pwd,
            'qdata': '\n'.join([x[1] for x in enqueued]).encode('utf-8')
            }

        req = client.getPage(
            self.baseURL, method='POST',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            postdata=urllib.urlencode(data))


        def received(data):
            self.log.debug('received a batch from the server')
            
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

                if key not in self._pending:
                    raise ValueError('key %s received while not expected' % repr(key))

                lp = len(parts)
                
                if lp not in (10, 12):
                    raise ValueError('result %s has not the expected syntax' % repr(line))

                if not doi:
                    self.log.debug('no DOI for key %s (%s)' % (repr(key), repr(line)))
                    continue
                
                # recreate a proper record given the fields
                rec = Store.Record()
                def one(field, val):
                    if val:
                        rec.add(field, val, Attribute.Text)
                    return

                def person(val):
                    return Attribute.Person(last=val)

                def year(val):
                    return Attribute.Date(year=int(val))
                
                rec.add('doi', doi, Attribute.ID)

                tp = self.db.txo['doctype'].byname
                
                if lp == 10:
                    rec.add('doctype', tp('article'), Attribute.Txo)
                    one('issn', parts[0])
                    one('title', parts[1])
                    rec.add('author', parts[2], person)
                    one('volume', parts[3])
                    one('issue', parts[4])
                    one('startpage', parts[5])
                    rec.add('year', parts[6], year)

                else:
                    rec.add('doctype', tp('book'), Attribute.Txo)
                    one('isbn', parts[0])
                    one('serial', parts[1])
                    one('title', parts[1])
                    rec.add('author', parts[2], person)
                    one('volume', parts[3])
                    one('edition', parts[4])
                    one('startpage', parts[5])
                    rec.add('year', parts[6], year)
                    one('part', parts[7])
                    
                r.setdefault(key, []).append(rec)

                
            # trigger the deferred of _all_ the clients of this batch
            for uid, q in enqueued:
                self._pending[uid].callback(r.get(uid, []))
                del self._pending[uid]

            self._stats[0] += len(enqueued)
            self._batch_done()
            return

        def failed(reason):
            self.log.debug('too bad, the batch failed: %s' % str(reason))
            
            for uid, q in enqueued:
                self._pending[uid].errback(reason)
                del self._pending[uid]
                
            self._stats[1] += len(enqueued)
            self._batch_done()
            return

        req.addCallback(received).addErrback(failed)
        return

    def _batch_done(self):
        if self._finished and not self._pending:
            self._finished.callback(self._stats)

        self._send()
        return
    
    def _prepare(self, q):
        d = defer.Deferred()
        
        self._pending[self._uid] = d
        self._queue.append((self._uid, q))
        self._uid += 1

        if len(self._queue) >= self.BATCH:
            self._make_batch()
            
        return d

    def finished(self):
        assert not self._finished, 'finished() called twice'
        self._make_batch()

        self._finished = defer.Deferred()
        return self._finished
    
    def search(self, record):
        assert not self._finished, 'finished() already called'
        
        t = record['doctype'][0]
        t = self.db.txo[t.group][t.id].names['C']

        def one(field):
            return record.get(field, [''])[0]
        
        if t == 'article':
            issn = one('issn')
            title = one('title')
            volume = one('volume')
            issue = one('issue')
            startpage = one('startpage')

            try:
                year = str(record['year'][0].year)
            except KeyError:
                year = ''

            try:
                author = record['author'][0].last
            except KeyError:
                author = ''
            
            q = '|'.join([
                issn, title, author, volume, issue, startpage,
                year, 'full_text', str(self._uid), ''])

        elif t == 'book':
            isbn = one('isbn')
            serial = one('serial')
            title = one('title')
            volume = one('volume')
            edition = one('edition')
            page = one('startpage')
            part = one('part')

            try:
                year = str(record['year'][0].year)
            except KeyError:
                year = ''

            try:
                author = record['author'][0].last
            except KeyError:
                author = ''

            q = '|'.join([
                isbn, serial, title, author, volume, edition, page,
                year, part, 'full_text', str(self._uid), ''])

        else:
            raise ValueError('cannot search for doctype %s' % repr(t))

        return self._prepare(q)
    

