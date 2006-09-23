# -*- coding: utf-8 -*-

import pybut

from Pyblio.Cite import Keys

class TestGenerate(pybut.TestCase):

    def testDocumentOrder(self):
        g = Keys.DocumentOrder(None)

        uids = [1, 2, 3, 2, 1]
        res = [g.make_key(uid) for uid in uids]

        self.failUnlessEqual(
            res, ['1', '2', '3', '2', '1'])

    def testAuthorYear(self):
        from Pyblio import Store
        db = Store.get('memory').dbimport(None, 'ut_keys/sample.bip')

        g = Keys.AuthorYear(db)

        res = [g.make_key(uid) for uid in range(1, 7)]
        
        self.failUnlessEqual(
            res, ['Gobry:2006',
                  'Gobry:2006:a',
                  'Other:2006',
                  '2006',
                  'Gobry',
                  'Unknown'])

        
suite = pybut.suite (TestGenerate)
if __name__ == '__main__':  pybut.run (suite)
