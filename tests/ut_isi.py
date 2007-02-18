# -*- coding: latin-1 -*-

import os, pybut, sys, re

from Pyblio.Parsers.Semantic import ISI
from Pyblio import Store, Schema, Registry, init_logging

class TestISI (pybut.TestCase):

    def setUp(self):
        Registry.parse_default()

    def tearDown(self):
        Registry.reset()

    def parse (self, file):
        schema = Registry.getSchema("org.pybliographer/wok/0.1")
        
        fd = open (file)

        self.fn = pybut.dbname ()
        self.db = Store.get('file').dbcreate (self.fn, schema)
        
        self.p = ISI.Reader()
        self.p.parse(fd, self.db)
        return
    
    def testText (self):
        self.parse(pybut.src('ut_isi/text.isi'))
        self.db.save ()

        pybut.fileeq(self.fn, pybut.src('ut_isi/text.xml'))
        return

suite = pybut.suite (TestISI)

if __name__ == '__main__':  pybut.run (suite)
