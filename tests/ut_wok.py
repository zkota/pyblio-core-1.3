# -*- coding: utf-8 -*-

import pybut, sys, os

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
            start = self.args.get('startRec', '1')
            f = os.path.join(base, 'r-' + start + '.xml')
            self.write(open(f).read())
            
        self.setResponseCode(http.OK)
        self.finish()
        return
    
class MyChannel(http.HTTPChannel):
    requestFactory = MyWOK

class Server(http.HTTPFactory):
    protocol = MyChannel



class TesFakeWOK(unittest.TestCase):

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
        
        return d.addCallback(self.fail).addErrback(lambda x: None)
    
    def testCount(self):
        """ Return the result count for a query."""

        d = self.cnx.count(query='Author=(Gobry)')

        def check(count):
            self.failUnlessEqual(count[0], 20)
            
        return d.addCallback(check)
    
    
