#! /usr/bin/python

"""Unit test for Import"""


import os, sys, unittest
# Setup the system so that we import the current python files
srcdir = os.environ.get ('srcdir', '.')
sys.path.insert (0, os.path.join (srcdir, '..'))

assert os.path.isdir (os.path.join (srcdir, '..', 'Pyblio'))


from Pyblio import Base, stubs
from Pyblio.Import import Import

verbose = 1


#----------------------------------------------------------------------

class GeneralTestCase(unittest.TestCase):
    parameter = 'XXX'
    
    def setUp (self):
        self.rdr = Import.Reader()
        self.rdr.entry =  Base.create('O')
        
    def test_title (self):
        self.rdr.add_title (
            "A Name is a name is a name is a name", role=Base.EDITOR_ROLE)
        self.assertEqual(
            self.rdr.entry['title'], "A Name is a name is a name is a name")
        
#----------------------------------------------------------------------


class PersonTestCase(unittest.TestCase):

    
    data = [
        ['Rind', 'B', 'Rind, B.'],
        ['GOBRY', 'F', 'Gobry, F.'],
        ['Hoffmann', 'ETA', 'Hoffmann, E. T. A.'],
        ['SCHULTE-STRACKE', 'PME', 'Schulte-Stracke, P. M. E.']]

    
    def setUp (self):
        self.rdr = Import.Reader()
       

    def check_name(self, i, j, k):
        self.rdr.entry =  Base.create('O')
        self.rdr.add_person(i, initials=j)
        print i, "/",  j, "/",  k, "/",  self.rdr.entry['author']
        assert self.rdr.entry.dict['author'] == k, "malformed author name"

    def test_names (self):
        for i in self.data:
            j, k, l = i
            self.check_name( j, k, l)

    def test_roles (self):
        self.rdr.entry =  Base.create('O')
        self.rdr.add_person (
            "A Name is a name is a name is a name", role=Base.EDITOR_ROLE)
        self.assertEqual(
            self.rdr.entry['editor'], "A Name is a name is a name is a name")
        self.rdr.add_person (
            "A Name is a name is a name is a name", role=999999)
        self.assertEqual(
            self.rdr.entry['note'],
            "Other person: A Name is a name is a name is a name(999999)")

#----------------------------------------------------------------------


#----------------------------------------------------------------------

def suite():
    theSuite = unittest.TestSuite()

    theSuite.addTest(unittest.makeSuite(PersonTestCase))

    return theSuite


if __name__ == '__main__':
    unittest.main( defaultTest='suite' )

