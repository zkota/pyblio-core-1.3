# -*- coding: latin-1 -*-

import os, pybut, sys
import StringIO

from Pyblio.Importers import BibTeX
from Pyblio import Store, Schema

class TestBibTeX (pybut.TestCase):

    """ Perform tests on the Pyblio.Importers.BibTeX module """

    count = 0
    
    def _check (self, base):

        f = ',,t%d.xml' % self.count

        TestBibTeX.count = self.count + 1

        s = Schema.Schema ('../Schemas/bibtex.xml')
        
        db = Store.Database (schema = s)
        
        BibTeX.file_import ('ut_bibtex/%s.bib' % base, 'latin-1', db)

        fd = open (f, 'w')
        db.xmlwrite (fd, schema = False)
        fd.close ()
        
        pybut.fileeq (f, 'ut_bibtex/%s.xml' % base)
        os.unlink (f)
        return

    
    def testSimple (self):
        ''' Read a bibtex file with simple properties '''

        self._check ('simple')
        return


    def testComment (self):
        """ Parse bibtex comments """
        
        self._check ('comment')
        return

    def testNested (self):
        """ Check for nested braces """
        
        self._check ('nested')
        return

    def testEmpty (self):
        """ Support empty braces """
        
        self._check ('empty')
        return
    
pybut.run (pybut.makeSuite (TestBibTeX, 'test'))
