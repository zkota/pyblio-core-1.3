import pybut

from PyblioUI import Undo

class TestUndo(pybut.TestCase):

    def setUp(self):
        self.document = []
        self.undo = Undo.Undoable()
        return

    def action(self):
        self.document.append('hi')
        return

    def unaction(self):
        self.document.pop()
        return

    def testNoActionNoUndo(self):

        self.failIf(self.undo.canUndo())
        self.failIf(self.undo.canRedo())
        return
    
    def testAction(self):
        """ adding an action actually performs the action """

        self.undo.doAction(self.action, self.unaction)

        self.failUnlessEqual(self.document, ['hi'])
        return

    def testUndo(self):

        self.undo.doAction(self.action, self.unaction)

        self.failUnless(self.undo.canUndo())
        self.failIf(self.undo.canRedo())
        
        self.undo.undoAction()

        self.failUnlessEqual(self.document, [])
        return
        
    def testRedo(self):

        self.undo.doAction(self.action, self.unaction)
        self.undo.undoAction()

        self.failUnless(self.undo.canRedo())
        self.undo.redoAction()

        self.failUnlessEqual(self.document, ['hi'])
        return

    def testNoRedoAfterAction(self):

        self.undo.doAction(self.action, self.unaction)
        self.undo.doAction(self.action, self.unaction)

        self.undo.undoAction()
        self.undo.doAction(self.action, self.unaction)

        self.failIf(self.undo.canRedo())
        return

    def testSavePoint(self):

        # at the beginning, no modification has been done
        self.failIf(self.undo.isModified())

        # first modif:
        self.undo.doAction(self.action, self.unaction)
        self.failUnless(self.undo.isModified())

        # we can undo it, and we have no modif again
        self.undo.undoAction()
        self.failIf(self.undo.isModified())
        
        # we can redo it, and we have a modif
        self.undo.redoAction()
        self.failUnless(self.undo.isModified())

        # Then we save: no more modif
        self.undo.savePoint()
        self.failIf(self.undo.isModified())
        
        # The next undo is a modif
        self.undo.undoAction()
        self.failUnless(self.undo.isModified())

        # But if we redo, there is no more modif
        self.undo.redoAction()
        self.failIf(self.undo.isModified())

        # If we undo and do another action, there is a definitive
        # modif (till the next savePoint)
        self.undo.undoAction()
        self.undo.doAction(self.action, self.unaction)
        self.failUnless(self.undo.isModified())

        return

    def testDynaUndo(self):

        def do():
            self.document.append('gronf')
            def undo():
                self.document.remove('gronf')

            return undo

        self.undo.doAction(do, None)
        self.undo.undoAction()

        self.failUnlessEqual(self.document, [])
        return
    
        
suite = pybut.suite (TestUndo)

if __name__ == '__main__':  pybut.run (suite)
