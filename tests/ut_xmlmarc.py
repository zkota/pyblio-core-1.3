# -*- coding: latin-1 -*-

import os, pybut, sys

from Pyblio.Parsers.Syntax import XMLMARC
from Pyblio import Store, Schema

SI = XMLMARC.SimpleReader

mapping = {

    001                 : 'marc-id',
    (245, '', '', 'a')  : 'title',
    (700, '', '', 'a')  : 'author',
    (773, '', '', 'p')  : 'journal',
    (856, '4', '', 'u') : 'url',

    }

class TestImport (pybut.TestCase):

    """ Perform tests on the Pyblio.Parsers.Syntax.BibTeX module """

    def _check (self, base):

        f = pybut.dbname ()

        s = Schema.Schema (pybut.src('ut_xmlmarc/schema.xml'))
        
        db = Store.get ('file').dbcreate (f, s)

        self.parser =  XMLMARC.SimpleReader (mapping)

        self.parser.parse (open (pybut.src('ut_xmlmarc/%s.xml' % base)), db)
        
        db.save ()
        
        pybut.fileeq (f, pybut.src('ut_xmlmarc/r-%s.xml' % base))

        Store.get ('file').dbdestroy (f, nobackup = True)
        return

    def testBase (self):

        self._check ('simple')
        
    def testControl (self):
        """ handling of control fields """
        self._check ('control')
        


suite = pybut.suite (TestImport)

if __name__ == '__main__':  pybut.run (suite)
