# -*- coding: latin-1 -*-

import os, pybut, sys
import StringIO

from Pyblio.Importers import BibTeX
from Pyblio import Store, Schema

class WithComments (BibTeX.Importer):

    def __init__ (self, charset):

        BibTeX.Importer.__init__ (self, charset = charset)

        self.comments = []
        return

    
    def comment_add (self, data):

        self.comments.append (data)
        return
    

class TestBibTeXImport (pybut.TestCase):

    """ Perform tests on the Pyblio.Importers.BibTeX module """

    def _check (self, base):

        f = pybut.dbname ()

        s = Schema.Schema ('ut_bibtex/schema.xml')
        
        db = Store.get ('file').dbcreate (f, s)

        # Add a few document types
        g = db.txo ['doctype']
        
        for t in ('Article',):
            dt = Store.TxoItem ()
            dt.names [''] = t

            g.add (dt)

        self.parser = WithComments (charset = 'latin-1')

        self.parser.parse (open ('ut_bibtex/%s.bib' % base), db)
        
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

        expected = [u' This is a comment',
                    u' This is a { comment too',
                    u' {mee too}',
                    u" Comments in the middle won't be kept",
                    u' (parenthesis are also allowed)']
        
        self._check ('comment')

        assert self.parser.comments == expected, \
               'got %s' % self.parser.comments
        return

    def testNested (self):
        """ Check for nested braces """
        
        self._check ('nested')
        return

    def testEmpty (self):
        """ Support empty braces """
        
        self._check ('empty')
        return

    def testSharp (self):
        """ Support concatenation """
        
        self._check ('sharp')
        return


class TestBibTeXExport (pybut.TestCase):

    def _check (self, base):

        f = pybut.dbname ()

        db = Store.get ('file').dbopen ('ut_bibtex/%s.xml' % base)
        fd = open (f, 'w')
        
        self.writer = BibTeX.Exporter (charset = 'latin-1')
        
        self.writer.write (fd, db.entries, db)

        fd.close ()
        
        pybut.fileeq (f, 'ut_bibtex/%s.bib' % base)
        return

    def testEmpty (self):

        self._check ('exp-simple')
        return
    
        
suite = pybut.suite (TestBibTeXImport, TestBibTeXExport)

if __name__ == '__main__':  pybut.run (suite)
