# -*- coding: latin-1 -*-

import os, pybut, sys, re

from Pyblio.Importers import Tagged, Flat
from Pyblio import Store

class T (Tagged.Tagged):
    
    start_re = re.compile (r'(\w{2,2})\s+(.*)')
    contd_re = re.compile (r'\s{2,2}(\s.*)')

    def line_handler (self, line, count):

        if line.strip () == '':
            if self.state == self.ST_IN_FIELD:
                self.push (self.EV_FIELD_END)
                self.push (self.EV_RECORD_END)
            return
        
        m = self.start_re.match (line)
        if m:
            if self.state == self.ST_OUTSIDE:
                self.push (self.EV_RECORD_START)
                
            elif self.state == self.ST_IN_FIELD:
                self.push (self.EV_FIELD_END)
                
            self.push (self.EV_FIELD_START, m.group (1), count)
            self.push (self.EV_FIELD_DATA,  m.group (2))
            return
        
        m = self.contd_re.match (line)
        if m:
            self.push (self.EV_FIELD_DATA, m.group (1))
            return

        raise SyntaxError (_('line %d: unexpected data') % count)


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
    
