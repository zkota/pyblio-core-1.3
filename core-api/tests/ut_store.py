import os, pybut, sys

from Pyblio import Store, Schema, Attribute

class TestStore (pybut.TestCase):

    """ Perform tests on the Pyblio.Store module """

    _i = 0

    def setUp (self):

        self.f = ',,t%d.xml' % self._i
        TestStore._i = self._i + 1

        return

    def tearDown (self):
        
        if os.path.exists (self.f):
            db = Store.get ('file').dbdestroy (self.f, nobackup = True)

        return
    

    def testEmpty (self):
        """ Create an empty database with a schema """

        schema = Schema.Schema ('ut_store/s:simple.xml')

        db = Store.get ('file').dbcreate (self.f, schema)
        db.save ()
        
        assert len (db.entries) == 0

        pybut.fileeq (self.f, 'ut_store/empty.xml')
        return

    def testReadEmpty (self):
        """ A schema in a database is equivalent to outside the database """
        
        db = Store.get ('file').dbopen ('ut_store/empty.xml')

        file = open (self.f, 'w')
        db.schema.xmlwrite (file)
        file.close ()

        pybut.fileeq (self.f, 'ut_store/s:simple.xml')
        
        return

    def testWrite (self):
        """ A new database can be saved with its schema """

        schema = Schema.Schema ('ut_store/s:full.xml')
        db = Store.get ('file').dbcreate (self.f, schema)

        e = Store.Entry ()

        e ['author'] = [ Attribute.Person (last = 'Last 1'),
                         Attribute.Person (last = 'Last 2')]
        e ['url']    = [ Attribute.URL ('http://pybliographer.org') ]
        e ['text']   = [ Attribute.Text (u'sample text') ]
        e ['date']   = [ Attribute.Date (year = 2003) ]
        
        db.add (e)

        db.header = u"Hi, I'm a database description"

        db.save ()

        pybut.fileeq (self.f, 'ut_store/simple.xml')
        return


    def testRead (self):
        """ A database can be read and saved again identically """
        
        db = Store.get ('file').dbopen ('ut_store/simple.xml')

        fd = open (self.f, 'w')
        db.xmlwrite (fd)
        fd.close ()

        pybut.fileeq (self.f, 'ut_store/simple.xml')
        return

    def testNativeWrite (self):

        """ Native data is stored in the database, along with loss information """

        schema = Schema.Schema ('ut_store/s:full.xml')
        db = Store.get ('file').dbcreate (self.f, schema)

        e = Store.Entry ()

        e ['author'] = [ Attribute.Person (last = 'LastName') ]
        e.loss_set ('author', True)
        
        e.native = ('bibtex', '@article{entry_1,\nauthor = {LastName}}')

        db.add (e)
        db.save ()
        
        pybut.fileeq (self.f, 'ut_store/native.xml')
        return
        
    def testTxoRead (self):
        """ A database with taxonomy fields can be read and saved again identically """
        
        db = Store.get ('file').dbopen ('ut_store/taxonomy.xml')

        fd = open (self.f, 'w')
        db.xmlwrite (fd)
        fd.close ()

        pybut.fileeq (self.f, 'ut_store/taxonomy.xml')
        return

    def testNativeRead (self):

        """ Native data is also read back from file """
        
        db = Store.get ('file').dbopen ('ut_store/native.xml')

        e = db [1]
        
        assert e.native == ('bibtex',
                            '@article{entry_1,\nauthor = {LastName}}')

        assert e.has_loss ('author')
        return


    def testValidate (self):

        from Pyblio.Exceptions import SchemaError
        
        schema = Schema.Schema ('ut_store/s:validate.xml')
        db = Store.get ('file').dbcreate (self.f, schema)

        def fail (e):
            try:
                db.validate (e)
                assert False, 'should not be accepted'
            
            except SchemaError:
                pass

            return
        
        # Discard empty attributes
        e = Store.Entry ()
        e ['title'] = []

        e = db.validate (e)
        assert not e.has_key ('title')

        # Discard unknown attributes
        e = Store.Entry ()
        e ['bozo'] = [ Attribute.Text ('yay') ]

        fail (e)

        # Check for entry types
        e = Store.Entry ()
        e ['text'] = [ Attribute.Text ('yay'),
                       Attribute.Text ('yay'),
                       Attribute.URL ('hoho'),
                       Attribute.Text ('yay'),
                       ]

        fail (e)

        # check for entry count
        e = Store.Entry ()
        p = Attribute.Person (last = 'gobry')
        
        e ['author'] = [ p, p, p, p, p ]
        fail (e)

        e = Store.Entry ()
        u = Attribute.URL ('abc')
        e ['author'] = [ u, u ]
        fail (e)

        # Check that unknown enumerates are rejected
        e = Store.Entry ()

        enu = Store.TxoItem ()

        enu.id    = 1
        enu.group = 'b'

        e ['enum'] = [ Attribute.Txo (enu) ]
        fail (e)
        
        enu.id    = 1
        enu.group = 'a'

        e ['enum'] = [ Attribute.Txo (enu) ]
        fail (e)

        # check that unexpected enums are rejected
        g = db.enum.add ('c')

        i = Store.TxoItem ()
        i.names [''] = 'youou'
        i = g.add (i)
        
        enu = db.enum ['c'][i]

        e ['enum'] = [ Attribute.Txo (enu) ]
        fail (e)
        return
    
        
suite = pybut.suite (TestStore)
if __name__ == '__main__':  pybut.run (suite)
