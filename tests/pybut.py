""" Common file for Pyblio Unit Tests """


import sys, os, time

import unittest
from unittest import makeSuite, TestSuite, TestCase

# Setup the system so that we import the current python files
srcdir = os.path.abspath(os.environ.get ('srcdir', '.'))
sys.path.insert (0, os.path.join (srcdir, '..'))

assert os.path.isdir (os.path.join (srcdir, '..', 'Pyblio'))

from Pyblio import init_logging

base = os.path.abspath('.')

def fp(*args):
    return os.path.join(*((base,) + args))


def _cleanup ():
    import shutil
    
    for d in os.listdir ('.'):

        if d [:2] != ',,': continue

        if os.path.isdir (d): shutil.rmtree (d)
        else:                 os.unlink (d)

class _WritelnDecorator:
    """Used to decorate file-like objects with a handy 'writeln' method"""
    def __init__(self,stream):
        self.stream = stream

    def __getattr__(self, attr):
        return getattr(self.stream,attr)

    def writeln(self, arg=None):
        if arg: self.write("unittest: %s" % arg)
        self.write('\n') # text-mode streams translate to \r\n if needed

class _TextTestResult(unittest.TestResult):
    """A test result class that can print formatted text results to a stream.

    Used by TextTestRunner.
    """

    def __init__(self, stream, descriptions, verbosity):
        unittest.TestResult.__init__(self)
        self.stream = stream
        self.showAll = verbosity > 1
        self.dots = verbosity == 1
        self.descriptions = descriptions
        self.stream.write ('unittest: ')

    def getDescription(self, test):
        if self.descriptions:
            return test.shortDescription() or str(test)
        else:
            return str(test)

    def startTest(self, test):
        unittest.TestResult.startTest(self, test)
        if self.showAll:
            self.stream.write(self.getDescription(test))
            self.stream.write(" ... ")
        
    def addSuccess(self, test):
        unittest.TestResult.addSuccess(self, test)
        if self.showAll:
            self.stream.writeln("ok")
        elif self.dots:
            self.stream.write('.')

    def addError(self, test, err):
        unittest.TestResult.addError(self, test, err)
        if self.showAll:
            self.stream.writeln("ERROR")
        elif self.dots:
            self.stream.write('E')

    def addFailure(self, test, err):
        unittest.TestResult.addFailure(self, test, err)
        if self.showAll:
            self.stream.writeln("FAIL")
        elif self.dots:
            self.stream.write('F')

    def printErrors(self):
        if self.dots or self.showAll:
            self.stream.writeln()
        self.printErrorList('ERROR', self.errors)
        self.printErrorList('FAIL', self.failures)

    def printErrorList(self, flavour, errors):
        for test, err in errors:
            self.stream.writeln("%s: %s" % (flavour,self.getDescription(test)))
            self.stream.writeln("%s" % err)


class TextTestRunner:
    """A test runner class that displays results in textual form.

    It prints out the names of tests as they are run, errors as they
    occur, and a summary of the results at the end of the test run.
    """
    def __init__(self, stream=sys.stderr, descriptions=1, verbosity=1):
        self.stream = _WritelnDecorator(stream)
        self.descriptions = descriptions
        self.verbosity = verbosity

    def _makeResult(self):
        return _TextTestResult(self.stream, self.descriptions, self.verbosity)

    def run(self, test):
        "Run the given test case or test suite."
        result = self._makeResult()
        startTime = time.time()
        test(result)
        stopTime = time.time()
        timeTaken = float(stopTime - startTime)
        result.printErrors()
        run = result.testsRun
        self.stream.writeln("[%d test%s in %.3fs]" %
                            (run, run != 1 and "s" or "", timeTaken))
        if not result.wasSuccessful():
            self.stream.writeln ("FAILED")
            failed, errored = map(len, (result.failures, result.errors))
            if failed:
                self.stream.writeln("  - failures: %d" % failed)
            if errored:
                self.stream.writeln("  - errors:   %d" % errored)
        else:
            self.stream.writeln("OK")
        return result


def suite (* args):
    return TestSuite (map (lambda s: makeSuite (s, 'test'), args))


def run (full):
    _cleanup ()
    
    r = TextTestRunner ()
    r.run (full)
    
    return

def fileeq(a, b):
    for f in a, b:
        if not os.path.exists (f):
            assert False, 'cannot diff %s and %s: %s does not exist' % (
                repr (a), repr (b), repr (f))
            
    if open (a).read () == open (b).read (): return

    os.system ("diff '%s' '%s'" % (a, b))
    assert False, '%s and %s differ' % (a, b)

basedir = os.path.dirname(os.path.abspath(__file__))
init_logging(',,pyblio.log')
_count = 0

def src(*name):
    return os.path.join(basedir, *name)

def dbname ():
    global _count
    _count = _count + 1
    return ',,db-%d' % _count

