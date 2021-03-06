import os, pybut, sys, string

from Pyblio import Store, Schema, Attribute, Query
from Pyblio.Sort import OrderBy

def fp(*args):
    return pybut.fp(*(('ut_database',) + args))

# in some cases, we cannot check for bsddb (too old)
try:
    m = Store.get ('bsddb')
    skip_bsddb = None
    
except ImportError, msg:                         
    print "warning: only testing the file store: %s" % msg

    skip_bsddb = 'bsddb is missing'


class TDatabase(object):

    """ Perform tests on the Pyblio.Stores main functions """

    def setUp (self):
        self.hd  = Store.get (self.fmt)

        self.nm = pybut.dbname ()
        return
    
    def testCreate (self):
        ''' Try to create a database, and check its content '''

        sc = Schema.Schema(fp('schema.xml'))
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
        
        sc = Schema.Schema (fp('schema.xml'))
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

        sc = Schema.Schema(fp('schema.xml'))

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

        db = self.hd.dbimport (self.nm, fp('sample.xml'))
        db.save ()

        nmo = pybut.dbname ()
        
        fd = open (nmo, 'w')
        db.xmlwrite (fd)
        fd.close ()

        pybut.fileeq (nmo, fp('sample.xml'))
        self.hd.dbdestroy (self.nm, nobackup = True)

        os.unlink (nmo)
        return

    def testHeader(self):
        sc = Schema.Schema(fp('schema.xml'))
        db = self.hd.dbcreate(self.nm, sc)

        msg = u'Hi, folks'
        
        db.header = msg
        db.save()

        other = self.hd.dbopen(self.nm)
        self.failUnlessEqual(other.header, msg)
        return
    
class TContent(object):

    """ Perform data manipulation tests """

    count = 0

    def setUp (self):

        self.hd   = Store.get (self.fmt)
        self.name = pybut.dbname ()
        
        TContent.count = self.count + 1

        sc = Schema.Schema(fp('schema.xml'))
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
        rs = self.db.rs.new()
        
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

                rs = map (None, self.db.query(q))
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

    def testTxoInDB (self):

        """ Use Txos in database entries """
        
        # add some enums to the database
        a = self.db.schema.txo['a']

        e = Store.Record ()
        e ['enum-a'] = [ Attribute.Txo (a [1]) ]
        
        self.db.add (e)

        f = ',,enumdb-' + self.fmt

        fd = open (f, 'w')
        self.db.xmlwrite (fd)
        fd.close ()
        
        pybut.fileeq (f, fp('enumerate.xml'))
        os.unlink (f)
        return

    def testTxoByName (self):
        
        g = self.db.schema.txo['a']

        # a map from C name to id
        r = {}
        for k in g.keys():
            r [g[k].names['C']] = k

        for k in ('J', 'B'):
            assert g.byname(k).id == r[k]

        return
    
    def testNamedResultSet (self):

        e = Store.Record ()

        e['title'] = [Attribute.Text('a sample')]
        for i in range(5):
            self.db.add(e)
        
        e['title'] = [Attribute.Text('youyou')]
        for i in range(5):
            self.db.add(e)

        rs = self.db.query(Query.AnyWord('youyou'))
        rs.name = u'my set'

        def integrity (rs):
            i = 0
            for k in rs:
                v = self.db [k] ['title'] [0]
                assert v == 'youyou', 'got %s %s' % (repr (v), repr (self.db [k]))
                i = i + 1

            assert i == 5, 'obtained %d' % i
            assert rs.name == u'my set'
            return

        rsid = rs.id
        
        integrity(rs)
        self.db.rs.update(rs)
        integrity(self.db.rs[rsid])
        
        del rs
        
        self.db.save ()
        self.db = self.hd.dbopen(self.name)

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
            
            rs = self.db.rs.new()

            # put all the entries
            for i in items:
                rs.add (i)

            if perm:
                self.db.rs.update(rs)
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
            if perm:
                self.db.rs.update(rs)

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

            for i in items:
                self.failUnlessEqual(i in rs, i in check)
                
        return

    def testResultSetsValues (self):
        """Loop over keys, values and pairs from result sets """

        rs   = self.db.rs.new()
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

        rs = self.db.rs.new()

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

    def testResultSetDestroy(self):

        rs = self.db.rs.new()
        
        for i in range(5):
            e = Store.Record()
            k = self.db.add(e)
            rs.add(k)
        
        for i in range(2):
            e = Store.Record()
            k = self.db.add(e)
            

        assert len(self.db.entries) == 7
        rs.destroy()
        assert len(self.db.entries) == 2
        return
    
            
    def testResultSetUpdate(self):

        """ If an item is removed from the database, it is removed
        from the result sets too.  """

        def check(rs):
            e = Store.Record()
            items = []
        
            for i in range(5):
                items.append(self.db.add(e))
        
            for i in items: rs.add(i)

            # remove one item in the db
            del self.db[items[0]]

            got = map(None, rs)
            got.sort()

            assert got == items[1:], \
                   "expected %s, got %s" % (items[1:], got)
            return

        # check on a fresh result set
        rs = self.db.rs.new()
        check (rs)

        # check on a saved result set
        rs = self.db.rs.new()
        self.db.rs.update(rs)
        self.db.save()

        rsid = rs.id
        self.db = self.hd.dbopen(self.name)
        check(self.db.rs[rsid])
        return

    def testFullRSIsReadOnly (self):
        """ Fail to alter the database by changing Store().entries. """

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

