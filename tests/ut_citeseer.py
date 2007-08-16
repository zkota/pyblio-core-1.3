# -*- coding: utf-8 -*-

import pybut, sys, os, logging
from twisted.trial import unittest

from Pyblio.External import Citeseer

base = os.path.abspath('ut_citeseer')

class TestScraping(unittest.TestCase):
    def testScrape(self):
        scrape = Citeseer.ResultScraper(
            open(os.path.join(base, 'result.html')).read())
        self.failUnlessEqual(214, scrape.count())

        links = scrape.links()
        self.failUnlessEqual(
            links[0], 'http://citeseer.ist.psu.edu/fredriksson01faster.html')

    def testNoResults(self):
        scrape = Citeseer.ResultScraper(
            open(os.path.join(base, 'noresult.html')).read())
        self.failUnlessEqual(0, scrape.count())

    def testCitation(self):
        scrape = Citeseer.CitationScraper(
            open(os.path.join(base, 'citation.html')).read())
        citation = scrape.citation()
        self.failUnlessEqual(
            "I'm an abstract with white space !", citation['abstract'])
        bibtex = """@misc{ sample,
  author = "O. Babaoglu and H. Meling and A. Montresor"
}"""
        self.failUnlessEqual(bibtex, citation['bibtex'])
