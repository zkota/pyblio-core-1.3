""" Common file for Pyblio Unit Tests """


import sys, os

import unittest
from unittest import makeSuite, TestCase

# Setup the system so that we import the current python files
srcdir = os.environ.get ('srcdir', '.')
sys.path.insert (0, os.path.join (srcdir, '..'))

assert os.path.isdir (os.path.join (srcdir, '..', 'Pyblio'))


def run (* args):
    full = unittest.TestSuite (args)

    r = unittest.TextTestRunner ()
    return r.run (full)