class BaseView(object):
    
    count = 0
    
    def setUp (self):

        self.hd   = Store.get (self.fmt)
        self.name = pybut.dbname ()
        
        BaseView.count = self.count + 1

        self.db = self.hd.dbimport (self.name, self.dbfile)
        self.db.save ()

        # create a RS with all the entries
        self.rs = self.db.rs.new()
        
        for k in self.db.entries:
            self.rs.add (k)

        self.a = Store.Record ()
        self.b = Store.Record ()
        return

class TOrdering(BaseView):

    """ Perform data manipulation tests """

    dbfile = fp('order.xml')

    def testAscDesc (self):

        v = list (self.rs.view (OrderBy ('a')))
        assert v [-2:] == [1, 2], 'got %s' % v

        v = list (self.rs.view (OrderBy ('a') & OrderBy ('b')))
        assert v [-4:] == [4, 3, 1, 2], 'got %s' % v


class TView(BaseView):

    """ Perform data manipulation tests """

    dbfile = fp('view.xml')

    def testIterView (self):
        for rs in (self.rs, self.db.entries):
            v = rs.view(OrderBy('text'))
            r = []
            
            for k in v.iterkeys(): r.append(k)

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

    def testGetIndex(self):
        """ Check that one can get the index of a key in a given view."""
        
        v = self.rs.view(OrderBy('text'))

        for r in self.rs.itervalues():
            idx = v.index(r.key)
            assert v[idx] == r.key
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
        
        v = self.db.entries.view(OrderBy('text'))
        
        e = self.db[4]
        e ['text'] = Attribute.Text('zzzzzzzzz')

        self.db[4] = e

        r = list(v)
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

class TCallbacks(object):
    """ Check the proper behavior of callbacks & signals """

    def setUp (self):

        self.hd = Store.get(self.fmt)
        self.nm = pybut.dbname ()

        sc = Schema.Schema(fp('schema.xml'))
        self.db = self.hd.dbcreate(self.nm, sc)
        return

    def testChangeThenCallback(self):
        """ Changing a record in a result set triggers a callback """

        called = {'k': None}
        def _do_call(k):
            called['k'] = k


        def check(v):
            self.failUnlessEqual(called['k'], v)
            called['k'] = None

        rs1 = self.db.rs.new()
        rs2 = self.db.rs.new()

        # First element is the one used to update the content, second
        # is the one on which we check the callback
        iterables = [
            (self.db, self.db.entries),
            (self.db, self.db.entries.view(OrderBy('text'))),
            (rs1, rs1),
            (rs2, rs2.view(OrderBy('text')))]
            
        for src, rs in iterables:
            r = Store.Record()
            k1 = self.db.add(r)

            r = Store.Record()
            k2 = self.db.add(r)

            if src is not self.db:
                src.add(k1)

                # Now, adding a new record to the rs should trigger a callback
                rs.register('add-item', _do_call)
                src.add(k2)
            
                check(k2)

            # so does updating
            rs.register('update-item', _do_call)
            self.db[k1] = r
            
            check(k1)

            # ...and deleting from rs
            rs.register('delete-item', _do_call)

            if src is not self.db:
                del src[k2]
                check(k2)

            # ...but also from the whole db
            del self.db[k1]
            check(k1)
        return
    
        
    def testNoChangeNoCallback(self):
        """ Changing a record _not_ in a result set triggers no callback """

        def _dont_call(*args):
            assert False, "don't call me"

        r = Store.Record()
        k1 = self.db.add(r)

        r = Store.Record()
        k2 = self.db.add(r)

        rs = self.db.rs.new()
        rs.add(k1)

        # Now, adding a new record to the db should not trigger a
        # callback
        rs.register('add-item', _dont_call)
        self.db.add(r)

        # ...same thing when _updating_ a record not in the set
        rs.register('update-item', _dont_call)
        self.db[k2] = r

        # ...same thing when _deleting_ a record
        rs.register('delete-item', _dont_call)
        del self.db[k2]

        
