import os, pybut

from Pyblio import Schema

class TestSchema (pybut.TestCase):

    def testEmpty (self):
        """ One can create an empty schema """
        s = Schema.Schema ()
        assert s.documents == {}


    def testEmpty (self):
        """ Open an empty document """
        
        s = Schema.Schema (file = 'ut_schema/empty.xml')
        assert s.documents == {}


    def testSimple (self):
        """ Open a simple document """
        
        s = Schema.Schema (file = 'ut_schema/simple.xml')
        assert s.documents.has_key ('article')

        a = s.documents ['article']
        
        assert a.mandatory.has_key ('author')
        assert a.optional.has_key ('url')

        assert a.names.has_key ('en')
        assert a.mandatory ['author'].names.has_key ('en')

        assert a.names ['en'] == 'Article (en)'
        assert a.mandatory ['author'].names ['en'] == 'Author (en)'
        return
    
    def testDefaultName (self):
        """ Check that the default names are used when no locale is specified """

        a = Schema.Schema (file = 'ut_schema/simple.xml').documents ['article']

        assert a.name == 'Article'
        assert a.mandatory ['author'].name == 'Author'
        return
    

    def testL10nName (self):
        """ Check that names are localized """

        import locale

        locale.setlocale (locale.LC_MESSAGES, 'en_US')
        
        a = Schema.Schema (file = 'ut_schema/simple.xml').documents ['article']

        assert a.name == 'Article (en)'
        assert a.mandatory ['author'].name == 'Author (en)'
        return
    

    def testSpurrious (self):
        """ Forbid nested documents """

        try:
            Schema.Schema (file = 'ut_schema/spurrious.xml')
            assert False
            
        except Schema.sax.SAXException, msg:
            pass

    def testWrite (self):
        """ Writing does not modify the file """

        file = ',,t1.xml'
        
        import sys
        a = Schema.Schema (file = 'ut_schema/simple.xml')

        out = open (file, 'w')
        a.xmlwrite (out)
        out.close ()
        
        # both files should be identical
        d1 = open (file).read ()
        d2 = open ('ut_schema/simple.xml').read ()
        
        assert d1 == d2
        
        try: os.unlink (file)
        except OSError: pass
            
    def testComplex (self):
        """ Accents and escaping """

        file = ',,t2.xml'
        
        import sys
        a = Schema.Schema (file = 'ut_schema/complex.xml')

        out = open (file, 'w')
        a.xmlwrite (out)
        out.close ()
        
        # both files should be identical
        d1 = open (file).read ()
        d2 = open ('ut_schema/complex.xml').read ()

        assert d1 == d2
        
        try: os.unlink (file)
        except OSError: pass

        
pybut.run (pybut.makeSuite (TestSchema, 'test'))
