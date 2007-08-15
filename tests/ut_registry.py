import os, pybut, sys

from Pyblio import Registry

class TestRegistry (pybut.TestCase):

    def setUp(self):
        Registry.reset()
        Registry.load_settings(pybut.src('ut_registry'))
        return

    def testSchemas(self):
        # The list of schemas only returns those for which we know the
        # path.
        self.failUnlessEqual(Registry.schemas(), ['with-path'])

    def testCategories(self):
        c = Registry.get('with-path', 'importers')
        assert len(c) == 2

    def testAdapters(self):
        c = Registry.get('with-adapter', 'adapters')
        self.failUnlessEqual(len(c), 1)

        c = c[0]
        self.failUnlessEqual(c.target, 'another/format')

    def testUnique(self):
        fd = open(',,sample.rip', 'w')
        fd.write('''
[with-path]

path: %(system)s/bibtex-2.xml
''')
        fd.close()
        self.failUnlessRaises(AssertionError, Registry.load_settings, '.')
    
suite = pybut.suite (TestRegistry)
if __name__ == '__main__':  pybut.run (suite)
