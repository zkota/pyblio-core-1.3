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
        from Pyblio.Cite.Style.BibTeX import AlphaKey
        
        db = Store.get('memory').dbimport(None, 'ut_citation/sample.bip')
        g = AlphaKey(db)

        res = [g.make_key(uid) for uid in range(1, 7)]
        
        self.failUnlessEqual(
            res, ['GF06',
                  'Gob06',
                  'Oth06',
                  '06',
                  'Gob',
                  'Unknown'])


# Fake WordProcessor class that stores the cited keys in an HTML file.

from StringIO import StringIO
from Pyblio.Cite.WP.File import File
    
from Pyblio.Cite import Citator

class TestCitation(pybut.TestCase):

    def setUp(self):
        self.fd = StringIO()
        self.wp = File(self.fd)
        self.db = Store.get('memory').dbimport(None, 'ut_citation/sample.bip')

        self.cit = Citator.Citator()
        self.cit.xmlload('ut_citation/sample.cip')
        self.cit.prepare(self.db, self.wp)

    def testInsert(self):
        self.cit.cite([1])
        self.failUnlessEqual(self.wp.cited, [(1, '1')])

        self.cit.update()
        content = self.fd.getvalue()
        expected = u'''\
<table>
<tr><td>[1]</td><td>Fr\xe9d\xe9ric Gobry and G\xe9d\xe9ric Fobrz. A title. 2006.</td></tr>
</table>'''
        
        self.failUnlessEqual(content, expected)
        
suite = pybut.suite (TestCitation, TestGenerateKeys)
if __name__ == '__main__':  pybut.run (suite)
