# -*- coding: latin-1 -*-

import os, pybut, sys

from Pyblio import Store, Attribute
from Pyblio.Format import Person, join, HTML, all, one, A, B, I, BR, DSL, switch, Misc, Pages, Text


class TestFormat (pybut.TestCase):

    def setUp (self):
        self.db = Store.get('file').dbopen('ut_format/sample.bip')

        self.rec = self.db[1]
        self.rec ['journal'] = [ ]

        return


    def _cmp (self, v, s):
        stage2 = v(self.db)
        stage3 = stage2(self.rec)
        
        r = HTML.generate(stage3)
        
        assert r == s, 'expected %s, got %s' % (
            repr (s), repr (r))
        
    def testAccessor (self):
        """ Check that accessors behave properly """
        
        # Failure modes are identical for both all and one

        for f in (all, one):
            f ('gronf')

            try:
                f ('jenexistepas')(self.db)
                assert False
            except KeyError: pass

            try:
                f ('journal.zoglu')(self.db)
                assert False
            except KeyError: pass


        # Access modes
        assert all ('title')(self.db)(self.rec)  == self.rec['title']
        assert all ('author')(self.db)(self.rec) == self.rec['author']

        assert one ('title')(self.db)(self.rec) == self.rec['title'][0]
        assert one ('author')(self.db)(self.rec) == self.rec['author'][0]

        self.failUnlessEqual(all('nest.sub')(self.db)(self.rec), self.rec ['nest'] [0].q ['sub'])
        self.failUnlessEqual(one('nest.sub')(self.db)(self.rec), self.rec ['nest'] [0].q ['sub'] [0])
        return


    def testOneAdd (self):
        """ It is possible to add one fields together or with text """

        v = one ('title') + ' ok'
        self._cmp (v, 'My title ok')

        v = 'ok ' + one ('title')
        self._cmp (v, 'ok My title')

        v = 'ok ' + one ('title') + ' ok'
        self._cmp (v, 'ok My title ok')

        # a missing field causes a delayed error
        v = 'ok ' + one ('gronf') + ' ok'
        try:
            v(self.db)(self.rec)
            assert False
        except DSL.Missing: pass
        return

    
    def testAlternate (self):
        """ When the left version fails, use the right version """

        v = one ('title') | 'success'
        self._cmp (v, 'My title')

        v = one ('gronf') | 'success'
        self._cmp (v, 'success')

        v = one ('gronf') | one ('regronf') | 'success'
        self._cmp (v, 'success')

        return

    def testJoin (self):
        """ The join function takes lists of items and joins them """

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
        v = join (', ') [ one ('gronf'), one ('regronf') ]
        phase2 = v(self.db)
        try:
            phase2(self.rec)
            assert False
        except DSL.Missing: pass

        # Join with a weird tag in the middle.
        v = 'a ' + join (BR) [ 'toto', 'tutu' ] + ' b'
        
        self._cmp (v, u'a toto<br>tutu b')
        return
    

    def testMarkup (self):

        v = I [ one ('title') ]
        self._cmp (v, u'<i>My title</i>')

        v = A (href = "http://pybliographer.org/") [ one ('title') ]
        self._cmp (v, u'<a href="http://pybliographer.org/">My title</a>')

        v = I [ 'simple' ]
        self._cmp (v, u'<i>simple</i>')

        v = 'a ' + I [ 'simple ', B [ one ('title') ] ]
        self._cmp (v, u'a <i>simple <b>My title</b></i>')

        v = 'a ' + BR + 'in the middle of a phrase'
        self._cmp (v, u'a <br>in the middle of a phrase')

        return
        
    def testInitials (self):
        
        self.failUnlessEqual(Person.initials(u'Frédéric'), 'F.')
        self.failUnlessEqual(Person.initials(u'Jean-Pierre'), 'J.-P.')
        self.failUnlessEqual(Person.initials(u'Jean Pierre'), 'J.P.')
        self.failUnlessEqual(Person.initials(u'J.Pierre'), 'J.P.')
        self.failUnlessEqual(Person.initials(u'JP'), 'J.P.')

    def testMissingPerson (self):

        r = Store.Record()
        r['author'] = [Attribute.Person (last = 'Gobry', first = u'Frédéric'),
                       Attribute.Person (last = 'Fobry') ]

        def run(fn):
            formatter = fn(all('author'))(self.db)
            return formatter(r)

        assert run(Person.initialLast) == ['F. Gobry', 'Fobry']
        assert run(Person.firstLast)   == [u'Frédéric Gobry', 'Fobry']
        assert run(Person.lastFirst)   == [u'Gobry, Frédéric', 'Fobry']

    def testPages (self):

        assert Pages.pagesLong(one ('singlepage'))(self.db)(self.rec) == u'page\xa0123'
        assert Pages.pagesLong(one ('pagerange'))(self.db)(self.rec)  == u'pages\xa0123-134'

    def testMiscPlural (self):

        zm  = Misc.plural (all('gronf'),
                           zero='zero',
                           more='more')(self.db)

        zom = Misc.plural (all('gronf'),
                           zero='zero',
                           one='one',
                           more='more')(self.db)
        zotm = Misc.plural (all('gronf'),
                            zero='zero',
                            one='one',
                            two='two',
                            more='more')(self.db)

        def run(format, vals):
            r = Store.Record()
            r['gronf'] = vals

            return Text.generate(format(r))
        
        self.failUnlessEqual(run(zm, []), 'zero')
        self.failUnlessEqual(run(zm, [1]), 'more')
        self.failUnlessEqual(run(zom, [1]), 'one')
        self.failUnlessEqual(run(zom, [1, 2]), 'more')
        self.failUnlessEqual(run(zotm, [1, 2]), 'two')
        self.failUnlessEqual(run(zotm, [1, 2, 3]), 'more')

    def testSwitch(self):
        """ Test the 'switch' operator."""
        
        def run(c, r):
            f = c(self.db)
            return Text.generate(f(r))


        def txo(name):
            return Attribute.Txo(self.db.txo['type'].byname(name))
        
        # One cannot use switch on a non-txo attribute
        citation = switch('title').default(one('title'))
        try:
            citation(self.db)
            assert False, 'should not be accepted'
        except TypeError:
            pass

        # A switch fails when the value to switch on does not exist
        # and there is no default case.
        citation = switch('type').case(ARTICLE=one('title'))

        try:
            run(citation, self.rec)
            assert False, 'should not succeed'
        except DSL.Missing:
            pass

        # With a default case, it should pass
        citation = switch('type').case(ARTICLE=one('singlepage'))
        citation = citation.default(one('title'))

        self.failUnlessEqual(run(citation, self.rec), 'My title')

        # Test with the actual value
        self.rec['type'] = [txo('ARTICLE')]
        self.failUnlessEqual(run(citation, self.rec), '123')
        
        # Another value will also return the default
        self.rec['type'] = [txo('BOOK')]
        self.failUnlessEqual(run(citation, self.rec), 'My title')
        return
    

class TestOutput (pybut.TestCase):

    def setUp (self):
        self.db = Store.get('file').dbopen('ut_format/sample.bip')

        self.rec = self.db[1]
        self.rec ['journal'] = [ ]
        self.rec ['title'] = [ Attribute.Text (u'My < title &') ]

        return


class TestOutputHTML (TestOutput):


    def _cmp (self, v, s):
        stage2 = v(self.db)
        stage3 = stage2(self.rec)
        
        r = HTML.generate (stage3)
        
        assert r == s, 'expected %s, got %s' % (
            repr (s), repr (r))

    
    def testEscape (self):
        v = one ('title') + ' ok &'
        self._cmp (v, 'My &lt; title &amp; ok &amp;')

        
class TestOutputText (TestOutput):


    def _cmp (self, v, s):
        stage2 = v(self.db)
        stage3 = stage2(self.rec)
        
        r = Text.generate(stage3)
        
        assert r == s, 'expected %s, got %s' % (
            repr (s), repr (r))

    
    def testEscape (self):
        v = one ('title') + ' ok &'
        self._cmp (v, 'My < title & ok &')


        
suite = pybut.suite (TestFormat, TestOutputHTML, TestOutputText)
if __name__ == '__main__':  pybut.run (suite)
