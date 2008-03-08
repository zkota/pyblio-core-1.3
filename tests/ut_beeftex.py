# -*- coding: utf-8 -*-

import os, pybut, sys

from Pyblio import BeefTeX

def fp(*args):
    return pybut.fp(*(('ut_beeftex',) + args))


class TestBeefTeX(pybut.TestCase):
        
    def testIdempotent(self):
        src = fp('idempotent.bib')
        bt = BeefTeX.BeefTeX(src)

        tmp = pybut.dbname()
        bt.Save(tmp)

        pybut.fileeq(src, tmp)

    def testTransform(self):
        bt = BeefTeX.BeefTeX(fp('transform.bib'))

        self.failUnlessEqual(bt.Keys(), ['a', 'c', 'd'])

        bt.Delete('d')
        self.failUnlessEqual(bt.Keys(), ['a', 'c'])

        tmp = pybut.dbname()
        bt.Save(tmp)

        pybut.fileeq(fp('transformed.bib'), tmp)

suite = pybut.suite(TestBeefTeX)

if __name__ == '__main__':  pybut.run (suite)
