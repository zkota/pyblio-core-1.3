import os, pybut, sys, string

from Pyblio import Store, Schema, Attribute

pybut.cleanup ()

class TestDatabase (pybut.TestCase):

    """ Perform tests on the Pyblio.Stores main functions """

    def setUp (self):
        self.fmt = fmt
        self.hd  = Store.get (self.fmt)

        self.nm = pybut.dbname ()
        return
    
    def testCreate (self):
        ''' Try to create a database, and check its content '''

        sc = Schema.Schema ('ut_database/schema.xml')
        db = self.hd.dbcreate (self.nm, sc)

        e = Store.Entry ()

        e ['title'] = [ Attribute.Text ('title') ]
        k = db.add (e)
        
        db.save ()

        db = self.hd.dbopen (self.nm)
        assert db [k]['title'] == ['title']

        return

    def testDestroy (self):
        ''' Try to destroy a database '''
        
        sc = Schema.Schema ('ut_database/schema.xml')
        db = self.hd.dbcreate (self.nm, sc)

        db.save ()
        del db

        self.hd.dbdestroy (self.nm, nobackup = True)

        try:
            self.hd.dbopen (self.nm)
            assert False
            
        except Store.StoreError:
            pass

        return

    def testRecreate (self):
        ''' Make it impossible to create a db twice '''

        sc = Schema.Schema ('ut_database/schema.xml')

        db = self.hd.dbcreate (self.nm, sc)
        db.save ()

        try:
            db = self.hd.dbcreate (self.nm, sc)
            assert False
            
        except Store.StoreError:
            pass

        self.hd.dbdestroy (self.nm, nobackup = True)
        return

    def testImport (self):
        ''' Import an XML database in the Store '''

        db = self.hd.dbimport (self.nm, 'ut_database/sample.xml')
        db.save ()

        nmo = pybut.dbname ()
        
        fd = open (nmo, 'w')
        db.xmlwrite (fd)
        fd.close ()

        pybut.fileeq (nmo, 'ut_database/sample.xml')
        self.hd.dbdestroy (self.nm, nobackup = True)

        os.unlink (nmo)
        return
    
        
    
