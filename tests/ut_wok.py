# -*- coding: utf-8 -*-

import pybut, sys, os, logging

from Pyblio.External import WOK
from Pyblio import Store, Attribute, Registry

from twisted.web import http
from twisted.internet import reactor
from twisted.python import log
from twisted.trial import unittest

base = os.path.abspath('ut_wok')

class MyWOK(http.Request):

    def process(self):
        if self.path.startswith('/broken'):
            # return an error code
            err = os.path.join(base, 'error.xml')
            self.write(open(err).read())

        else:
            start = self.args.get('firstRec', ['1'])[0]
            f = os.path.join(base, 'r-' + start + '.xml')
            self.write(open(f).read())
            
        self.setResponseCode(http.OK)
        self.finish()
        return
    
class MyChannel(http.HTTPChannel):
    requestFactory = MyWOK

class Server(http.HTTPFactory):
    protocol = MyChannel


# To activate more debugging:
#
#log = logging.getLogger('pyblio')
#log.setLevel(logging.DEBUG)


class TestFakeWOK(unittest.TestCase):

    def setUp(self):
        Registry.parse_default()

        s = Registry.getSchema('org.pybliographer/wok/0.1')
        fmt = Store.get('memory')

        self.db = fmt.dbcreate(None, s)

        self.cnx = WOK.WOK(self.db)
        self.port = reactor.listenTCP(8000, Server())

        self.cnx.baseURL = 'http://localhost:8000/esti'
        return

    def tearDown(self):
        self.port.stopListening()
        Registry.reset()
        return

    def testFailure(self):
        """ Check that error codes are properly detected."""
        
        self.cnx.baseURL = 'http://localhost:8000/broken'
        d = self.cnx.count(query='Author=(Gobry)')

        def check(e):
            if e.check(unittest.FailTest):
                return e
            
        return d.addCallback(self.fail).addErrback(check)
    
    def testCount(self):
        """ Return the result count for a query."""

        d = self.cnx.count(query='Author=(Gobry)')

        def check(count):
            self.failUnlessEqual(count, 1641)
            
        return d.addCallback(check)
    
    def testQuery(self):
        """ Return the result count for a query."""

        d, rs = self.cnx.search(query='TS=(peer to peer)', maxhits=250)

        def done(total):
            self.failUnlessEqual(total, 1641)
            self.failUnlessEqual(len(rs), 250)
            
            tmp = pybut.dbname()
            fd = open(tmp, 'w')
            self.db.xmlwrite(fd)
            fd.close()

            pybut.fileeq(tmp, pybut.fp('ut_wok', 'result.bip'))
            
        return d.addCallback(done)
    
    
