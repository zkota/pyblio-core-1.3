# -*- coding: utf-8 -*-

import pybut

from Pyblio import Store

class TestGenerateKeys(pybut.TestCase):

    def testNumeric(self):
        from Pyblio.Cite.Style.Base import Numeric
        g = Numeric(None)

        uids = [1, 2, 3, 2, 1]
        res = [g.make_key(uid) for uid in uids]

        self.failUnlessEqual(
            res, ['1', '2', '3', '2', '1'])

    def testAuthorYear(self):
        from Pyblio.Cite.Style.BibTeX import AuthorYear
        
        db = Store.get('memory').dbimport(None, 'ut_citation/sample.bip')
        g = AuthorYear(db)

        res = [g.make_key(uid) for uid in range(1, 7)]
        
        self.failUnlessEqual(
            res, ['Gobry:2006',
                  'Gobry:2006:a',
                  'Other:2006',
                  '2006',
                  'Gobry',
                  'Unknown'])


# Fake WordProcessor class that stores the cited keys in an HTML file.

from Pyblio.Format.HTML import generate

class HTMLWP(object):

    def __init__(self):
        self.keys = []
        self.biblio = []
        
    def cite(self, keys):
        self.keys += keys

    def fetch(self):
        return self.keys

    def update_keys(self, keymap):
        pass

    def update_biblio(self):
        self.biblio = []
        def format(t):
            self.biblio.append(generate(t))

        return format
    
from Pyblio.Cite import Citator

class TestCitation(pybut.TestCase):

    def setUp(self):

        self.wp = HTMLWP()
        self.db = Store.get('memory').dbimport(None, 'ut_citation/sample.bip')

        self.cit = Citator.Citator()
        self.cit.xmlload('ut_citation/sample.cip')
        self.cit.prepare(self.db, self.wp)

    def testInsert(self):
        self.cit.cite([1])
        self.failUnlessEqual(self.wp.keys, [(1, '1')])

        self.cit.update()
        self.failUnlessEqual(self.wp.biblio, [u'A title'])
        
suite = pybut.suite (TestCitation, TestGenerateKeys)
if __name__ == '__main__':  pybut.run (suite)
