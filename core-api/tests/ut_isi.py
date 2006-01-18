# -*- coding: latin-1 -*-

import os, pybut, sys, re

from Pyblio.Importers import ISI, Tagged
from Pyblio import Store, Schema

class Importer (ISI.Importer):

    def __init__ (self):
        ISI.Importer.__init__ (self)
        
        self.mapping = {
            'TI': (self.text_add,   'title'),
            'AU': (self.person_add, 'author'),
            }

    def do_default (self, line, tag, data):

        try:
            meth, field = self.mapping [tag]
        except KeyError:
            return
        
        meth (field, data)
        return


class TestISI (pybut.TestCase):

    def parse (self, file):

        fd = open (file)

        self.fn = pybut.dbname ()
        s = Schema.Schema ('standard.xml')
        self.db = Store.get ('file').dbcreate (self.fn, s)
        
        self.p = Importer ()
        self.p.parse (fd, self.db)
        return
    

    def testText (self):

        self.parse ('ut_isi/text.isi')
        self.db.save ()

        pybut.fileeq (self.fn, 'ut_isi/text.xml')
        return
    


suite = pybut.suite (TestISI)

if __name__ == '__main__':  pybut.run (suite)
