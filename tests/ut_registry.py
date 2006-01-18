import os, pybut, sys

from Pyblio import Registry

class TestRegistry (pybut.TestCase):

    def setUp(self):
        Registry.reset()
        Registry.parse('ut_registry')
        return

    def testSchemas(self):
        # The list of schemas only returns those for which we know the
        # path.
        self.failUnlessEqual(Registry.schemas(), ['with-path'])

    def testCategories(self):
        c = Registry.get('with-path', 'importers')

        assert len(c) == 2
        
    
suite = pybut.suite (TestRegistry)
if __name__ == '__main__':  pybut.run (suite)
