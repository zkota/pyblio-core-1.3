# -*- coding: utf-8 -*-

import pybut, sys

from Pyblio.External import CrossRef
from Pyblio import Store, Attribute, Registry

from twisted.web import http
from twisted.internet import reactor
from twisted.python import log
from twisted.trial import unittest

class MyCrossRef(http.Request):

    knownDOI = {
        ('', 'Journal of Physical Chemistry B',
         'Su', '109', '', '23925', '2005'): ['abc/123']
        }

    def process(self):
        if self.path != '/query':
            self.setResponseCode(http.NOT_FOUND)
            self.finish()
            return

        try:
            user = self.args['usr'][0]
            pwd  = self.args['pwd'][0]
            qdata = self.args['qdata'][0]
            
        except (KeyError, IndexError), msg:
            log.err('ATTENTION: %s' % str(msg))
            
            self.setResponseCode(http.BAD_REQUEST)
            self.finish()
            return

        # we know some information about a few samples. for those we
        # don't know, return no DOI. For some, return more than one.
        r = []

        for q in qdata.split('\n'):

            parts = q.strip().split('|')

            search, key = tuple(parts[:-3]), parts[-2]
            
            dois = self.knownDOI.get(search, [''])

            for doi in dois:
                parts = list(parts)
                parts[-1] = doi
                r.append('|'.join(parts))

        self.write('\n'.join(r))
        self.setResponseCode(http.OK)
        self.finish()

class MyChannel(http.HTTPChannel):
    requestFactory = MyCrossRef

class Server(http.HTTPFactory):
    protocol = MyChannel



class TestCrossRef(unittest.TestCase):

    def setUp(self):
        Registry.parse_default()

        s = Registry.getSchema('org.pybliographer/crossref/0.1')
        fmt = Store.get('memory')

        self.db = fmt.dbcreate(None, s)

        self.cnx = CrossRef.DOIQuery(self.db, 'user', 'pass')
        self.cnx.baseURL = 'http://localhost:8000/query'
        
        self.port = reactor.listenTCP(8000, Server())
        return

    def tearDown(self):
        self.port.stopListening()
        Registry.reset()
        
    def testJournal(self):
        r = Store.Record()
        r.add('doctype', self.db.schema.txo['doctype'].byname('article'), Attribute.Txo)

        r.add('title', u"Journal of Physical Chemistry B", Attribute.Text)
        r.add('author', Attribute.Person(last=u"Su"))
        r.add('volume', '109', Attribute.Text)
        r.add('startpage', '23925', Attribute.Text)
        r.add('year', Attribute.Date(year=2005))
        
        d = self.cnx.search(r)

        result = []
        
        def done(found):
            self.failUnlessEqual(len(found), 1)
            found = found[0]

            self.failUnlessEqual(found['doi'][0], 'abc/123')

            del found['doi']
            self.failUnlessEqual(found, r)

        d.addCallback(done)

        return self.cnx.finished()
    
    def testMassive(self):

        r = Store.Record()
        r.add('doctype', self.db.schema.txo['doctype'].byname('article'), Attribute.Txo)

        r.add('title', u"Journal of Physical Chemistry B", Attribute.Text)
        r.add('author', Attribute.Person(last=u"Su"))
        r.add('volume', '109', Attribute.Text)
        r.add('startpage', '23925', Attribute.Text)
        r.add('year', Attribute.Date(year=2005))

        result = []

        def done(back):
            result.append(back)

        for i in range(100):
            d = self.cnx.search(r)

            d.addCallback(done)

        d = self.cnx.finished()

        def check(stats):
            self.failUnlessEqual(stats, [100, 0])

        return d.addCallback(check)
        
