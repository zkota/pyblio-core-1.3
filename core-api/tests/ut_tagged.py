# -*- coding: latin-1 -*-

import os, pybut, sys, re

from Pyblio.Importers import Tagged, Flat
from Pyblio import Store

class T (Tagged.Tagged):
    
    start_re = re.compile (r'(\w{2,2})\s+(.*)')
    contd_re = re.compile (r'\s{2,2}(\s.*)')
    split_re = re.compile (r'^\s*$')

class F (Flat.Flat):

    Reader = T


class TestTagged (pybut.TestCase):

    def setUp (self):

        from Pyblio.Schema import Schema

        pybut.cleanup ()
        
        s = Schema ('ut_tagged/schema.xml')
        self.db = Store.get ('file').dbcreate (pybut.dbname (), s)
        
        return
    

    def testSimpleTagged (self):

        data = open ('ut_tagged/simple.isi')

        
        expected = [[(1, 'PT', 'Journal'),
                     (2, 'AU', 'Hetzel, P'),
                     (3, 'TI', 'The low-frequency transmitter DCF77 at 77.5 kHz: '
                      'On 40 years of times signals and standard frequencies, '
                      '25 years of coded time information')]]

        obtained = []

        t = T (data)
        
        while 1:
            d = t.next ()
            if d is None: break

            obtained.append (d)

        assert obtained == expected, 'obtained %s' % `obtained`

        return


    def testSimpleFlat (self):

        data = open ('ut_tagged/simple.isi')

        f = F ()

        f.parse (data, self.db)

        for e in self.db.entries:

            print str (e)
            
        
pybut.run (pybut.makeSuite (TestTagged, 'test'))
    
