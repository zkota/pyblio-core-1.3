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

        self._check (Attribute.URL ('http://pybliographer.org/'),
                     u'<url href="http://pybliographer.org/"/>')
        return

    def testReference (self):

        from Pyblio.Store import Key
        
        self._check (Attribute.Reference (Key (123)),
                     u'<reference ref="123"/>')
        return

    def testID (self):

        self._check (Attribute.ID (u'87657ejh#{[|é<'),
                     u'<id value="87657ejh#{[|é&lt;"/>')
        return


    def testEnum (self):

        from Pyblio.Store import EnumItem

        i = EnumItem (123, 'group')
        
        self._check (Attribute.Enumerated (i),
                     u'<enumerated id="123"/>')
        return

    
    def testIndex (self):

        idx = Attribute.Text (u"HÉHÉ les Gens, s'il vous plaît.").index ()

        assert idx == [u'héhé', 'les', 'gens', 's', 'il', 'vous', u'plaît'], `idx`

        idx = Attribute.Person (first = u'Jean-Albert',
                                last  = u'Dââ Schnock').index ()
        
        assert idx == ['jean-albert', u'dââ', 'schnock' ]

        idx = Attribute.URL ('http://www.pybliographer.org/faq/').index ()
        assert idx == ['http', 'www', 'pybliographer', 'org', 'faq']

        assert Attribute.Date (year = 2003).index () == []
        
        from Pyblio.Store import Key
        
        assert Attribute.Reference (Key (314)).index () == []
        return

    def testSort (self):

        coll = Attribute.Text (u"HÉHÉ les Gens, s'il vous plaît.").sort ()
        assert coll == u"héhé les gens, s'il vous plaît."
        
        coll = Attribute.Person (first = u'Jean-Albert',
                                 last  = u'Dââ Schnock').sort ()
        assert coll == u"dââ schnock\0jean-albert"

        for d, c in (((2003, None, None), '20030000'),
                     ((2003, 11,   None), '20031100'),
                     ((2003, 11,   13  ), '20031113')):
            
            coll = Attribute.Date (year = d [0], month = d [1], day = d [2]).sort ()
            assert coll == c

        coll = Attribute.URL ('http://pybliographer.org/FAQ/').sort ()
        assert coll == 'http://pybliographer.org/FAQ/'

        from Pyblio.Store import Key
        
        coll = Attribute.Reference (Key (456)).sort ()
        assert coll == '456'
        return


pybut.run (pybut.makeSuite (TestAttribute, 'test'))
