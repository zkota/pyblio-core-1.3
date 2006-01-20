# -*- coding: latin-1 -*-

import os, pybut, sys
import StringIO
from cElementTree import ElementTree

from Pyblio.Parsers.Semantic.BibTeX import Reader
from Pyblio.Parsers.Syntax.BibTeX import Writer

from Pyblio.Parsers.Syntax.BibTeX import Parser

from Pyblio.Parsers.Syntax.BibTeX.Parser import Record, Block, Cmd, Text, Join, Comment, ATComment

from Pyblio import Store, Schema

class WithComments (Reader):

    def __init__ (self, charset):

        Reader.__init__ (self, charset = charset)

        self.comments = []
        return
    
    def comment_add (self, data):

        self.comments.append (data)
        return

    def record_begin (self):
        Reader.record_begin(self)
        self.id_add ('id', self.key)
        

class WithCaseHandler (Writer):

    def record_parse (self, key, value):

        if key in ('title',):
            return self.capitalized_text_add (key, self.record [key])

        return Writer.record_parse (self, key, value)
    

class TestBibTeXReader (pybut.TestCase):


    def _cmp (self, bib, obj):

        io = StringIO.StringIO (bib.encode ('utf-8'))
        re = list (Parser.read (io))

        ri = eval (obj)

        assert ri == re, 'got\n\t %s\n instead of\n\t %s' % (
            repr (re), repr (ri))
        
        
    def testComment (self):

        comment = u'''
% a simple test, h�h�

Random comments
'''
        
        io = StringIO.StringIO (comment.encode ('utf-8'))
        re = list (Parser.read (io))

        assert re == [Parser.Comment (comment)]

    def testArobasComment (self):

        comment = u'@comment (gronf'
        
        io = StringIO.StringIO (comment.encode ('utf-8'))
        re = list (Parser.read (io))

        assert re == [Parser.Comment (' (gronf')], 'got %s' % re

    def testMixed (self):

        c = u'''
toto
@comment gronf
tutu
'''
        io = StringIO.StringIO (c.encode ('utf-8'))
        re = [ type (x) for x in Parser.read (io)]

        assert re == [Parser.Comment, Parser.ATComment, Parser.Comment]

    def testBraces (self):

        b = '''@article { toto, author = { Gobry, {F}. } }'''
        o = """[Record (u'article', u'toto', [(u'author', [Block ('{', [ Text (u' Gobry, '),Block ('{', [Text (u'F')]),Text (u'. ')]) ])])]"""

        self._cmp (b, o)
                   
    def testParen (self):

        b = '''@article ( toto, author = { Gobry, {F}. } )'''
        o = """[Record (u'article', u'toto', [(u'author', [Block ('{', [ Text (u' Gobry, '),Block ('{', [Text (u'F')]),Text (u'. ')]) ])])]"""

        self._cmp (b, o)
                   
    def testQuote (self):

        b = '''@article ( toto, author = " Gobry, {F}. " )'''
        o = """[Record (u'article', u'toto', [(u'author', [Block ('\"', [ Text (u' Gobry, '),Block ('{', [Text (u'F')]),Text (u'. ')]) ])])]"""

        self._cmp (b, o)
                   
    def testQuoteCompact (self):

        b = '''@article(toto,author="Gobry,{F}.")'''
        o = """[Record (u'article', u'toto', [(u'author', [Block ('\"', [ Text (u'Gobry,'),Block ('{', [Text (u'F')]),Text (u'.')]) ])])]"""

        self._cmp (b, o)
                   
    def testString (self):
        
        b = '''@string (gobry="Gobry,{F}.")'''
        o = """[Record (u'string', None, [(u'gobry', [Block ('\"', [ Text (u'Gobry,'),Block ('{', [Text (u'F')]),Text (u'.')]) ])])]"""

        self._cmp (b, o)

    def testJoin (self):
        
        b = '''@article(toto,gobry="Gobry,{F}." # " and Fobry, G.")'''
        o = """[Record (u'article', u'toto', [(u'gobry', Join ([Block ('\"', [Text (u'Gobry,'), Block ('{', [Text (u'F')]), Text (u'.')]), Block ('\"', [Text (u' and Fobry, G.')])]))])]"""

        self._cmp (b, o)

    def testBackslash (self):
        
        b = '''@article(toto, gobry = \"Gobry,\\{F\\}.\" )'''
        o = """[Record (u'article', u'toto', [(u'gobry', Join ([Block ('\"', [Text (u'Gobry,'), Cmd (u'{'), Text (u'F'), Cmd (u'}'), Text (u'.')])]))])]"""

        self._cmp (b, o)

        
