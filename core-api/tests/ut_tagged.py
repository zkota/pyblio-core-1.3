# -*- coding: latin-1 -*-

import os, pybut, sys, re
import StringIO

from Pyblio.Importers import Tagged, Flat
from Pyblio import Store

class TestTagged (pybut.TestCase):

    """ Check that the state machine of the Tagged parser behaves as
    advertised """

    def setUp (self):

        import StringIO

        self.fd = StringIO.StringIO ()
        self.t  = Tagged.Parser (self.fd)
        
        return

    def parsingFails (self):

        try:
            while 1:
                d = self.t.next ()
                if d is None: break

            assert False
            
        except SyntaxError:
            pass
        
        return

    def parsingOk (self):

        ret = []
        
        while 1:
            d = self.t.next ()
            if d is None: break
            
            ret.append (d)
                
        return ret

    def testNoNestedRecord (self):

        """ Reject nested records """
        
        self.t.record_start ()
        self.t.record_start ()

        self.parsingFails ()
        return

    def testNoRecordEnd (self):

        """ Reject non-closed records """

        self.t.record_start ()

        self.parsingFails ()
        return

    def testEmptyRecord (self):

        self.t.record_start ()
        self.t.record_end ()

        r = self.parsingOk ()
        assert r == [[]], 'obtained %s' % `r`
        return

    def testNoEmptyField (self):

        self.t.record_start ()
        self.t.field_start ('ST', 1)
        self.t.record_end ()

        self.parsingFails ()
        return

    def testNoEmptyFieldWithData (self):

        self.t.record_start ()
        self.t.field_start ('ST', 1)
        self.t.field_data ('data')
        self.t.record_end ()

        self.parsingFails ()
        return

    def testNoNestedFields (self):

        self.t.record_start ()
        self.t.field_start ('ST', 1)
        self.t.field_start ('ST', 1)
        self.t.field_end ()
        self.t.field_end ()
        self.t.record_end ()

        self.parsingFails ()
        return

    def testSingleField (self):

        self.t.record_start ()
        self.t.field_start ('ST', 1)
        self.t.field_data ('data')
        self.t.field_end ()
        self.t.record_end ()

        r = self.parsingOk ()
        assert r == [[(1, 'ST', u'data')]], 'obtained %s' % `r`
        return

    def testSingleField (self):

        self.t.record_start ()
        self.t.field_start ('ST', 1)
        self.t.field_data ('data')
        self.t.field_end ()
        self.t.record_end ()

        r = self.parsingOk ()
        assert r == [[(1, 'ST', u'data')]], 'obtained %s' % `r`
        return

    def testMultipleFields (self):

        self.t.record_start ()
        self.t.field_start ('ST', 1)
        self.t.field_data ('data')
        self.t.field_end ()
        self.t.field_start ('UV', 2)
        self.t.field_data ('doto')
        self.t.field_end ()
        self.t.record_end ()

        r = self.parsingOk ()
        assert r == [[(1, 'ST', u'data'),
                      (2, 'UV', u'doto')]], 'obtained %s' % `r`
        return

    def testMultipleRecords (self):

        self.t.record_start ()
        self.t.field_start ('ST', 1)
        self.t.field_data ('data')
        self.t.field_end ()
        self.t.field_start ('UV', 2)
        self.t.field_data ('doto')
        self.t.field_end ()
        self.t.record_end ()

        self.t.record_start ()
        self.t.field_start ('WX', 3)
        self.t.field_data ('dutu')
        self.t.field_end ()
        self.t.field_start ('YZ', 4)
        self.t.field_data ('diti')
        self.t.field_end ()
        self.t.record_end ()

        r = self.parsingOk ()
        assert r == [[(1, 'ST', u'data'),
                      (2, 'UV', u'doto')],
                     
                     [(3, 'WX', u'dutu'),
                      (4, 'YZ', u'diti')]], 'obtained %s' % `r`
        return


from Pyblio.Importers import RIS

class TestRISTransport (pybut.TestCase):

    """ Test that the RIS parser works according to the spec """

    def parsingOk (self, txt):

        fd = StringIO.StringIO (txt)
        rt = []

        ris = RIS.RISParser (fd)
        
        while 1:
            d = ris.next ()
            if d is None: break

            rt.append (d)

        return rt

    def testEmptyIsValid (self):

        r = self.parsingOk ('\n\n')
        assert r == [], 'obtained %s' % `r`

    def testSingleRecord (self):

        r = self.parsingOk ('''
TY  - TYPE\r
A1  - Gobry, Frederic\r
ER  - \r
''')

        assert r == [[(2, 'TY', u'TYPE'),
                      (3, 'A1', u'Gobry, Frederic')]], \
                      'obtained %s' % `r`
        return

    def testMultiRecord (self):

        r = self.parsingOk ('''
TY  - TYPE\r
A1  - Gobry, Frederic\r
ER  - \r
TY  - TYPE\r
A1  - Gobry 2, Frederic\r
ER  - \r
''')

        assert r == [[(2, 'TY', u'TYPE'),
                      (3, 'A1', u'Gobry, Frederic')],
                     [(5, 'TY', u'TYPE'),
                      (6, 'A1', u'Gobry 2, Frederic')]], \
                      'obtained %s' % `r`
        return

    def testMultiLines (self):

        r = self.parsingOk ('''
TY  - TYPE\r
A1  - Gobry,\r
      Frederic\r
ER  - \r

TY  - TYPE\r
A1  - Gobry 2,\r
      Frederic\r
ER  - \r
''')
        
        assert r == [[(2, 'TY', u'TYPE'),
                      (3, 'A1', u'Gobry, Frederic')],
                     [(7, 'TY', u'TYPE'),
                      (8, 'A1', u'Gobry 2, Frederic')]], \
                      'obtained %s' % `r`
        return




pybut.run (pybut.makeSuite (TestTagged, 'test'),
           pybut.makeSuite (TestRISTransport, 'test'))
    
