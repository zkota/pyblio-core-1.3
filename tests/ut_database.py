import os, pybut, sys

from Pyblio import Store, Schema, Attribute

class TestDatabase (pybut.TestCase):

    """ Perform tests on the Pyblio.Stores modules """

    def setUp (self):
        self.fmt = fmt
        self.hd  = Store.get (self.fmt)
        return
    
    def testCreate (self):
        ''' Try to create a database, and check its content '''
        
        sc = Schema.Schema ('ut_database/schema.xml')
        db = self.hd.dbcreate (',,db', sc)

        k = Store.Key ('a')
        e = Store.Entry (db.schema ['article'])

        e ['title'] = [ Attribute.Text ('title') ]
        db [k] = e
        
        db.save ()

        db = self.hd.dbopen (',,db')
        assert db ['a']['title'] == ['title']

        self.hd.dbdestroy (',,db')
        return

    def testDestroy (self):
        ''' Try to destroy a database '''
        
        sc = Schema.Schema ('ut_database/schema.xml')
        db = self.hd.dbcreate (',,db2', sc)

        db.save ()
        del db

        self.hd.dbdestroy (',,db2')

        try:
            self.hd.dbopen (',,db2')
            assert False
            
        except Store.StoreError:
            pass

        return
    

fmts = ('bsddb', 'file')

global fmt

for fmt in fmts:
    print "unittest: ------------ storage '%s' ----------" % fmt
    pybut.run (pybut.makeSuite (TestDatabase, 'test'))
