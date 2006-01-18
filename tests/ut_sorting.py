import os, pybut, sys, string

from Pyblio import Store, Schema, Attribute, Query
from Pyblio.Sort import OrderBy, compare

class TestOrdering (pybut.TestCase):

    """ Perform data manipulation tests """

    def setUp (self):

        self.a = Store.Record ()
        self.b = Store.Record ()

    def isLess (self, q, a, b):

        qa = q.cmp_key (a)
        qb = q.cmp_key (b)

        assert compare (qa, qb) == -1, '%s [%s] should be < to %s [%s]' % (
            a, repr (qa), b, repr (qb))
        
    def testSimple (self):
        
        self.a ['a'] = [ Attribute.Text ('ABC') ]
        self.b ['a'] = [ Attribute.Text ('BCD') ]

        q = OrderBy ('a')
        self.isLess (q, self.a, self.b)

        q = OrderBy ('a', asc = False)
        self.isLess (q, self.b, self.a)


    def testMultiValued (self):
        
        self.a ['a'] = [ Attribute.Text ('ABC'),
                         Attribute.Text ('ABC')]
        
        self.b ['a'] = [ Attribute.Text ('ABC'),
                         Attribute.Text ('BCD')]

        q = OrderBy ('a')
        self.isLess (q, self.a, self.b)

        q = OrderBy ('a', asc = False)
        self.isLess (q, self.b, self.a)

    def testMissingIsLess (self):
        
        self.a ['a'] = [ Attribute.Text ('ABC') ]
        
        self.b ['a'] = [ Attribute.Text ('ABC'),
                         Attribute.Text ('BCD')]

        q = OrderBy ('a')
        self.isLess (q, self.a, self.b)

        q = OrderBy ('a', asc = False)
        self.isLess (q, self.b, self.a)

    def testShorterIsLess (self):
        self.a ['a'] = [ Attribute.Text ('ABC') ]
        self.b ['a'] = [ Attribute.Text ('ABCD') ]
        
        q = OrderBy ('a')
        self.isLess (q, self.a, self.b)

        q = OrderBy ('a', asc = False)
        self.isLess (q, self.b, self.a)

    def testShorterIsLessThanMultiple (self):
        self.a ['a'] = [ Attribute.Text ('ABC'),
                         Attribute.Text ('DEF')]
        self.b ['a'] = [ Attribute.Text ('ABCD'),
                         Attribute.Text ('EF') ]
        
        q = OrderBy ('a')
        self.isLess (q, self.a, self.b)

        q = OrderBy ('a', asc = False)
        self.isLess (q, self.b, self.a)

        

suite = pybut.suite (TestOrdering)

if __name__ == '__main__':  pybut.run (suite)
