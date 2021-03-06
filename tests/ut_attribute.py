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
        
        assert xml == txt, 'unexpected: %s (expecting %s)' % (xml, txt)

        return

    def testPerson (self):
        """ Check the XML output of a person """

        self._check (Attribute.Person (last  = u'Gobry',
                                       first = u'Fr�d�ric'),
                     u'<person first="Fr�d�ric" last="Gobry"/>')
        
        self._check (Attribute.Person (honorific = u'Dr.',
                                       last      = u'Gobry',
                                       first     = u'Fr�d�ric',
                                       lineage   = u'Jr.'),
                     u'<person honorific="Dr." first="Fr�d�ric" '
                     'last="Gobry" lineage="Jr."/>')
        return
        
    def testDate (self):

        txt = u'h�h�\nhuhu'
        self._check (Attribute.Date (year = 2003),
                     u'<date year="2003"/>')
        
        self._check (Attribute.Date (year = 2003,
                                     month = 12),
                     u'<date year="2003" month="12"/>')

        self._check (Attribute.Date (year  = 2003,
                                     month = 12,
                                     day   = 25),
                     u'<date year="2003" month="12" day="25"/>')

        assert Attribute.Date (year = 2000) > None
        assert None < Attribute.Date (year = 2000)
        return

    def testText (self):

        self._check (Attribute.Text (u'h�h�\nhuhu'),
                     u'<text>h�h�\nhuhu</text>')
        return

    def testURL (self):

        self._check (Attribute.URL ('http://pybliographer.org/'),
                     u'<url href="http://pybliographer.org/"/>')
        return

    def testID (self):

        self._check (Attribute.ID (u'87657ejh#{[|�<'),
                     u'<id value="87657ejh#{[|�&lt;"/>')
        return


    def testTxo (self):

        from Pyblio.Schema import TxoItem

        i = TxoItem ()
        i.id = 123
        i.group = 'a'

        self._check (Attribute.Txo (i),
                     u'<txo group="a" id="123"/>')
        return

    
    def testIndex (self):

        idx = Attribute.Text (u"H�H� les Gens, s'il vous pla�t.").index ()

        assert idx == [u'h�h�', 'les', 'gens', 's', 'il', 'vous', u'pla�t'], `idx`

        idx = Attribute.Person (first = u'Jean-Albert',
                                last  = u'D�� Schnock').index ()
        
        assert idx == ['jean', 'albert', u'd��', 'schnock' ]

        idx = Attribute.URL ('http://www.pybliographer.org/faq/toto.html').index ()
        assert idx == ['www', 'pybliographer', 'org', 'faq', 'toto']

        assert Attribute.Date (year = 2003).index () == []
        
        return

    def testSort (self):

        coll = Attribute.Text (u"H�H� les Gens, s'il vous pla�t.").sort ()
        assert coll == u"h�h� les gens, s'il vous pla�t."
        
        coll = Attribute.Person (first = u'Jean-Albert',
                                 last  = u'D�� Schnock').sort ()
        assert coll == u"d�� schnock\0jean-albert"

        for d, c in (((2003, None, None), '20030000'),
                     ((2003, 11,   None), '20031100'),
                     ((2003, 11,   13  ), '20031113')):
            
            coll = Attribute.Date (year = d [0], month = d [1], day = d [2]).sort ()
            assert coll == c

        coll = Attribute.URL ('http://pybliographer.org/FAQ/').sort ()
        assert coll == 'http://pybliographer.org/FAQ/'

        return


suite = pybut.suite (TestAttribute)
if __name__ == '__main__':  pybut.run (suite)
