import os, pybut, sys, string

from Pyblio import Store, Schema, Attribute, Query

class TestSimpleQuery (pybut.TestCase):

    def setUp (self):

        self.hd   = Store.get (self.fmt)
        self.name = pybut.dbname ()
        
        sc = Schema.Schema ('ut_query/schema.xml')
        self.db = self.hd.dbcreate (self.name, sc)

        return


    def testTxoQuery (self):
        """ Txo query """

        self.db.txo.add ('a')

        g = self.db.txo ['a']

        a = g [g.add (Store.TxoItem ())]
        b = g [g.add (Store.TxoItem ())]

        c = Store.TxoItem ()
        c.parent = b.id

        c = g [g.add (c)]

        e = Store.Entry ()

        e ['enum-a'] = [ Attribute.Txo (a) ]
        ea = self.db.add (e)

        e ['enum-a'] = [ Attribute.Txo (b) ]
        eb = self.db.add (e)

        e ['enum-a'] = [ Attribute.Txo (c) ]
        ec = self.db.add (e)


        # Check that querying for a base txo also returns the children
        
        for q, res in ((a, [ea]),
                       (b, [eb, ec]),
                       (c, [ec])):
            
            rs = self.db.query (Query.Txo ('enum-a', q))

            got = list (rs)
            got.sort ()

            assert got == res, 'got %s instead of %s' % (
                `got`, `res`)

        return
    

    def testFullTextQuery (self):
        """ Full text query """

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
            
            rs = self.db.query (Query.AnyWord (w))

            vals = []
            for v in rs:
                vals.append (v)

            real = [] + entries [w]

            vals.sort ()
            real.sort ()

            assert vals == real, "%s != %s" % (vals, real)
        return




class TestSimpleQueryFile (TestSimpleQuery):
    fmt = 'file'

class TestSimpleQueryDB (TestSimpleQuery):
    fmt = 'bsddb'


suite = pybut.suite (TestSimpleQueryFile, TestSimpleQueryDB)

if __name__ == '__main__':  pybut.run (suite)
