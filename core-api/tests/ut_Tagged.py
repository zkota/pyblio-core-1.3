#! /usr/bin/python

"""Unit test for Tagged"""



import pygtk
pygtk.require('2.0')

import gtk, pango


import sys, unittest

sys.path.append('../')
sys.path.append('../compiled')

#from testlib import  Record, get_entry, Key
import Tagged

verbose = 1


#----------------------------------------------------------------------

class ATestCase(unittest.TestCase):
    parameter = 'XXX'
    
    def setUp (self):
        pass
#----------------------------------------------------------------------




#----------------------------------------------------------------------

def suite():
    theSuite = unittest.TestSuite()

    theSuite.addTest(unittest.makeSuite(ATestCase))

    return theSuite


if __name__ == '__main__':
    unittest.main( defaultTest='suite' )

