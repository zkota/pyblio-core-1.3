import os, pybut, sys

from Pyblio import Core, Schema, Attribute

class TestCore (pybut.TestCase):

    """ Perform tests on the Pyblio.Core module """

    def testEmpty (self):
        """ Create an empty database with a schema """
        
        schema = Schema.open ('ut_core/s:simple.xml')
        db = Core.Database (schema)

        assert len (db) == 0

        file = open (',,t1.xml', 'w')
        db.xmlwrite (file)
        file.close ()

        pybut.fileeq (',,t1.xml', 'ut_core/empty.xml')

        os.unlink (',,t1.xml')
        return

    def testReadEmpty (self):
        """ A schema in a database is equivalent to outside the database """
        
        db = Core.open ('ut_core/empty.xml')

        file = open (',,t2.xml', 'w')
        db.schema.xmlwrite (file)
        file.close ()

        pybut.fileeq (',,t2.xml', 'ut_core/s:simple.xml')
        
        os.unlink (',,t2.xml')
        return

    def testWrite (self):

        schema = Schema.open ('ut_core/s:full.xml')
        db = Core.Database (schema)

        e = Core.Entry (Core.Key ('entry 1'),
                        schema.documents ['sample'])

        e ['author'] = [ Attribute.Person (last = 'Last 1'),
                         Attribute.Person (last = 'Last 2')]
        e ['url']    = [ Attribute.URL ('http://pybliographer.org') ]
        e ['text']   = [ Attribute.Text (u'sample text') ]
        e ['date']   = [ Attribute.Date (year = 2003) ]
        e ['ref']    = [ Attribute.Reference (Core.Key ('ref')) ]
        
        db [e.key] = e

        fd = open (',,t3.xml', 'w')
        db.xmlwrite (fd)
        fd.close ()

        pybut.fileeq (',,t3.xml', 'ut_core/simple.xml')
        return
    
        
pybut.run (pybut.makeSuite (TestCore, 'test'))
