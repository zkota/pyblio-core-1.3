# -*- coding: latin-1 -*-

import os, pybut, sys
import StringIO

from Pyblio.Importers import BibTeX
from Pyblio import Store, Schema

class TestBibTeX (pybut.TestCase):

    """ Perform tests on the Pyblio.Importers.BibTeX module """
    
    def testSimple (self):
        ''' Read a bibtex file with simple properties '''

        f = ',,t1.xml'
        
        s = Schema.Schema ('../Schemas/bibtex.xml')
        
        db = Store.Database (schema = s)

        BibTeX.file_import ('ut_bibtex/simple.bib', 'latin-1', db)

        fd = open (f, 'w')
        db.xmlwrite (fd, schema = False)
        fd.close ()

        pybut.fileeq (f, 'ut_bibtex/simple.xml')
        os.unlink (f)
        return

    def testComment (self):

        f = ',,t2.xml'
        
        s = Schema.Schema ('../Schemas/bibtex.xml')
        
        db = Store.Database (schema = s)

        BibTeX.file_import ('ut_bibtex/comment.bib', 'latin-1', db)

        fd = open (f, 'w')
        db.xmlwrite (fd, schema = False)
        fd.close ()

        pybut.fileeq (f, 'ut_bibtex/comment.xml')
        os.unlink (f)
        return

    
pybut.run (pybut.makeSuite (TestBibTeX, 'test'))
