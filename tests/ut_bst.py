import os, pybut, sys

from Pyblio import Registry
from Pyblio import Store
from Pyblio.Format import BST
from Pyblio.Parsers.Semantic import BibTeX

import logging

logging.getLogger('pyblio').setLevel(logging.DEBUG)

class TestBST(pybut.TestCase):
    def testSimple(self):
        Registry.load_default_settings()

        source = pybut.src('ut_bst', 'abbrv.bst')
        o = BST.BST(open(source))

        db = Store.get('memory').dbcreate(
            None, Registry.getSchema('org.pybliographer/bibtex/0.1'))
        reader = BibTeX.Reader()
        rs = reader.parse(open(pybut.src('ut_bst', 'simple.bib')), db)
        
        state = BST.State(rs, db)
        o.Run(state)

        output = """\
\\begin{thebibliography}{1}

\\bibitem{1}
Frederic Gobry and First Last.
\\newblock This is a title.
\\newblock {\em My journal}, 12(123), 2007.

\\bibitem{2}
Frederic Gobry and First Last.
\\newblock {\em This is a title}.

\\end{thebibliography}
"""
        self.failUnlessEqual(state.output, output)

suite = pybut.suite(TestBST)
if __name__ == '__main__':  pybut.run(suite)
