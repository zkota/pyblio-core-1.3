import os, pybut, sys

from Pyblio import Store, Schema, Attribute

class TestStore (pybut.TestCase):

    """ Perform tests on the Pyblio.Store module """

    def testEmpty (self):
        """ Create an empty database with a schema """

        f = ',,t1.xml'
        
        schema = Schema.Schema ('ut_store/s:simple.xml')

        db = Store.get ('file').dbcreate (f, schema)
        db.save ()
        
        assert len (db) == 0

        pybut.fileeq (f, 'ut_store/empty.xml')
        os.unlink (f)
        return

    def testReadEmpty (self):
        """ A schema in a database is equivalent to outside the database """
        
        db = Store.get ('file').dbopen ('ut_store/empty.xml')

        file = open (',,t2.xml', 'w')
        db.schema.xmlwrite (file)
        file.close ()

        pybut.fileeq (',,t2.xml', 'ut_store/s:simple.xml')
        
        os.unlink (',,t2.xml')
        return

    def testWrite (self):
        """ A new database can be saved with its schema """

        f = ',,t3.xml'
        
        schema = Schema.Schema ('ut_store/s:full.xml')
        db = Store.get ('file').dbcreate (f, schema)

        e = Store.Entry ()

        e ['author'] = [ Attribute.Person (last = 'Last 1'),
                         Attribute.Person (last = 'Last 2')]
        e ['url']    = [ Attribute.URL ('http://pybliographer.org') ]
        e ['text']   = [ Attribute.Text (u'sample text') ]
        e ['date']   = [ Attribute.Date (year = 2003) ]
        e ['ref']    = [ Attribute.Reference (Store.Key (1)) ]
        
        db.add (e)

        db.header = u"Hi, I'm a database description"

        db.save ()

        pybut.fileeq (f, 'ut_store/simple.xml')
        os.unlink (f)
        return


    def testRead (self):
        """ A database can be read and saved again identically """
        
        db = Store.get ('file').dbopen ('ut_store/simple.xml')

        fd = open (',,t4.xml', 'w')
        db.xmlwrite (fd)
        fd.close ()

        pybut.fileeq (',,t4.xml', 'ut_store/simple.xml')

        os.unlink (',,t4.xml')
        return

    def testEnumRead (self):
        """ A database with enumerated fields can be read and saved again identically """
        
        db = Store.get ('file').dbopen ('ut_store/enumerated.xml')

        fd = open (',,t6.xml', 'w')
        db.xmlwrite (fd)
        fd.close ()

        pybut.fileeq (',,t6.xml', 'ut_store/enumerated.xml')

        os.unlink (',,t6.xml')
        return


    def testNativeWrite (self):

        """ Native data is stored in the database, along with loss information """
        
        schema = Schema.Schema ('ut_store/s:full.xml')
        db = Store.get ('file').dbcreate (',,t5.xml', schema)

        e = Store.Entry ()

        e ['author'] = [ Attribute.Person (last = 'LastName') ]
        e.loss_set ('author', True)
        
        e.native = ('bibtex', '@article{entry_1,\nauthor = {LastName}}')

        db.add (e)
        db.save ()
        
        pybut.fileeq (',,t5.xml', 'ut_store/native.xml')

        os.unlink (',,t5.xml')
        return
        
    def testNativeRead (self):

        """ Native data is also read back from file """
        
        db = Store.get ('file').dbopen ('ut_store/native.xml')

        e = db [1]
        
        assert e.native == ('bibtex',
                            '@article{entry_1,\nauthor = {LastName}}')

        assert e.has_loss ('author')
        return
    
pybut.run (pybut.makeSuite (TestStore, 'test'))
