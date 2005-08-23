# -*- encoding: utf-8 -*-

import os, pybut, sys

from Pyblio import Store, Schema, Attribute

class TestStore (pybut.TestCase):

    """ Perform tests on the Pyblio.Store module """

    _i = 0

    def setUp (self):

        self.f = ',,t%d.xml' % self._i
        TestStore._i = self._i + 1

        return


    def testEmpty (self):
        """ Create an empty database with a schema """

        schema = Schema.Schema (os.path.join ('ut_store', 's_simple.xml'))

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

        pybut.fileeq (self.f, os.path.join ('ut_store', 's_simple.xml'))
        
        return

    def testWrite (self):
        """ A new database can be saved with its schema """

        schema = Schema.Schema (os.path.join ('ut_store', 's_full.xml'))
        db = Store.get ('file').dbcreate (self.f, schema)

        e = Store.Record ()

        scn = Attribute.Person (last = 'Last 2')
        scn.q ['role'] = [ Attribute.Text ('Editor') ]
        
        e ['author'] = [ Attribute.Person (last = u'Last 1é'), scn ]

        url = Attribute.URL ('http://pybliographer.org')
        url.q ['desc'] = [ Attribute.Text ('Main site') ]
        
        e ['url']    = [ url ]

        e ['text']   = [ Attribute.Text (u'sample text é') ]

        rich = Attribute.Text (u'sample text é')
        rich.q ['comment'] = [ Attribute.Text ('bullshit') ]
        
        e ['rich']   = [ rich ]
        e ['date']   = [ Attribute.Date (year = 2003) ]
        e ['id']     = [ Attribute.ID ('Hehe') ]
        
        db.add (e)

        db.header = u"Hi, I'm a database description"

        rs = db.rs.add (permanent = True)
        rs.name = "sample"

        rs.add (1)
        
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

    def testTxoRead (self):
        """ A database with taxonomy fields can be read and saved again identically """
        
        db = Store.get ('file').dbopen ('ut_store/taxonomy.xml')

        fd = open (self.f, 'w')
        db.xmlwrite (fd)
        fd.close ()

        pybut.fileeq (self.f, 'ut_store/taxonomy.xml')
        return

    def testValidate (self):

        from Pyblio.Exceptions import SchemaError
        
        schema = Schema.Schema (os.path.join ('ut_store', 's_validate.xml'))
        db = Store.get ('file').dbcreate (self.f, schema)

        def fail (e):
            try:
                db.validate (e)
                assert False, 'should not be accepted'
            
            except SchemaError:
                pass

            return
        
        # Discard empty attributes
        e = Store.Record ()
        e ['title'] = []

        e = db.validate (e)
        assert not e.has_key ('title')

        # Discard unknown attributes
        e = Store.Record ()
        e ['bozo'] = [ Attribute.Text ('yay') ]

        fail (e)

        # Discard unknown qualifiers
        e = Store.Record ()

        txt = Attribute.Text ('yay')
        txt.q ['bozo'] = [ Attribute.Text ('gronf') ]
        
        e ['title'] = [ txt ]

        fail (e)

        # Discard ill-typed qualifiers
        e = Store.Record ()

        url = Attribute.URL ('yay')
        url.q ['info'] = [ Attribute.URL ('gronf') ]
        
        e ['qualified'] = [ url ]

        fail (e)

        # Accept well-typed qualifiers
        e = Store.Record ()

        url = Attribute.URL ('yay')
        url.q ['info'] = [ Attribute.Text ('gronf') ]
        
        e ['qualified'] = [ url ]

        e = db.validate (e)

        # Check for entry types
        e = Store.Record ()
        e ['text'] = [ Attribute.Text ('yay'),
                       Attribute.Text ('yay'),
                       Attribute.URL ('hoho'),
                       Attribute.Text ('yay'),
                       ]

        fail (e)

        # check for entry count
        e = Store.Record ()
        p = Attribute.Person (last = 'gobry')
        
        e ['author'] = [ p, p, p, p, p ]
        fail (e)

        e = Store.Record ()
        u = Attribute.URL ('abc')
        e ['author'] = [ u, u ]
        fail (e)

        # Check that unknown enumerates are rejected
        e = Store.Record ()

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
        g = db.txo ['c']

        i = Store.TxoItem ()
        i.names [''] = 'youou'
        i = g.add (i)
        
        enu = g [i]

        e ['enum'] = [ Attribute.Txo (enu) ]
        fail (e)

    def testValidateTxoCleanup (self):

        db = Store.get ('file').dbopen ('ut_store/nasty-txo.xml')

        # check that unnecessary txo items are removed
        g = db.txo ['a']
        
        e = Store.Record ()
        
        e ['txo'] = [ Attribute.Txo (g [1]),
                      Attribute.Txo (g [2]),
                      Attribute.Txo (g [3]),
                      Attribute.Txo (g [4]) ]

        e = db.validate (e)
        
        assert e ['txo'] == [ Attribute.Txo (g [2]),
                              Attribute.Txo (g [4]),], \
                              'got %s' % `e ['enum']`
        return

    def testResultSet (self):

        db = Store.get ('file').dbopen ('ut_store/resultset.xml')

        ks = db.rs [1]
        assert ks.name == 'gronf'

        ks = ks.keys ()
        ks.sort ()

        assert ks == [1,2], 'got %s' % repr (ks)

        
suite = pybut.suite (TestStore)
if __name__ == '__main__':  pybut.run (suite)
