import os, pybut, sys, string

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

        e = Store.Entry (db.schema ['article'])

        e ['title'] = [ Attribute.Text ('title') ]
        k = db.add (e)
        
        db.save ()

        db = self.hd.dbopen (',,db')
        assert db [k]['title'] == ['title']

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
        """ Loop over the db content """
        
        e = Store.Entry (self.db.schema ['article'])

        initial = []
        
        for i in range (0, 10):
            initial.append (self.db.add (e))

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
        
        assert count == len (initial)

        # Iterate over the values
        keys = []
        for k, v in self.db.iteritems ():
            assert v == e
            keys.append (k)
        
        keys.sort ()
        
        assert keys == initial
        return
    

    def testFullQuery (self):
        """ Full text ordered queries """

        import random

        # generate 64 base words
        words  = []
        letter = 'abcdefgh'
        
        for a in letter:
            for b in letter:
                words.append (a +b)

        def phrase ():
            random.shuffle (words)
            return string.join (words [:5], ' ')

        # Fill the db with some phrases
        entries = {}
        for w in words:
            entries [w] = []

        for i in range (0, 16):

            e = Store.Entry (self.db.schema ['article'])

            a, b, c = phrase (), phrase (), phrase ()
            
            e ['title'] = [ Attribute.Text (a), Attribute.Text (b) ]
            e ['url']   = [ Attribute.URL (c) ]

            k = self.db.add (e)

            for w in a.split () + b.split () + c.split ():
                if k not in entries [w]:
                    entries [w].append (k)
            

        # Search the occurences of every word
        for w in words:
            rs = self.db.query (w, 'title')

            vals = []
            for v in rs:
                vals.append (v)

            real = [] + entries [w]

            vals.sort ()
            real.sort ()

            assert vals == real, "%s != %s" % (vals, real)
        return
    

fmts = ('bsddb', 'file')

global fmt

for fmt in fmts:
    print "unittest: ------------ storage '%s' ----------" % fmt
    pybut.run (pybut.TestSuite ((pybut.makeSuite (TestDatabase, 'test'),
                                 pybut.makeSuite (TestContent,  'test'))))