class TestContent (pybut.TestCase):

    """ Perform data manipulation tests """

    count = 0

    def setUp (self):
        self.fmt  = fmt
        self.hd   = Store.get (self.fmt)
        self.name = pybut.dbname ()
        
        TestContent.count = self.count + 1

        sc = Schema.Schema ('ut_database/schema.xml')
        self.db = self.hd.dbcreate (self.name, sc)

        return

    def testInsertRemove (self):
        """ Check the db behavior upon insertion/suppression """

        import copy
        
        e = Store.Entry ()

        content = {}

        def checkpoint ():

            def subcheck ():
                seen = []
                for k, v in self.db.entries.iteritems ():
                    seen.append (k)
                    assert v == content [k]

                keys = content.keys ()
            
                keys.sort ()
                seen.sort ()

                assert keys == seen

                assert len (self.db.entries) == len (seen)
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

    def testIterDB (self):
        """ A database provides independent iterators """

        e = Store.Entry ()

        for i in range (3):
            self.db.add (e)

        full = []
        for x in self.db.entries:
            for y in self.db.entries:
                full.append ((x, y))

        assert len (full) == 9
        return
    
    def testIterRS (self):
        """ A database provides independent iterators """

        e  = Store.Entry ()
        rs = self.db.rs.add ()
        
        for i in range (3):
            ix = self.db.add (e)
            rs.add (ix)

        full = []
        for x in rs:
            for y in rs:
                full.append ((x, y))

        assert len (full) == 9
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
        for k in self.db.entries:
            keys.append (k)

        keys.sort ()
        
        assert keys == initial

        keys = []
        for k in self.db.entries.iterkeys ():
            keys.append (k)

        keys.sort ()
        
        assert keys == initial

        # Iterate over the values
        count = 0
        for v in self.db.entries.itervalues ():
            assert v == e
            count = count + 1
        
        assert count == len (initial)

        # Iterate over the values
        keys = []
        for k, v in self.db.entries.iteritems ():
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

        rs = self.db.query ('youyou', permanent = True)
        rs.name = u'my set'
        
        def integrity (rs):
            i = 0
            for k in rs:
                assert self.db [k] ['title'] [0] == 'youyou'
                i = i + 1

            assert i == 5, 'obtained %d' % i
            assert rs.name == u'my set'
            return

        rsid = rs.id
        
        integrity (rs)
        integrity (self.db.rs [rsid])
        
        del rs
        
        self.db.save ()
        self.db = self.hd.dbopen (self.name)

        integrity (self.db.rs [rsid])

        # Once removed, the rs should not exist anymore
        del self.db.rs [rsid]

        try:
            r = self.db.rs [rsid]
            assert False, 'the result set should not exist anymore'

        except KeyError: pass

        self.db.save ()
        self.db = self.hd.dbopen (self.name)

        try:
            r = self.db.rs [rsid]
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

        for perm in (True, False):
            
            rs = self.db.rs.add (perm)

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

    def testResultSetsValues (self):

        """ It is possible to loop over keys, values and pairs from result sets """

        rs   = self.db.rs.add ()
        keys = []
        vals = range (5)
        
        for i in vals:
            e = Store.Entry ()
            e ['title'] = [Attribute.Text ('%d' % i)]
            
            k = self.db.add (e)
            
            rs.add (k)
            keys.append (k)

        keys.sort ()

        # check the db resultset and a vanilla rs capabilities
        for r in (self.db.entries, rs):

            vs = []
            for v in r: vs.append (v)
            vs.sort ()

            assert keys == vs, 'got %s instead of %s' % (vs, keys)

            vs = []
            for v in r.iterkeys (): vs.append (v)
            vs.sort ()

            assert keys == vs, 'got %s instead of %s' % (vs, keys)

            vs = []
            for v in r.itervalues ():
                v = int (v ['title'][0])
                vs.append (v)
            vs.sort ()
            
            assert vals == vs, 'got %s instead of %s' % (vs, vals)
            
            vs = []
            ks = []
            for k, v in r.iteritems ():
                v = int (v ['title'][0])
                vs.append (v)
                ks.append (k)

            vs.sort ()
            ks.sort ()
            
            assert vals == vs, 'got %s instead of %s' % (vs, vals)
            assert keys == ks, 'got %s instead of %s' % (ks, keys)
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

        def check (rs):
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

        # check on a fresh result set
        rs = self.db.rs.add ()
        check (rs)

        # check on a saved result set
        rsid = self.db.rs.add (permanent = True).id
        self.db.save ()
        
        self.db = self.hd.dbopen (self.name)
        check (self.db.rs [rsid])
        return

    def testFullRSIsReadOnly (self):

        """ It is not possible to alter the database by changing Store ().entries """

        try:
            self.db.entries.add (Store.Key (123))
            assert False, 'should be rejected'
            
        except AttributeError: pass
        except RuntimeError: pass
        
        e = Store.Entry ()
        e ['title'] = [Attribute.Text ('hehe')]
            
        k = self.db.add (e)
            
        try:
            del self.db.entries [k]
            assert False, 'should be rejected'
            
        except AttributeError: pass
        except TypeError: pass

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


class TestView (pybut.TestCase):

    """ Perform data manipulation tests """

    count = 0

    def setUp (self):
        self.fmt  = fmt
        self.hd   = Store.get (self.fmt)
        self.name = pybut.dbname ()
        
        TestContent.count = self.count + 1

        self.db = self.hd.dbimport (self.name, 'ut_database/view.xml')
        self.db.save ()

        # create a RS with all the entries
        self.rs = self.db.rs.add ()
        
        for k in self.db.entries:
            self.rs.add (k)
            
        return


    def testViewText (self):

        for rs in (self.rs, self.db.entries):
                
            v = rs.view ('text')

            res = list (v)
            assert res == [1, 2, 3], 'got %s' % res

        return
    
            
        

if os.environ.has_key ('STORES'):
    fmts = os.environ ['STORES'].split (':')
else:
    fmts = Store.modules ()

classes = (pybut.makeSuite (TestDatabase, 'test'),
           pybut.makeSuite (TestContent,  'test'),
           pybut.makeSuite (TestView,     'test'))

if os.environ.has_key ('CLASS'):
    c = int (os.environ ['CLASS'])
    
    classes = classes [c:c+1]
    
global fmt

for fmt in fmts:
    print "unittest: ------------ storage '%s' ----------" % fmt
    pybut.run (pybut.TestSuite (classes))