class TCollate(object):

    def setUp (self):

        self.hd   = Store.get (self.fmt)
        self.name = pybut.dbname ()
        
        self.db = self.hd.dbimport (self.name, fp('collate.xml'))
        self.db.save ()

        return

    def check (self, got, exp):

        got = list (got)
        got.sort ()

        assert got == exp, "expected %s, got %s" % (
            repr (exp), repr (got))
        
    def testCollateTest (self):

        rss = self.db.collate (self.db.entries, 'enum')

        self.check(rss[Attribute.Txo(self.db.schema.txo['type'][1])], [1])
        self.check(rss[Attribute.Txo(self.db.schema.txo['type'][2])], [2, 3, 4])


class TestMemoryStore(pybut.TestCase):

    def setUp(self):
        self.hd = Store.get('memory')
        self.name = pybut.dbname()
        return

    def testCreate(self):
        sc = Schema.Schema(fp('schema.xml'))
        db = self.hd.dbcreate(self.name, sc)

        try:
            os.stat(self.name)
            assert False, 'the file should not be created'
        except OSError:
            pass

        return
    
    def testImport(self):
        db = self.hd.dbimport(self.name, fp('sample.xml'))
        try:
            os.stat(self.name)
            assert False, 'the file should not be created'
        except OSError:
            pass

        nmo = pybut.dbname ()
        
        fd = open (nmo, 'w')
        db.xmlwrite (fd)
        fd.close ()

        pybut.fileeq (nmo, fp('sample.xml'))
        return

    def testNoSave(self):
        db = self.hd.dbimport(self.name, fp('sample.xml'))
        db.save()
        try:
            os.stat(self.name)
            assert False, 'the file should not be created'
        except OSError:
            pass

        return

    def testNoOpen(self):
        try:
            db = self.hd.dbopen(fp('sample.xml'))
            assert False, 'should not work'
            
        except Store.StoreError:
            pass
        return
    
class TestDatabaseFile(TDatabase, pybut.TestCase):
    fmt = 'file'

class TestContentFile(TContent, pybut.TestCase):
    fmt = 'file'

class TestViewFile(TView, pybut.TestCase):
    fmt = 'file'

class TestOrderingFile(TOrdering, pybut.TestCase):
    fmt = 'file'

class TestCollateFile(TCollate, pybut.TestCase):
    fmt = 'file'

class TestCallbacksFile(TCallbacks, pybut.TestCase):
    fmt = 'file'

class TestDatabaseDB(TDatabase, pybut.TestCase):
    fmt = 'bsddb'
    skip = skip_bsddb
    
class TestContentDB(TContent, pybut.TestCase):
    fmt = 'bsddb'
    skip = skip_bsddb

class TestViewDB(TView, pybut.TestCase):
    fmt = 'bsddb'
    skip = skip_bsddb

class TestCollateDB (TCollate, pybut.TestCase):
    fmt = 'bsddb'
    skip = skip_bsddb

class TestOrderingDB (TOrdering, pybut.TestCase):
    fmt = 'bsddb'
    skip = skip_bsddb

class TestCallbacksDB(TCallbacks, pybut.TestCase):
    fmt = 'bsddb'
    skip = skip_bsddb

files = [ TestDatabaseFile,
          TestContentFile,
          TestViewFile,
          TestCollateFile,
          TestOrderingFile,
          TestMemoryStore,
          TestCallbacksFile,
          ]

bsddb = [ TestDatabaseDB,
          TestContentDB,
          TestViewDB,
          TestCollateDB,
          TestOrderingDB,
          TestCallbacksDB,
          ]

## # in some cases, we cannot check for bsddb (too old)
## if skip_bsddb:
##     suite = pybut.suite (* files)
## else:
##     suite = pybut.suite (* (files + bsddb))

## if __name__ == '__main__':  pybut.run (suite)
