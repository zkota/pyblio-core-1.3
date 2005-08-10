import os, pybut, sys, string

from Pyblio import Store, Schema, Attribute, Query
from Pyblio.Sort import OrderBy

class TestDatabase (pybut.TestCase):

    """ Perform tests on the Pyblio.Stores main functions """

    def setUp (self):
        self.hd  = Store.get (self.fmt)

        self.nm = pybut.dbname ()
        return
    
    def testCreate (self):
        ''' Try to create a database, and check its content '''

        sc = Schema.Schema ('ut_database/schema.xml')
        db = self.hd.dbcreate (self.nm, sc)

        e = Store.Record ()

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

        self.hd   = Store.get (self.fmt)
        self.name = pybut.dbname ()
        
        TestContent.count = self.count + 1

        sc = Schema.Schema ('ut_database/schema.xml')
        self.db = self.hd.dbcreate (self.name, sc)

        return

    def testInsertRemove (self):
        """ Check the db behavior upon insertion/suppression """

        import copy
        
        e = Store.Record ()

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

        e = Store.Record ()

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

        e  = Store.Record ()
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

        e = Store.Record ()

        e ['title'] = [ Attribute.Text ('a') ]
        a = self.db.add (e)

        e ['title'] = [ Attribute.Text ('b') ]
        b = self.db.add (e)

        def check (res):

            for w, r in zip (('a', 'b', 'c'), res):

                q = Query.AnyWord (w)

                rs = map (None, self.db.query (q))
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
        
        e = Store.Record ()

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
    


    def testTxoAdd (self):

        """ Check for enum addition in the database """
        
        # add some enums to the database
        i = Store.TxoItem ()

        a  = []
        va = ['A / 1', 'A / 2']
        ka = []

        g = self.db.txo ['a']
        
        for k in va:
            i.names [''] = k
            ka.append (g.add (i))
            
        b = []
        vb = ['B / 1', 'B / 2']
        
        g = self.db.txo ['b']
        for k in vb:
            i.names [''] = k
            g.add (i)

        na = []
        for v in self.db.txo ['a'].values ():
            na.append (v.names [''])

        assert na == va
        assert list (g) == ka
        return

    def testTxoInDB (self):

        """ Use Txos in database entries """
        
        # add some enums to the database
        i = Store.TxoItem ()

        a  = []
        va = ['A / 1', 'A / 2']

        g = self.db.txo ['a']
        for k in va:
            i.names [''] = k

            v = g.add (i)
            a.append (self.db.txo ['a'][v])
        

        e = Store.Record ()
        e ['enum-a'] = [ Attribute.Txo (a [0]) ]
        
        self.db.add (e)

        f = ',,enumdb-' + self.fmt

        fd = open (f, 'w')
        self.db.xmlwrite (fd)
        fd.close ()
        
        pybut.fileeq (f, 'ut_database/enumerate.xml')
        os.unlink (f)
        return

    def testTxoByName (self):
        
        g = self.db.txo ['a']

        i = Store.TxoItem ()

        r = {}
        
        for k in ('A', 'B', 'C'):
            i.names ['C'] = k
            v = g.add (i)

            r [k] = v

        for k in ('A', 'B', 'C'):
            assert self.db.txo ['a'].byname (k).id == r [k]

        return
    
    def testNamedResultSet (self):

        e = Store.Record ()

        e ['title'] = [Attribute.Text ('a sample')]
        for i in range (5):
            self.db.add (e)
        
        e ['title'] = [Attribute.Text ('youyou')]
        for i in range (5):
            self.db.add (e)

        rs = self.db.query (Query.AnyWord ('youyou'), permanent = True)
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
        e = Store.Record ()
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
            e = Store.Record ()
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

        e = Store.Record ()
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
            e = Store.Record ()
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
        
        e = Store.Record ()
        e ['title'] = [Attribute.Text ('hehe')]
            
        k = self.db.add (e)
            
        try:
            del self.db.entries [k]
            assert False, 'should be rejected'
            
        except AttributeError: pass
        except TypeError: pass

        return


    def testTxoDel (self):

        """ Forbid the removal of a Txo definition that is in use """

        from Pyblio import Exceptions
        
        # Create two enums, one that will be used, the other not. Try
        # to remove both.
        i = Store.TxoItem ()

        a  = []
        va = ['A / 1', 'A / 2']

        g = self.db.txo ['a']
        for k in va:
            i.names [''] = k
            v = g.add (i)

            a.append (self.db.txo ['a'][v])
            
        e = Store.Record ()
        
        e ['enum-a'] = [Attribute.Txo (a [1])]
        self.db.add (e)

        del self.db.txo ['a'][a [0].id]

        try:
            del self.db.txo ['a'][a [1].id]
            assert False, 'should not be possible'
            
        except Exceptions.ConstraintError:
            pass

        return

    def testTxoDelLeaf (self):

        """ Forbid the removal of a Txo definition that is not a leaf """

        from Pyblio import Exceptions
        
        g = self.db.txo ['a']

        a = g.add (Store.TxoItem ())
        
        b = Store.TxoItem ()
        b.parent = a

        b = g.add (b)
        
        try:
            del g [a]
            assert False, 'should not succeed'
            
        except Exceptions.ConstraintError:
            pass


        del g [b]
        del g [a]
        
        return


    def testTxoValidParent (self):

        """ Refuse invalid parent value for a TxoItem """
        from Pyblio import Exceptions

        g = self.db.txo ['a']

        i = Store.TxoItem ()
        i.parent = 123

        try:
            g.add (i)
            assert False, 'should not succeed'
            
        except Exceptions.ConstraintError:
            pass

        # Check at update

        i.parent = None
        k = g.add (i)

        i.parent = 123

        try:
            g [k] = i
            assert False, 'should not succeed'
            
        except Exceptions.ConstraintError:
            pass

        return


