# -*- coding: latin-1 -*-

import os, pybut, sys
import StringIO

from Pyblio import Attribute

class TestAttribute (pybut.TestCase):

    """ Perform tests on the Pyblio.Attribute module """
    
    def _check (self, o, txt):

        xml = StringIO.StringIO ()
        o.xmlwrite (xml)

        xml = xml.getvalue ()
        txt = txt.encode ('utf-8')
        
        assert xml == txt, 'unexpected: %s' % txt

        return

    def testPerson (self):
        """ Check the XML output of a person """

        self._check (Attribute.Person (last  = u'Gobry',
                                       first = u'Frédéric'),
                     u'<person first="Frédéric" last="Gobry"/>')
        
        self._check (Attribute.Person (honorific = u'Dr.',
                                       last      = u'Gobry',
                                       first     = u'Frédéric',
                                       lineage   = u'Jr.'),
                     u'<person honorific="Dr." first="Frédéric" '
                     'last="Gobry" lineage="Jr."/>')
        return
        
    def testDate (self):

        txt = u'héhé\nhuhu'
        self._check (Attribute.Date (year = 2003),
                     u'<date year="2003"/>')
        
        self._check (Attribute.Date (year = 2003,
                                     month = 12),
                     u'<date year="2003" month="12"/>')

        self._check (Attribute.Date (year  = 2003,
                                     month = 12,
                                     day   = 25),
                     u'<date year="2003" month="12" day="25"/>')
        return

    def testText (self):

        self._check (Attribute.Text (u'héhé\nhuhu'),
                     u'<text>héhé\nhuhu</text>')
        return

    def testURL (self):

        self._check (Attribute.URL ('http://pybliographer.org'),
                     u'<url href="http://pybliographer.org"/>')
        return

    def testReference (self):

        from Pyblio.Store import Key
        
        self._check (Attribute.Reference (Key ('toto')),
                     u'<reference ref="toto"/>')
        return


    
pybut.run (pybut.makeSuite (TestAttribute, 'test'))
