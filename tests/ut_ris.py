# -*- coding: latin-1 -*-

import os, pybut, sys, re

from Pyblio.Parsers.Syntax import RIS
from Pyblio import Store, Schema


class TestRIS (pybut.TestCase):

    def parse (self, file):

        fd = open (file)

        self.fn = pybut.dbname ()
        s = Schema.Schema ('standard.xml')
        self.db = Store.get ('file').dbcreate (self.fn, s)
        
        self.p = RIS.Reader ()
        self.p.parse (fd, self.db)
        return
    

    def testText (self):

        self.parse ('ut_ris/text.ris')
        self.db.save ()

        pybut.fileeq (self.fn, 'ut_ris/text.xml')
        return
    


suite = pybut.suite (TestRIS)

if __name__ == '__main__':  pybut.run (suite)
