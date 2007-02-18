import os, pybut, sys, string

from Pyblio import Store, Schema, Attribute, Query

class TestSimpleQuery (object):
    indexed = False

    def setUp (self):

        self.hd   = Store.get(self.fmt)
        self.name = pybut.dbname()
        
        return

    def _res (self, rs):

        res = list (rs)
        res.sort ()

        return res
    

    def testAndQuery (self):
        
        db = self.hd.dbimport (self.name, pybut.src('ut_query/and.xml'))
        if self.indexed: db.index()
        
        g  = db.schema.txo ['a']

        q = Query.Txo ('txo', g [2]) & Query.AnyWord('First')

        res = self._res (db.query (q))
        assert res == [3], 'got %s' % `res`
        
        return
    
    def testOrQuery (self):
        
        db = self.hd.dbimport (self.name, pybut.src('ut_query/and.xml'))
        if self.indexed: db.index()

        g  = db.schema.txo ['a']

        q = Query.Txo ('txo', g [2]) | Query.AnyWord ('First')

        res = self._res (db.query (q))
        assert res == [1, 2, 3], 'got %s' % `res`
        
        return

    def testNotQuery (self):
        
        db = self.hd.dbimport (self.name, pybut.src('ut_query/and.xml'))
        if self.indexed: db.index()

        g  = db.schema.txo ['a']

        q = ~ (Query.Txo ('txo', g [2]) | Query.AnyWord ('First'))

        res = self._res (db.query (q))
        assert res == [4], 'got %s' % repr (res)
        

    def testTxoQuery (self):
        """ Txo query """

        db = self.hd.dbimport (self.name, pybut.src('ut_query/txo.xml'))
        if self.indexed: db.index()


        # Check that querying for a base txo also returns the children
        g = db.schema.txo ['a']

        a, b, c = g [1], g [2], g [3]
        
        for q, res in ((a, [1]),
                       (b, [2, 3]),
                       (c, [3])):
            
            got = self._res (db.query (Query.Txo ('txo', q)))

            assert got == res, 'got %s instead of %s' % (
                `got`, `res`)

        return

    def textHasFieldQuery (self):

        db = self.hd.dbimport (self.name, pybut.src('ut_query/hasfield.xml'))
        if self.indexed: db.index()

        got = self._res (db.query (Query.HasField ('a')))

        assert got == [1, 3, 4], 'got %s' % got
        return
    

    def testFullTextQuery (self):
        """ Full text query """
        
        sc = Schema.Schema (pybut.src('ut_query/schema.xml'))
        self.db = self.hd.dbcreate (self.name, sc)
        if self.indexed: self.db.index()
        
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

            e = Store.Record ()

            a, b, c = phrase (), phrase (), phrase ()
            
            e ['title'] = [ Attribute.Text (a), Attribute.Text (b) ]
            e ['url']   = [ Attribute.URL (c) ]

            k = self.db.add (e)

            for w in a.split () + b.split () + c.split ():
                if k not in entries [w]:
                    entries [w].append (k)
            

        # Search the occurences of every word
        for w in words:
            
            rs = self.db.query (Query.AnyWord (w))

            vals = []
            for v in rs:
                vals.append (v)

            real = [] + entries [w]

            vals.sort ()
            real.sort ()

            assert vals == real, "%s != %s" % (vals, real)
        return


class TestSimpleQueryFile(TestSimpleQuery, pybut.TestCase):
    fmt = 'file'

class TestSimpleQueryFileIndexed(TestSimpleQuery, pybut.TestCase):
    fmt = 'file'
    indexed = True
    
class TestSimpleQueryDB(TestSimpleQuery, pybut.TestCase):
    fmt = 'bsddb'


files = [
    TestSimpleQueryFile,
    TestSimpleQueryFileIndexed
    ]

bsddb = [
    TestSimpleQueryDB
    ]

# in some cases, we cannot check for bsddb (too old)
try:
    m = Store.get ('bsddb')
    
    suite = pybut.suite (* (files + bsddb))
    
except ImportError, msg:                         
    print "warning: only testing the file store: %s" % msg

    suite = pybut.suite (* files)

if __name__ == '__main__':  pybut.run (suite)
