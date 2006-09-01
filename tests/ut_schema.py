import os, pybut, sys

from Pyblio import Schema, Store


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
    

    def testDuplicate (self):
        """ Forbid field duplication """

        try:
            Schema.Schema ('ut_schema/duplicate.xml')
            assert False
            
        except Schema.SchemaError, msg:
            pass

    def testWrite (self):
        """ Writing does not modify the file """

        for sch in ('simple.xml', 'qualifiers.xml', 'group.xml'):
            file = pybut.dbname ()

            schema = os.path.join ('ut_schema', sch)
            a = Schema.Schema (schema)

            out = open (file, 'w')
            a.xmlwrite (out)
            out.close ()

            # both files should be identical
            pybut.fileeq (schema, file)

            try: os.unlink (file)
            except OSError: pass

    def testGroup (self):
        """ Some fields have Txo groups."""

        import sys
        a = Schema.Schema ('ut_schema/group.xml')

        assert a ['toto'].group == 'toto'

        # Create a database, and check that the Txo has indeed been
        # prefilled.
        file = pybut.dbname()
        
        fmt = Store.get('file')
        db = fmt.dbcreate(file, a)

        keys = db.schema.txo['toto'].keys()
        keys.sort()

        self.failUnlessEqual(keys, [1,2])
        return
    
    def testComplex (self):
        """ Accents and escaping """

        file = pybut.dbname ()
        
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
        assert s ['enum'].type is Attribute.Txo

        return

    
    
suite = pybut.suite (TestSchema)
if __name__ == '__main__':  pybut.run (suite)
