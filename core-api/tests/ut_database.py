import os, pybut, sys, string

from Pyblio import Store, Schema, Attribute

class TestDatabase (pybut.TestCase):

    """ Perform tests on the Pyblio.Stores main functions """

    def setUp (self):
        self.fmt = fmt
        self.hd  = Store.get (self.fmt)
        return
    
    def testCreate (self):
        ''' Try to create a database, and check its content '''
        
        sc = Schema.Schema ('ut_database/schema.xml')
        db = self.hd.dbcreate (',,db', sc)

        e = Store.Entry ()

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

    """ Perform data manipulation tests """

    count = 0

    def setUp (self):
        self.fmt  = fmt
        self.hd   = Store.get (self.fmt)
        self.name = ',,db-%d' % self.count
        
        TestContent.count = self.count + 1

        sc = Schema.Schema ('ut_database/schema.xml')
        self.db = self.hd.dbcreate (self.name, sc)

        return

    def tearDown (self):

        self.hd.dbdestroy (self.name, nobackup = True)
        return

    def testInsertRemove (self):
        """ Check the db behavior upon insertion/suppression """

        import copy
        
        e = Store.Entry ()

        content = {}

        def checkpoint ():

            def subcheck ():
                seen = []
                for k, v in self.db.iteritems ():
                    seen.append (k)
                    assert v == content [k]

                keys = content.keys ()
            
                keys.sort ()
                seen.sort ()

                assert keys == seen
                return

            subcheck ()
            
            self.db.save ()
            self.db = self.hd.dbopen (self.name)

            subcheck ()
            return
        
        for i in xrange (0, 10):
            k = self.db.add (e)
            
            v = copy.deepcopy (e)
            content [k] = v

        checkpoint ()

        # Remove some entries
        
        for k in [2, 4, 6, 8]:
            del self.db [k]
            del content [k]

        checkpoint ()

        # Modify one entry
        e ['title'] = [ Attribute.Text ('A title') ]
        self.db [1] = e

        content [1] = copy.deepcopy (e)

        assert content [1] != content [3]
        
        checkpoint ()
        return


    def testIndexUpdate (self):
        """ Check for index coherency upon modifications """

        e = Store.Entry ()

        e ['title'] = [ Attribute.Text ('a') ]
        a = self.db.add (e)

        e ['title'] = [ Attribute.Text ('b') ]
        b = self.db.add (e)

        def check (res):

            for w, r in zip (('a', 'b', 'c'), res):

                rs = map (None, self.db.query (w))
                assert rs == r, \
                       'for %s: expected %s, got %s' % (w, r, rs)
            return

        # check initial state
        check (([a], [b], []))

        # modify an entry
        e ['title'] = [ Attribute.Text ('c') ]
        self.db [b] = e

        check (([a], [], [b]))

        # remove an entry
        del self.db [a]
        check (([], [], [b]))
        
        return

    
        
    def testIterate (self):
        """ Loop over the db content """
        
        e = Store.Entry ()

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
    

    def testFullTextQuery (self):
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

            e = Store.Entry ()

            a, b, c = phrase (), phrase (), phrase ()
            
            e ['title'] = [ Attribute.Text (a), Attribute.Text (b) ]
            e ['url']   = [ Attribute.URL (c) ]

            k = self.db.add (e)

            for w in a.split () + b.split () + c.split ():
                if k not in entries [w]:
                    entries [w].append (k)
            

        # Search the occurences of every word
        for w in words:
            rs = self.db.query (w)

            vals = []
            for v in rs:
                vals.append (v)

            real = [] + entries [w]

            vals.sort ()
            real.sort ()

            assert vals == real, "%s != %s" % (vals, real)
        return


    def testEnumAdd (self):

        """ Check for enum addition in the database """
        
        # add some enums to the database
        i = Store.EnumItem ()

        a  = []
        va = ['A / 1', 'A / 2']

        g = self.db.enum.add ('a')
        
        for k in va:
            i.names [''] = k
            g.add (i)
            
        b = []
        vb = ['B / 1', 'B / 2']
        
        g = self.db.enum.add ('b')
        for k in vb:
            i.names [''] = k
            g.add (i)

        na = []
        for v in self.db.enum ['a'].values ():
            na.append (v.names [''])

        assert na == va
        return

    def testEnumInDB (self):

        """ Use Enums in database entries """
        
        # add some enums to the database
        i = Store.EnumItem ()

        a  = []
        va = ['A / 1', 'A / 2']

        g = self.db.enum.add ('a')
        for k in va:
            i.names [''] = k

            v = g.add (i)
            a.append (self.db.enum ['a'][v])
        

        e = Store.Entry ()
        e ['enum-a'] = [ Attribute.Enumerated (a [0]) ]
        
        self.db.add (e)

        f = ',,enumdb-' + fmt

        fd = open (f, 'w')
        self.db.xmlwrite (fd)
        fd.close ()
        
        pybut.fileeq (f, 'ut_database/enumerate.xml')
        os.unlink (f)
        return


    def testNamedResultSet (self):

        e = Store.Entry ()

        e ['title'] = [Attribute.Text ('a sample')]
        for i in range (5):
            self.db.add (e)
        
        e ['title'] = [Attribute.Text ('youyou')]
        for i in range (5):
            self.db.add (e)

        rs = self.db.query ('youyou', name = u'my set')

        def integrity (rs):
            i = 0
            for k in rs:
                assert self.db [k] ['title'] [0] == 'youyou'
                i = i + 1

            assert i == 5, 'obtained %d' % i
            return

        integrity (rs)
        integrity (self.db.rs [u'my set'])
        
        self.db.save ()
        self.db = self.hd.dbopen (self.name)

        integrity (self.db.rs [u'my set'])

        # Once removed, the rs should not exist anymore
        del self.db.rs [u'my set']

        try:
            r = self.db.rs [u'my set']
            assert False, 'the result set should not exist anymore'

        except KeyError: pass

        self.db.save ()
        self.db = self.hd.dbopen (self.name)

        try:
            r = self.db.rs [u'my set']
            assert False, 'the result set should not exist anymore'

        except KeyError: pass
        return


    def testResultSetAddRemove (self):

        """ Create a RS, add items in it and remove them """
        e = Store.Entry ()
        items = []
        
        e ['title'] = [Attribute.Text ('a sample')]

        for i in range (5):
            items.append (self.db.add (e))

        items.sort ()

        for name in (None, u'named'):
            
            rs = self.db.rs.add (name)

            # put all the entries
            for i in items:
                rs.add (i)

            got = []
            for v in rs:
                got.append (v)

            got.sort ()
            assert got == items, 'expected %s, got %s' % (
                items, got)

            # remove some items
            del rs [items [0]]
            del rs [items [-1]]
            del rs [items [2]]

            check = [] + items
            del check [2]
            del check [0]
            del check [-1]

            got = []
            for v in rs:
                got.append (v)

            got.sort ()
            assert got == check, 'expected %s, got %s' % (
                check, got)
            
        return


    def testResultSetDuplicates (self):

        """ There are no duplicates in a result set """

        e = Store.Entry ()
        items = []
        
        e ['title'] = [Attribute.Text ('a sample')]

        for i in range (5):
            items.append (self.db.add (e))

        rs = self.db.rs.add ()

        # put all the entries twice
        for i in items + items:
            rs.add (i)

        got = []
        for v in rs:
            got.append (v)

        got.sort ()
        assert got == items, 'expected %s, got %s' % (
            items, got)
        
        return

    def testResultSetUpdate (self):

        """ If an item is removed from the database, it is removed
        from the result sets too.  """

        rs = self.db.rs.add ()

        e = Store.Entry ()
        items = []
        
        for i in range (5):
            items.append (self.db.add (e))
        
        for i in items: rs.add (i)

        # remove one item in the db
        del self.db [items [0]]

        got = map (None, rs)
        got.sort ()
        
        assert got == items [1:], \
               "expected %s, got %s" % (items [1:], got)

        return

    def testEnumDel (self):

        """ Forbid the removal of an Enum definition that is in use """

        from Pyblio import Exceptions
        
        # Create two enums, one that will be used, the other not. Try
        # to remove both.
        i = Store.EnumItem ()

        a  = []
        va = ['A / 1', 'A / 2']

        g = self.db.enum.add ('a')
        for k in va:
            i.names [''] = k
            v = g.add (i)

            a.append (self.db.enum ['a'][v])
            
        e = Store.Entry ()
        
        e ['enum-a'] = [Attribute.Enumerated (a [1])]
        self.db.add (e)

        del self.db.enum ['a'][a [0].id]

        try:
            del self.db.enum ['a'][a [1].id]
            assert False, 'should not be possible'
            
        except Exceptions.ConstraintError:
            pass

        return


    def testEnumSingle (self):

        from Pyblio import Exceptions
        
        g = self.db.enum.add ('a')

        try:
            g = self.db.enum.add ('a')
            assert False, 'should not succeed'
            
        except Exceptions.ConstraintError:
            pass

        return
    
    
fmts = ('file', 'bsddb')

global fmt

for fmt in fmts:
    print "unittest: ------------ storage '%s' ----------" % fmt
    pybut.run (pybut.TestSuite ((pybut.makeSuite (TestDatabase, 'test'),
                                 pybut.makeSuite (TestContent,  'test'))))
