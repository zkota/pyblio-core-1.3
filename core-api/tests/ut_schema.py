import os, pybut

from Pyblio import Schema


class TestSchema (pybut.TestCase):

    """ Perform tests on the Pyblio.Schema module """

    def testEmpty (self):
        """ One can create an empty schema """
        s = Schema.Schema ()
        assert s == {}


    def testEmpty (self):
        """ Open an empty document """
        
        s = Schema.Schema ('ut_schema/empty.xml')
        assert s == {}


    def testSimple (self):
        """ Open a simple document """
        
        s = Schema.Schema ('ut_schema/simple.xml')
        
        assert s.has_key ('author')
        assert s.has_key ('url')

        a = s ['author']
        assert a.names ['en'] == 'Author (en)'
        
        return
    
    def testDefaultName (self):
        """ Check that the default names are used when no locale is specified """

        a = Schema.Schema ('ut_schema/simple.xml') ['author']

        assert a.name == 'Author'
        return
    

    def testL10nName (self):
        """ Check that names are localized """

        from Pyblio import I18n
        
        I18n.lz.lang     = 'en_US'
        I18n.lz.lang_one = 'en'
        
        a = Schema.Schema ('ut_schema/simple.xml') ['author']

        assert a.name == 'Author (en)', a.name
        return
    

    def testSpurrious (self):
        """ Forbid nested documents """

        try:
            Schema.Schema ('ut_schema/spurrious.xml')
            assert False
            
        except Schema.sax.SAXException, msg:
            pass

    def testWrite (self):
        """ Writing does not modify the file """

        file = ',,t1.xml'
        
        import sys
        a = Schema.Schema ('ut_schema/simple.xml')

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
        a = Schema.Schema ('ut_schema/complex.xml')

        out = open (file, 'w')
        a.xmlwrite (out)
        out.close ()
        
        # both files should be identical
        d1 = open (file).read ()
        d2 = open ('ut_schema/complex.xml').read ()

        assert d1 == d2
        
        try: os.unlink (file)
        except OSError: pass

        
    def testTypes (self):
        """ Attribute types """

        from Pyblio import Attribute
        
        s = Schema.Schema ('ut_schema/types.xml')

        assert s ['url'].type is Attribute.URL
        assert s ['text'].type is Attribute.Text
        assert s ['author'].type is Attribute.Person
        assert s ['date'].type is Attribute.Date
        assert s ['id'].type is Attribute.ID
        assert s ['enum'].type is Attribute.Enumerated

        return

    def testIndexed (self):

        s = Schema.Schema ('ut_schema/indexed.xml')

        assert s ['author'].indexed
        assert not s ['url'].indexed
        assert not s ['enum'].indexed

        return
    
    
suite = pybut.suite (TestSchema)
if __name__ == '__main__':  pybut.run (suite)
