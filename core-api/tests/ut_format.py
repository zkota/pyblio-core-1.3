# -*- coding: latin-1 -*-

import os, pybut, sys

from Pyblio import Store, Attribute
from Pyblio.Format import Person, join, HTML, access, A, B, I, DSL, Misc, Pages

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
        rec ['singlepage'] = [ Attribute.Text ('123') ]
        rec ['pagerange'] = [ Attribute.Text ('123-134') ]

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

        # join skip missing values
        v = join (', ') [ one ('title'), one ('journal'), one ('gronf') ]
        self._cmp (v, u'My title')

        # join fails when _no_ value is available
        v = join (', ') [ one ('gronf'), one ('rasdf') ]
        try:
            v ()
            assert False
        except DSL.Missing: pass

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
        
    def testInitials (self):
        
        assert Person.initials (u'Frédéric') == 'F.'
        assert Person.initials (u'Jean-Pierre') == 'J.-P.'
        assert Person.initials (u'Jean Pierre') == 'J.P.'
        assert Person.initials (u'J.Pierre') == 'J.P.'

    def testMissingPerson (self):

        def persons ():
            return [Attribute.Person (last = 'Gobry', first = u'Frédéric'),
                    Attribute.Person (last = 'Fobry') ]

        assert Person.initialLast (persons) () == ['F. Gobry', 'Fobry']
        assert Person.firstLast (persons) ()   == [u'Frédéric Gobry', 'Fobry']
        assert Person.lastFirst (persons) ()   == [u'Gobry, Frédéric', 'Fobry']

    def testPages (self):
        all, one = access (self.rec)

        assert Pages.pagesLong (one ('singlepage')) () == u'page\xa0123'
        assert Pages.pagesLong (one ('pagerange')) ()  == u'pages\xa0123-134'

    def testMiscPlural (self):

        assert Misc.plural (DSL.T ([]),  zero = 'zero', more = 'more') () == 'zero'
        assert Misc.plural (DSL.T ([1]), zero = 'zero', more = 'more') () == 'more'
        assert Misc.plural (DSL.T ([1]), zero = 'zero', one = 'one',
                            more = 'more') () == 'one'
        
        assert Misc.plural (DSL.T ([1,2]), zero = 'zero', one = 'one',
                            more = 'more') () == 'more'
        assert Misc.plural (DSL.T ([1,2]), zero = 'zero', one = 'one',
                            two = 'two', more = 'more') () == 'two'
        assert Misc.plural (DSL.T ([1,2,3]), zero = 'zero', one = 'one',
                            two = 'two', more = 'more') () == 'more'

        
suite = pybut.suite (TestFormat)
if __name__ == '__main__':  pybut.run (suite)
