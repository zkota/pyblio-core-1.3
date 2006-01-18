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

        for name, format in (('gronf/toto.bip', 'file'),):
            assert Document.format_guess (name) == format

        return

    def testOpen (self):
        """ Open an existing database """

        for format, name in (('file', 'ut_document/sample.bip'),
                             (None,   'ut_document/sample.bip')):
            d = Document.Document (name, format)
            
            assert len (d.db.entries) == 1
            
        return

suite = pybut.suite (TestDocument)

if __name__ == '__main__':  pybut.run (suite)
