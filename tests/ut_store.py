import os, pybut, sys

from Pyblio import Store, Schema, Attribute

class TestStore (pybut.TestCase):

    """ Perform tests on the Pyblio.Store module """

    def testEmpty (self):
        """ Create an empty database with a schema """
        
        schema = Schema.open ('ut_store/s:simple.xml')
        db = Store.Database (schema)

        assert len (db) == 0

        file = open (',,t1.xml', 'w')
        db.xmlwrite (file)
        file.close ()

        pybut.fileeq (',,t1.xml', 'ut_store/empty.xml')

        os.unlink (',,t1.xml')
        return

    def testReadEmpty (self):
        """ A schema in a database is equivalent to outside the database """
        
        db = Store.open ('ut_store/empty.xml')

        file = open (',,t2.xml', 'w')
        db.schema.xmlwrite (file)
        file.close ()

        pybut.fileeq (',,t2.xml', 'ut_store/s:simple.xml')
        
        os.unlink (',,t2.xml')
        return

    def testWrite (self):

        schema = Schema.open ('ut_store/s:full.xml')
        db = Store.Database (schema)

        e = Store.Entry (Store.Key ('entry 1'),
                        schema.documents ['sample'])

        e ['author'] = [ Attribute.Person (last = 'Last 1'),
                         Attribute.Person (last = 'Last 2')]
        e ['url']    = [ Attribute.URL ('http://pybliographer.org') ]
        e ['text']   = [ Attribute.Text (u'sample text') ]
        e ['date']   = [ Attribute.Date (year = 2003) ]
        e ['ref']    = [ Attribute.Reference (Store.Key ('ref')) ]
        
        db [e.key] = e

        fd = open (',,t3.xml', 'w')
        db.xmlwrite (fd)
        fd.close ()

        pybut.fileeq (',,t3.xml', 'ut_store/simple.xml')

        os.unlink (',,t3.xml')
        return

    def testRead (self):

        db = Store.open ('ut_store/simple.xml')
        
        fd = open (',,t4.xml', 'w')
        db.xmlwrite (fd)
        fd.close ()

        pybut.fileeq (',,t4.xml', 'ut_store/simple.xml')

        os.unlink (',,t4.xml')
        return

    
pybut.run (pybut.makeSuite (TestStore, 'test'))
