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

        self.hd.dbdestroy (',,db', nobackup = True)
        return

    def testDestroy (self):
        ''' Try to destroy a database '''
        
        sc = Schema.Schema ('ut_database/schema.xml')
        db = self.hd.dbcreate (',,db2', sc)

        db.save ()
        del db

        self.hd.dbdestroy (',,db2', nobackup = True)

        try:
            self.hd.dbopen (',,db2')
            assert False
            
        except Store.StoreError:
            pass

        return

    def testRecreate (self):
        ''' Make it impossible to create a db twice '''

        sc = Schema.Schema ('ut_database/schema.xml')

        db = self.hd.dbcreate (',,db3', sc)
        db.save ()

        try:
            db = self.hd.dbcreate (',,db3', sc)
            assert False
            
        except Store.StoreError:
            pass

        self.hd.dbdestroy (',,db3', nobackup = True)
        return

    
class TestContent (pybut.TestCase):

    """ Perform tests on the Pyblio.Stores modules """

    count = 0

    def setUp (self):
        self.fmt = fmt
        self.hd  = Store.get (self.fmt)

        TestContent.count = self.count + 1

        sc = Schema.Schema ('ut_database/schema.xml')
        self.db = self.hd.dbcreate (',,db-%d' % self.count, sc)

        return

    def tearDown (self):

        self.hd.dbdestroy (',,db-%d' % self.count, nobackup = True)
        return

    
    def testIterate (self):

        e = Store.Entry (self.db.schema ['article'])

        initial = ['a', 'b', 'c', 'd']
        
        for k in initial:
            k = Store.Key (k)
            self.db [k] = e

        # Iterate over the keys
        keys = []
        for k in self.db:
            keys.append (k)

        keys.sort ()
        
        assert keys == initial

        keys = []
        for k in self.db.iterkeys ():
            keys.append (k)

        keys.sort ()
        
        assert keys == initial

        # Iterate over the values
        count = 0
        for v in self.db.itervalues ():
            assert v == e
            count = count + 1
        
        assert count == 4

        # Iterate over the values
        keys = []
        for k, v in self.db.iteritems ():
            assert v == e
            keys.append (k)
        
        keys.sort ()
        
        assert keys == initial
        return
    

fmts = ('bsddb', 'file')

global fmt

for fmt in fmts:
    print "unittest: ------------ storage '%s' ----------" % fmt
    pybut.run (pybut.TestSuite ((pybut.makeSuite (TestDatabase, 'test'),
                                 pybut.makeSuite (TestContent,  'test'))))
