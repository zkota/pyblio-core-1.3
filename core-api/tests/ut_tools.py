# -*- coding: latin-1 -*-

import os, pybut, sys

from Pyblio import Tools

class TestTools (pybut.TestCase):

    """ Perform tests on the Pyblio.Tools module """
    
    def testIdMake (self):

        """ Check the id generator """

        # No proposal
        k = Tools.id_make (1, None)
        assert k == (2, 1)

        # The proposed id is smaller than the latest
        k = Tools.id_make (2, 1)
        assert k == (2, 1)

        # The proposed id is larget than the latest
        k = Tools.id_make (2, 4)
        assert k == (5, 4)

        return
    

pybut.run (pybut.makeSuite (TestTools, 'test'))
