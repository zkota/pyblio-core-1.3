import os, pybut, sys, string

from PyblioUI import Document

class TestDocument (pybut.TestCase):

    """ Test the Logic.Document module """

    def tearDown (self):

        for l in os.listdir ('.'):
            if l [:2] == ',,':
                os.unlink (l)
        return
    
        
    def testGuess (self):

        for name, format in (('gronf/toto.pbl', 'file'),):
            assert Document.format_guess (name) == format

        return

    def testOpen (self):
        """ Open an existing database """

        for format, name in (('file', 'ut_document/sample.pbl'),
                             (None,   'ut_document/sample.pbl')):
            d = Document.Document (name, format)
            
            assert len (d) == 1
            
        return

    
document = pybut.makeSuite (TestDocument, 'test')

pybut.run (pybut.TestSuite ((document,)))