class TestBibTeXImport (pybut.TestCase):

    """ Perform tests on the Pyblio.Parsers.Syntax.BibTeX module """

    def _check (self, base):

        f = pybut.dbname ()

        s = Schema.Schema ('../Pyblio/RIP/bibtex.sip')
        
        db = Store.get ('file').dbcreate (f, s)

        # Add a few document types
        g = db.txo ['doctype']
        
        for t in ('Article',):
            dt = Store.TxoItem ()
            dt.names ['C'] = t

            g.add (dt)

        self.parser = WithComments ('latin-1')

        self.parser.parse (open ('ut_bibtex/%s.bib' % base), db)
        
        db.save ()

        # mess a bit with the file to discard the schema
        tree = ElementTree(file=open(f))
        for s in tree.findall('./pyblio-schema'):
            s.clear()
        for s in tree.findall('./txo-group'):
            s.clear()

        tree.write(open(f, 'w'), encoding="utf-8")
        
        pybut.fileeq (f, 'ut_bibtex/%s.xml' % base)

        Store.get ('file').dbdestroy (f, nobackup = True)
        return

    
    def testSimple (self):
        ''' Read a bibtex file with simple properties '''

        self._check ('simple')
        return


    def testComment (self):
        """ Parse bibtex comments """

        expected = [ATComment (u' This is a comment'),
                    Comment (u'\n'),
                    ATComment (u' This is a { comment too'),
                    Comment (u'\n'),
                    ATComment (u' {mee too}'),
                    Comment (u'\n'),
                    Comment (u'\n'),
                    ATComment (u" Comments in the middle won't be kept"),
                    Comment (u'\n'),
                    ATComment (u' (parenthesis are also allowed)')]
        
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

    def testExtendedKey (self):
        """ Allow symbols in keys """
        
        self._check ('ext-key')
        return

    def testOther (self):
        """ Allow symbols in keys """
        
        self._check ('other')
        return

    def testMissingComma (self):
        """ Allow missing comma between fields """
        
        self._check ('missing-comma')
        return

    def testSpaceInAuthors (self):
        """ No extra spaces around authors """
        
        self._check ('authors')
        return

    def testInitialsPlusName (self):
        """ Parse names like F. Gobry """
        
        self._check ('initials')
        return

    def testCRInName (self):
        """ A carriage return in a name """
        
        self._check ('carriage')
        return

    def testVariants (self):
        """ Multiple variants in names """
        
        self._check ('variants')
        return

    def testLaTeXAccent (self):
        """ Decode LaTeX-accented strings like \'e """
        
        self._check ('accents')
        return

    def testVon (self):
        """ Split authors with a Von in the name """
        
        self._check ('von')
        return

    def testStringJoin (self):

        self._check ('environ')
        
    def testCharMacro (self):
        """ Test the handling of the char macro, especially for { and } """
        self._check ('charmacro')
        

class TestBibTeXExport (pybut.TestCase):

    def _check (self, base):

        f = pybut.dbname ()

        db = Store.get ('file').dbopen ('ut_bibtex/%s.xml' % base)
        fd = open (f, 'w')
        
        self.writer = WithCaseHandler ()
        
        self.writer.write (fd, db.entries, db)

        fd.close ()
        
        pybut.fileeq (f, 'ut_bibtex/%s.bib' % base)
        return

    def testEmpty (self):

        self._check ('exp-simple')
        return
    
    def testEmpty (self):

        self._check ('exp-nested')
        return
    
        
suite = pybut.suite (TestBibTeXReader, TestBibTeXImport, TestBibTeXExport)

if __name__ == '__main__':  pybut.run (suite)