class BaseView (pybut.TestCase):
    
    count = 0
    
    def setUp (self):

        self.hd   = Store.get (self.fmt)
        self.name = pybut.dbname ()
        
        BaseView.count = self.count + 1

        self.db = self.hd.dbimport (self.name, self.dbfile)
        self.db.save ()

        # create a RS with all the entries
        self.rs = self.db.rs.add ()
        
        for k in self.db.entries:
            self.rs.add (k)

        self.a = Store.Record ()
        self.b = Store.Record ()
        return

class TestOrdering (BaseView):

    """ Perform data manipulation tests """

    dbfile = 'ut_database/order.xml'

    def testAscDesc (self):

        v = list (self.rs.view (OrderBy ('a')))
        assert v [-2:] == [1, 2], 'got %s' % v

        v = list (self.rs.view (OrderBy ('a') & OrderBy ('b')))
        assert v [-4:] == [4, 3, 1, 2], 'got %s' % v


class TestView (BaseView):

    """ Perform data manipulation tests """

    dbfile = 'ut_database/view.xml'

    def testIterView (self):

        
        for rs in (self.rs, self.db.entries):
            
            v = rs.view (OrderBy ('text'))
            r = []
            
            for k in v.iterkeys (): r.append (k)

            assert r in ([1, 4, 2, 3],
                         [4, 1, 2, 3]), 'got %s' % r

            r = []
            for k, x in v.iteritems ():
                r.append (k)
                assert self.db [k] == x, 'got %s' % repr (x)

            assert r in ([1, 4, 2, 3],
                         [4, 1, 2, 3]), 'got %s' % r

            r = []
            for x in v.itervalues ():
                r.append (x.key)
                assert self.db [x.key] == x
                
            assert r in ([1, 4, 2, 3],
                         [4, 1, 2, 3]), 'got %s' % r

        return

        
    def testViewText (self):

        for rs in (self.rs, self.db.entries):
                
            v = rs.view (OrderBy ('text'))

            assert len (v) == 4
            
            res = list (v)
            assert res in ([1, 4, 2, 3],
                           [4, 1, 2, 3]), 'got %s' % res

        return


    def testViewDate (self):

        for rs in (self.rs, self.db.entries):
                
            v = rs.view (OrderBy ('date'))

            assert len (v) == 4
            
            res = list (v)
            assert res in ([4, 3, 1, 2],), 'got %s' % res

        return


    def testIndexed (self):

        v = self.rs.view (OrderBy ('text'))

        res = []
        for i in range (len (self.rs)):
            res.append (v [i])

        assert res == list (v), 'got %s and %s' % (
            res, list (v))
        
        return

    def testInsertRS (self):

        """ A view is updated when the result set is updated """

        v = self.rs.view (OrderBy ('text'))

        e = Store.Record ()
        e ['text'] = Attribute.Text ('zzzzzzzzz')

        k = self.db.add (e)

        self.rs.add (k)

        r = list (v)
        assert r in ([1, 4, 2, 3, k],
                     [4, 1, 2, 3, k]), 'got %s' % `r`
        return
        
    def testInsertDB (self):

        """ A view of the DB is updated when the result set is updated """

        v = self.db.entries.view (OrderBy ('text'))

        e = Store.Record ()
        e ['text'] = Attribute.Text ('zzzzzzzzz')

        k = self.db.add (e)

        r = list (v)
        assert r in ([1, 4, 2, 3, k],
                     [4, 1, 2, 3, k]), 'got %s' % `r`
        return

    def testDelRS (self):

        """ A view is updated when removing from the result set  """

        v = self.rs.view (OrderBy ('text'))

        del self.rs [4]

        r = list (v)
        assert r == [1, 2, 3], 'got %s' % `r`

        # removing from the DB directly should cascade
        del self.db [2]
        
        r = list (v)
        assert r == [1, 3], 'got %s' % `r`

        return

    
    def testDelDB (self):

        """ A view of the DB is updated when removing from the DB """

        v = self.db.entries.view (OrderBy ('text'))

        del self.db [4]

        r = list (v)
        assert r == [1, 2, 3], 'got %s' % `r`

        return

    def testChangeDB (self):

        """ Doing a modification in an entry is reflected in the DB views """
        
        v = self.db.entries.view (OrderBy ('text'))
        
        e = self.db [4]
        e ['text'] = Attribute.Text ('zzzzzzzzz')

        self.db [4] = e

        r = list (v)
        assert r == [1, 2, 3, 4], 'got %s' % r

        return

    def testChangeRS (self):

        """ Doing a modification in an entry is reflected in the RS views """
        
        v = self.rs.view (OrderBy ('text'))
        
        e = self.db [4]
        e ['text'] = Attribute.Text ('zzzzzzzzz')

        self.db [4] = e

        r = list (v)
        assert r == [1, 2, 3, 4], 'got %s' % r

        return


