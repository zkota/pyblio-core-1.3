#! /usr/bin/python

"""Unit test for Base"""

import os, sys, unittest
# Setup the system so that we import the current python files
srcdir = os.environ.get ('srcdir', '.')
sys.path.insert (0, os.path.join (srcdir, '..'))

assert os.path.isdir (os.path.join (srcdir, '..', 'Pyblio'))

from Pyblio import Base, stubs

verbose = 1


#----------------------------------------------------------------------

class RecordTestCase(unittest.TestCase):

    def test_create(self):
        r = Base.create('O')
        self.assertEqual(r.Typ, 'O')

    def test_dict (self):
        r = Base.create('O')
        self.assertEqual(r.dict, {})
        r['fieldname'] = 'string'
        self.assertEqual(r['fieldname'], 'string')
        self.assertEqual(r.dict.get('wrongfield', None), None)


#----------------------------------------------------------------------

class RecordSetTestCase(unittest.TestCase):
    parameter = 'XXX'
    
    def setUp (self):
        self.db = stubs.Database()
        self.rs = Base.RecordSet(base=self.db)

    def test_create(self):
        self.assertEqual(len(self.rs), 0)

    def test_add(self):
        r = Base.create('O')
        self.assertEqual(r.Typ, 'O')
        new_item = Base.create('O')
        self.rs.add(new_item)
        self.assertEqual (len(self.rs), 1)

    def test_delete(self):
        new_item = Base.create('O')
        self.rs.add(new_item)
        self.assertEqual (len(self.rs), 1)
        self.rs.remove(new_item)
        self.assertEqual (len(self.rs), 0)
        
    def test_extend (self):
        rs1 = Base.RecordSet(base=self.db)
        new_item = Base.create('O')
        self.rs.add(new_item)
        new_item = Base.create('O')
        rs1.add(new_item)
        print `rs1`
        self.rs.extend(rs1)
        self.assertEqual(len(self.rs), 2)
        self.assert_(new_item in self.rs)
        self.assert_(new_item in rs1)



#----------------------------------------------------------------------





#----------------------------------------------------------------------

def main ():
    
    unittest.main()
   

if __name__ == '__main__':
    main()

