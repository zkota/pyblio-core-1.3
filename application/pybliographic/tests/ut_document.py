import os, pybut, sys, string

from PyblioUI.Logic import Document

class TestDocument (pybut.TestCase):
    """ Test the Logic.Document module """

    def testOpen (self):
        """ Open an existing database """

        for format, name in (('file', 'ut_document/sample.xml'),):
            db = Document.open (name, format)

            assert len (db) == 1
            
        return


document = pybut.makeSuite (TestDocument, 'test')

pybut.run (pybut.TestSuite ((document,)))
