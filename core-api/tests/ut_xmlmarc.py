# -*- coding: latin-1 -*-

import os, pybut, sys

from Pyblio.Importers import XMLMARC
from Pyblio import Store, Schema

SI = XMLMARC.SimpleImporter

mapping = {

    (245, '', '', 'a')  : 'title',
    (700, '', '', 'a')  : 'author',
    (773, '', '', 'p')  : 'journal',
    (856, '4', '', 'u') : 'url',

    }

class TestImport (pybut.TestCase):

    """ Perform tests on the Pyblio.Importers.BibTeX module """

    def _check (self, base):

        f = pybut.dbname ()

        s = Schema.Schema ('ut_xmlmarc/schema.xml')
        
        db = Store.get ('file').dbcreate (f, s)

        self.parser =  XMLMARC.SimpleImporter (mapping)

        self.parser.parse (open ('ut_xmlmarc/%s.xml' % base), db)
        
        db.save ()
        
        pybut.fileeq (f, 'ut_xmlmarc/r-%s.xml' % base)

        Store.get ('file').dbdestroy (f, nobackup = True)
        return

    def testBase (self):

        self._check ('simple')
        


suite = pybut.suite (TestImport)

if __name__ == '__main__':  pybut.run (suite)
