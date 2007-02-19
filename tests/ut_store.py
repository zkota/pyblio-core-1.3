# -*- encoding: utf-8 -*-

import os, pybut, sys

from Pyblio import Store, Schema, Attribute, Exceptions

class TestStore (pybut.TestCase):

    """ Perform tests on the Pyblio.Store module """

    _i = 0

    def setUp (self):

        self.f = ',,t%d.xml' % self._i
        TestStore._i = self._i + 1

        return


    def testEmpty (self):
        """ Create an empty database with a schema """

        schema = Schema.Schema (pybut.src(os.path.join ('ut_store', 's_simple.xml')))

        db = Store.get ('file').dbcreate (self.f, schema)
        db.save ()
        
        assert len (db.entries) == 0

        pybut.fileeq (self.f, pybut.src('ut_store/empty.xml'))
        return

    def testReadEmpty (self):
        """ A schema in a database is equivalent to outside the database """
        
        db = Store.get ('file').dbopen (pybut.src('ut_store/empty.xml'))

        file = open (self.f, 'w')
        db.schema.xmlwrite (file)
        file.close ()

        pybut.fileeq (self.f, pybut.src(os.path.join ('ut_store', 's_simple.xml')))
        
        return

    def testWrite (self):
        """ A new database can be saved with its schema """

        schema = Schema.Schema (pybut.src(os.path.join ('ut_store', 's_full.xml')))
        db = Store.get ('file').dbcreate (self.f, schema)
        
        e = Store.Record ()

        scn = Attribute.Person (last = 'Last 2')
        scn.q ['role'] = [ Attribute.Text ('Editor') ]
        
        e ['author'] = [ Attribute.Person (last = u'Last 1é'), scn ]

        url1 = Attribute.URL ('http://pybliographer.org')
        url1.q ['desc'] = [ Attribute.Text ('Main site') ]
        url1.q ['lang'] = [ Attribute.Txo (db.schema.txo ['language'].byname ('EN')) ]

        url2 = Attribute.URL ('http://pybliographer.org')
        url2.q ['desc'] = [ Attribute.Text ('Main site') ]
        url2.q ['lang'] = [ Attribute.Txo (db.schema.txo ['language'].byname ('FR')) ]
        e ['url']    = [ url1, url2 ]

        e ['text']   = [ Attribute.Text (u'sample text é') ]

        rich = Attribute.Text (u'sample text é')
        rich.q ['comment'] = [ Attribute.Text ('bullshit') ]
        
        e ['rich']   = [ rich ]
        e ['date']   = [ Attribute.Date (year = 2003) ]
        e ['id']     = [ Attribute.ID ('Hehe') ]
        
        db.add (e)

        db.header = u"Hi, I'm a database description"

        rs = db.rs.new()
        rs.name = "sample"

        rs.add (1)
        db.rs.update(rs)

        db.save ()

        pybut.fileeq (self.f, pybut.src('ut_store/simple.xml'))
        return


    def testRead (self):
        """ A database can be read and saved again identically """

        db = Store.get ('file').dbopen (pybut.src('ut_store/simple.xml'))

        fd = open (self.f, 'w')
        db.xmlwrite (fd)
        fd.close ()

        pybut.fileeq (self.f, pybut.src('ut_store/simple.xml'))
        return

    def testQualifiedRead (self):
        """ Qualified fields can be read and saved again identically """
        
        db = Store.get ('file').dbopen (pybut.src('ut_store/qualified.xml'))

        fd = open (self.f, 'w')
        db.xmlwrite (fd)
        fd.close ()

        pybut.fileeq (self.f, pybut.src('ut_store/qualified.xml'))
        return

    def testTxoFromSchema (self):
        """ Taxonomy fields can be read and saved """

        tmp = pybut.dbname()
        s = Schema.Schema(pybut.src('ut_store/taxoschema.xml'))
        db = Store.get('file').dbcreate(tmp,s)

        fd = open (self.f, 'w')
        db.xmlwrite (fd)
        fd.close ()

        pybut.fileeq (self.f, pybut.src('ut_store/taxoschemadb.xml'))
        return

    def testValidate (self):

        from Pyblio.Exceptions import SchemaError
        
        schema = Schema.Schema (pybut.src(os.path.join ('ut_store', 's_validate.xml')))
        db = Store.get ('file').dbcreate (self.f, schema)

        def fail(e):
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

        enu = Schema.TxoItem ()

        enu.id    = 1
        enu.group = 'b'

        e ['enum'] = [ Attribute.Txo (enu) ]
        fail (e)
        
        enu.id    = 1
        enu.group = 'a'

        e ['enum'] = [ Attribute.Txo (enu) ]
        fail (e)


    def testValidateTxoCleanup (self):

        db = Store.get ('file').dbopen (pybut.src('ut_store/nasty-txo.xml'))

        # check that unnecessary txo items are removed
        g = db.schema.txo ['a']

        e = Store.Record ()
        
        e ['txo'] = [ Attribute.Txo (g [1]),
                      Attribute.Txo (g [2]),
                      Attribute.Txo (g [3]),
                      Attribute.Txo (g [4]) ]

        e = db.validate (e)
        
        assert e ['txo'] == [ Attribute.Txo (g [2]),
                              Attribute.Txo (g [4]),], \
                              'got %s' % `e ['txo']`
        return

    def testResultSet (self):

        db = Store.get('file').dbopen(pybut.src('ut_store/resultset.xml'))

        ks = db.rs[1]
        assert ks.name == 'gronf'

        ks = list(ks.iterkeys())
        ks.sort()

        assert ks == [1,2], 'got %s' % repr (ks)


    def testAddSimple (self):
        db = Store.get ('file').dbopen (pybut.src('ut_store/addsimple.xml'))

        rec = Store.Record ()
        
        rec.add ('id', 'myid is here', Attribute.ID)
        rec.add ('text', 'some stupid comment', Attribute.Text)
        rec.add ('url', 'www.mehfleysch.ch', Attribute.URL)
        rec.add ('date', {'year':2005, 'month':9}, Attribute.Date)
        rec.add ('author', {'last':'Karlen', 'first':'Michael'}, Attribute.Person) 
        
        db.add (rec)

        sol = Store.Record ()
        sol ['id']  = [ Attribute.ID ('myid is here') ]
        sol ['text'] = [ Attribute.Text ('some stupid comment') ]
        sol ['url'] = [ Attribute.URL ('www.mehfleysch.ch') ]
        sol ['date'] = [ Attribute.Date (2005, 9) ]
        sol ['author'] = [ Attribute.Person (None, 'Michael', 'Karlen') ]

        assert sol.deep_equal (rec), "\n%s\n not equal to \n%s\n (Think of non-displayed" \
               " qualifiers, if you can't see any difference.)" % (sol, rec)


    def testAddTextQualifiersBizarrOrder (self):
        db = Store.get ('file').dbopen (pybut.src('ut_store/addsimple.xml'))
        rec = Store.Record ()
        
        rec.add ('text.qtext', 'some stuff', Attribute.Text)
        rec.add ('text', 'some stupid comment', Attribute.Text)
        rec.add ('text.qtext', 'even more stuff', Attribute.Text)
        rec.add ('text', 'another comment', Attribute.Text)
        rec.add ('text.qtext', 'stuff for another comment', Attribute.Text)
        
        db.add (rec)

        sol = Store.Record ()

        at = Attribute.Text ('some stupid comment')
        at.q = { 'qtext': [
            Attribute.Text ('some stuff'),
            Attribute.Text ('even more stuff')] }

        at2 = Attribute.Text ('another comment')
        at2.q = {'qtext': [ Attribute.Text ('stuff for another comment')]}
        sol ['text'] = [ at, at2 ]

        assert sol.deep_equal (rec), "\n%s\n not equal to \n%s\n (Think of non-displayed" \
               " qualifiers, if you can't see any difference.)" % (sol, rec)


    def testAddAuthorQualifiers (self):
        db = Store.get ('file').dbopen (pybut.src('ut_store/addsimple.xml'))
        rec = Store.Record ()

        rec.add ('author', {'last':'Karlen', 'first':'Michael'}, Attribute.Person)                
        rec.add ('author.qtext', 'some stuff', Attribute.Text)
        rec.add ('author.qperson', {'last':'Karlen', 'first':'Mum'}, Attribute.Person)                        
        
        db.add (rec)

        sol = Store.Record ()

        at =  Attribute.Person (None, 'Michael', 'Karlen') 

        at.q = {
            'qtext': [ Attribute.Text ('some stuff')],
            'qperson': [ Attribute.Person (None, 'Mum', 'Karlen') ],
            }        
        
        sol ['author'] = [ at ]

        assert sol.deep_equal (rec), "\n%s\n not equal to \n%s\n (Think of non-displayed" \
               " qualifiers, if you can't see any difference.)" % (sol, rec)


    def testAddQualifiersFirst (self):
        db = Store.get ('file').dbopen (pybut.src('ut_store/addsimple.xml'))
        rec = Store.Record ()
        
        rec.add ('text.qtext', 'some stuff', Attribute.Text)
        rec.add ('text.qtext', 'even more stuff', Attribute.Text)
        rec.add ('text', 'some stupid comment', Attribute.Text)
        
        db.add (rec)

        sol = Store.Record ()

        at = Attribute.Text ('some stupid comment')
        at.q = { 'qtext': [
            Attribute.Text ('some stuff'),
            Attribute.Text ('even more stuff')] }
        sol ['text'] = [ at ]

        assert sol.deep_equal (rec), "\n%s\n not equal to \n%s\n (Think of non-displayed" \
               " qualifiers, if you can't see any difference.)" % (sol, rec)


    def testAddOnlyQualifiers (self):
        db = Store.get ('file').dbopen (pybut.src('ut_store/addsimple.xml'))
        rec = Store.Record ()

        rec.add ('text.qtext', 'some stuff', Attribute.Text)
        rec.add ('text.qtext', 'even more stuff', Attribute.Text)

        try:
            db.add (rec)
        except Exceptions.SchemaError:
            pass
        else:
            assert 0, 'db.add should not be allowed as there is ' \
                   'Attribute.UnknownContent in rec'
                    
        sol = Store.Record ()

        at = Attribute.UnknownContent ()
        at.q = { 'qtext': [
            Attribute.Text ('some stuff'),
            Attribute.Text ('even more stuff')] }
        sol ['text'] = [ at ]

        assert sol.deep_equal (rec), "\n%s\n not equal to \n%s\n (Think of non-displayed" \
               " qualifiers, if you can't see any difference.)" % (sol, rec)


suite = pybut.suite (TestStore)
if __name__ == '__main__':  pybut.run (suite)
 
