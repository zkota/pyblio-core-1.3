# -*- coding: latin-1 -*-

import os, pybut, sys

from Pyblio import Store, Attribute
from Pyblio.Format import Person, join, HTML, access, A, B, I, DSL

class TestFormat (pybut.TestCase):

    def setUp (self):
        rec = Store.Record ()

        rec ['title'] = [ Attribute.Text (u'My title') ]

        rec ['author'] = [
            Attribute.Person (last = u'Gobry', first = u'Frédéric'),
            Attribute.Person (last = u'Fobry', first = u'Grédéric'),
            Attribute.Person (last = u'Dobry', first = u'Lrédéric'),
            ]

        rec ['journal'] = [ ]

        self.rec = rec
        
        return

    def _cmp (self, v, s):
        r = HTML.generate (v ())
        
        assert r == s, 'expected %s, got %s' % (
            repr (s), repr (r))
        
    def testAccessor (self):
        """ Check that accessors behave properly """
        
        all, one = access (self.rec)

        # Failure modes are identical for both all and one

        for f in (all, one):
            f ('gronf')

            try:
                f ('gronf') ()
                assert False
            except DSL.Missing: pass

            try:
                f ('journal') ()
                assert False
            except DSL.Missing: pass

        # Access modes
        assert all ('title')  () == self.rec ['title']
        assert all ('author') () == self.rec ['author']

        assert one ('title')  () == self.rec ['title']  [0]
        assert one ('author') () == self.rec ['author'] [0]
        return


    def testOneAdd (self):
        """ It is possible to add one fields together or with text """
        all, one = access (self.rec)

        v = one ('title') + ' ok'
        self._cmp (v, 'My title ok')

        v = 'ok ' + one ('title')
        self._cmp (v, 'ok My title')

        v = 'ok ' + one ('title') + ' ok'
        self._cmp (v, 'ok My title ok')

        # a missing field causes a delayed error
        v = 'ok ' + one ('gronf') + ' ok'
        try:
            v ()
            assert False
        except DSL.Missing: pass
        return

    
    def testAlternate (self):
        """ When the left version fails, use the right version """
        all, one = access (self.rec)

        v = one ('title') | 'success'
        self._cmp (v, 'My title')

        v = one ('gronf') | 'success'
        self._cmp (v, 'success')

        v = one ('gronf') | one ('gudule') | 'success'
        self._cmp (v, 'success')

        return

    def testJoin (self):
        """ The join function takes lists of items and joins them """
        all, one = access (self.rec)

        v = join (', ') [ Person.lastFirst (all ('author')) ]
        self._cmp (v, u'Gobry, Frédéric, Fobry, Grédéric, Dobry, Lrédéric')

        v = join (', ') [ 'a', 'b', 'c' ]
        self._cmp (v, u'a, b, c')
        
        v = join (', ', last = '; ') [ 'a', 'b', 'c' ]
        self._cmp (v, u'a, b; c')

        v = join (', ') [ 'a', 'b', 'c' ] + ' ok'
        self._cmp (v, u'a, b, c ok')

        # Joins skip missing values
        v = join (', ') [ one ('title'), one ('journal'), one ('gronf') ]
        self._cmp (v, u'My title')

        return
    

    def testMarkup (self):

        all, one = access (self.rec)

        v = I [ one ('title') ]
        self._cmp (v, u'<i>My title</i>')

        v = A (href = "http://pybliographer.org/") [ one ('title') ]
        self._cmp (v, u'<a href="http://pybliographer.org/">My title</a>')

        v = I [ 'simple' ]
        self._cmp (v, u'<i>simple</i>')

        v = 'a ' + I [ 'simple ', B [ one ('title') ] ]
        self._cmp (v, u'a <i>simple <b>My title</b></i>')
        return
        
        
        
suite = pybut.suite (TestFormat)
if __name__ == '__main__':  pybut.run (suite)
