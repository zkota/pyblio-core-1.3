import os, logging, pybut

from twisted.trial import unittest
from twisted.internet import reactor

from Pyblio.External.PubMed import PubMed
from Pyblio import Store, Attribute, Registry, init_logging

# To activate more debugging:
#
#init_logging()
#log = logging.getLogger('pyblio')
#log.setLevel(logging.DEBUG)


base = os.path.abspath('ut_pubmed')

from twisted.web import http

class MyPubMed(http.Request):

    def process(self):
        if self.path.startswith('/broken'):
            # return an error code
            err = os.path.join(base, 'error.xml')
            self.write(open(err).read())

        elif self.path.startswith('/count'):
            f = os.path.join(base, 'count.xml')
            self.write(open(f).read())
            
        elif self.path.startswith('/search/esearch.fcgi'):
            f = os.path.join(base, 'search-count.xml')
            self.write(open(f).read())
            
        elif self.path.startswith('/search/efetch.fcgi'):
            start = self.args.get('retstart', ['0'])[0]
            
            f = os.path.join(base, 'search-%s.xml' % start)
            self.write(open(f).read())
            
        self.setResponseCode(http.OK)
        self.finish()
        return
    
class MyChannel(http.HTTPChannel):
    requestFactory = MyPubMed

class Server(http.HTTPFactory):
    protocol = MyChannel


class TestPubMed(unittest.TestCase):

    def setUp(self):
        Registry.parse_default()

        s = Registry.getSchema('org.pybliographer/pubmed/0.1')
        fmt = Store.get('memory')

        self.db = fmt.dbcreate(None, s)

        self.cnx = PubMed(self.db)
        self.port = reactor.listenTCP(8000, Server())

    def tearDown(self):
        self.port.stopListening()
        Registry.reset()
        return

    def testCount(self):
        """ Test that one can get a result count """
        self.cnx.baseURL = 'http://localhost:8000/count'

        d = self.cnx.count('gobry')

        def check(count):
            self.failUnlessEqual(count, 7)
            
        return d.addCallback(check)
    
    def testSearch(self):
        """ Test a simple search. """
        
        self.cnx.baseURL = 'http://localhost:8000/search'
        self.cnx.BATCH_SIZE = 5
        
        d, rs = self.cnx.search('gobry')

        def check(count):
            self.failUnlessEqual(len(rs), 7)
            
        return d.addCallback(check)
    
    def testFailure(self):
        """ Check that error codes are properly detected."""
        
        self.cnx.baseURL = 'http://localhost:8000/broken'
        d = self.cnx.count(query='TOTO')

        def check(e):
            if e.check(unittest.FailTest):
                return e
            
        return d.addCallback(self.fail).addErrback(check)

from Pyblio.Parsers.Semantic.PubMed import Reader
from cElementTree import ElementTree

class TestPubMedParser(unittest.TestCase):

    def setUp(self):
        Registry.parse_default()

        s = Registry.getSchema('org.pybliographer/pubmed/0.1')
        fmt = Store.get('memory')

        self.db = fmt.dbcreate(None, s)

    def testParsing(self):

        src = os.path.join(base, 'search-0.xml')

        r = Reader()
        r.parse(ElementTree(file=open(src)), self.db)

        tmp = pybut.dbname()
        fd = open(tmp, 'w')
        self.db.xmlwrite(fd)
        fd.close()

        pybut.fileeq(tmp, pybut.fp('ut_pubmed', 'result.bip'))
            
        