class TestCollate (pybut.TestCase):

    def setUp (self):

        self.hd   = Store.get (self.fmt)
        self.name = pybut.dbname ()
        
        self.db = self.hd.dbimport (self.name, 'ut_database/collate.xml')
        self.db.save ()

        return

    def check (self, got, exp):

        got = list (got)
        got.sort ()

        assert got == exp, "expected %s, got %s" % (
            repr (exp), repr (got))
        
    def testCollateTest (self):

        rss = self.db.collate (self.db.entries, 'enum')

        self.check (rss [Attribute.Txo (self.db.txo ['type'][1])], [1])
        self.check (rss [Attribute.Txo (self.db.txo ['type'][2])], [2, 3, 4])
    

class TestDatabaseFile (TestDatabase):
    fmt = 'file'

class TestContentFile (TestContent):
    fmt = 'file'

class TestViewFile (TestView):
    fmt = 'file'

class TestOrderingFile (TestOrdering):
    fmt = 'file'

class TestCollateFile (TestCollate):
    fmt = 'file'

class TestDatabaseDB (TestDatabase):
    fmt = 'bsddb'

class TestContentDB (TestContent):
    fmt = 'bsddb'

class TestViewDB (TestView):
    fmt = 'bsddb'

class TestCollateDB (TestCollate):
    fmt = 'bsddb'

class TestOrderingDB (TestOrdering):
    fmt = 'bsddb'


suite = pybut.suite (TestDatabaseFile, TestContentFile, TestViewFile, TestCollateFile, TestOrderingFile,
                     TestDatabaseDB,   TestContentDB,   TestViewDB,   TestCollateDB,   TestOrderingDB,
                     )

if __name__ == '__main__':  pybut.run (suite)
