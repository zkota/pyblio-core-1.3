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

        s = Schema.Schema ('ut_bibtex/schema.xml')
        
        db = Store.get ('file').dbcreate (f, s)

        # Add a few document types
        g = db.enum.add ('doctype')
        
        for t in ('Article',):
            dt = Store.EnumItem ()
            dt.names [''] = t

            g.add (dt)
        
        BibTeX.file_import ('ut_bibtex/%s.bib' % base, 'latin-1', db)

        db.save ()
        
        pybut.fileeq (f, 'ut_bibtex/%s.xml' % base)

        Store.get ('file').dbdestroy (f, nobackup = True)
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

    def testShqrp (self):
        """ Support concatenation """
        
        self._check ('sharp')
        return

    
pybut.run (pybut.makeSuite (TestBibTeX, 'test'))
