#! /usr/bin/python  

"""Unit test for Isi"""

import sys, pybut

from Pyblio.Import import Isi
from Pyblio import stubs

verbose = 1


#----------------------------------------------------------------------

class SimpleTestCase(pybut.TestCase):

    data = """PT Journal
AU Hetzel, P
TI The low-frequency transmitter DCF77 at 77.5 kHz: On 40 years of
   times signals and standard frequencies, 25 years of coded time
   information
SO PTB-MITTEILUNGEN
LA German
DT Article
NR 14
SN 0030-834X
PU VIEWEG
C1 Phys Tech Bundesanstalt, Lab Zeit & Frequenzubertragung,
   Bundesallee 100, D-38116 Braunschweig, Germany
   Phys Tech Bundesanstalt, Lab Zeit & Frequenzubertragung, D-38116 Braunschweig, Germany
AB The development of the time signal and standard frequency
   emissions through the LF-transmitter DCF77 since the first test
   emissions in the mid-fifties is described. Information is given
   about the agreements between the Physikalisch-Technische
   Bundesanstalt (PTB) and the Deutsche Telekom AG (DTAG) which
   were made after the privatization of the Deutsche Bundespost
   Telekom and govern the dissemination of time through DCF77 for
   the time being until the end of the year 2006.
CR *SEND DCF77, 1967, NACHRICHTENTECHNISCH, V20, P346
   BECKER G, 1981, PTB-MITT, V91, P183
   BECKER G, 1977, PTB-MITT, V87, P110
   BECKER G, 1973, PTB-MITT, V83, P163
   BECKER G, 1971, PTB-MITT, V81, P199
   ENSLIN H, 1988, ALTE UHREN MODERNE Z, P60
   HETZEL P, 1974, FUNKSCHAU, V46, P727
   HETZEL P, 1993, FUNKUHREN ZEITSIGNAL, P55
   HETZEL P, 1993, TELEKOM PRAXIS, V70, P25
   HILBERG W, 1983, FUNKUHREN
   HILBERG W, 1993, FUNKUHREN ZEITSIGNAL
   HILBERG W, 1988, FUNKUHRTECHNIK
   SUSS R, 1965, NACHRICHTENTECHNISCH, V18, P519
   SUSS R, 1964, Z INSTRUMENTENKD, V72, P225
TC 0
BP 11
EP 18
PG 8
JI PTB-Mitt.
PY 1999
PD FEB
VL 109
IS 1
GA 179ZV
PI WIESBADEN
RP Hetzel P
   Phys Tech Bundesanstalt, Lab Zeit & Frequenzubertragung, Bundesallee 100, D-38116 Braunschweig, Germany
J9 PTB-MITT
PA ABRAHAM-LINCOLN-STRABE 46, POSTFACH 15 47, D-65005 WIESBADEN,
   GERMANY
UT ISI:000079361000002
ER
"""

    def setUp (self):
        self.reader = Isi.Reader(data=self.data)
        self.x = self.reader.next()

    def test_someFields (self):
        self.assertEqual(self.x.dict['journal'], 'PTB-Mitteilungen')
        self.assertEqual(self.x.dict['publisher'], 'VIEWEG')
        pass
#----------------------------------------------------------------------

class AuthorTestCase(pybut.TestCase):
    
    def check (self, i, k):
        self.reader = Isi.Reader(data=i)
        x = self.reader.next ()
        self.assertEqual(x['author'], k)
        
    def test01_simple(self):
        data = [
            ['Rind, B', 'Rind, B.'],
            ['GOBRY, F', 'Gobry, F.'],
            ['Hoffmann, ETA', 'Hoffmann, E. T. A.'],
            ['SCHULTE-STRACKE, PME', 'Schulte-Stracke, P. M. E.'],
            ['Ghizzoni, L\n   Milani, S', 'Ghizzoni, L. and Milani, S.']]


        for i in data:
            j, k = i
            self.check ('AU %s\nER\n' %(j), k)

class OtherTestCase (pybut.TestCase):
    
    def test02_journal (self):
        data = [
            ['JOURNAL OF PEDIATRIC ENDOCRINOLOGY & METABOLISM',
             'J. Pediatr. Endocrinol. Metab.',
             'J PEDIATR ENDOCRINOL METAB',
             'Journal of Pediatric Endocrinology & Metabolism']]
        for item in data:
            i, j, k, l = item
            inp = "J9 %s\nJI %s\nSO %s\nER\n" %(k, j, i)
            rdr = Isi.Reader(data=inp)
            x = rdr.next()
            self.assertEqual(x['journal'], l)

    def test03_pages (self):
        data = [
            ['BP 99', '99'],
            ['BP 99', 'EP 100', '99-100']]

        
#----------------------------------------------------------------------
class FileTestCase(pybut.TestCase):
    
    
    def test_reading(self):
        fn = '/home/ptr/txt/bib/isi-1.isi'
        self.rs = Isi.Reader(file=fn)
        
        for i in self.rs:
            print i['title']
        
##     def test_xml (self):
##         fn = '/home/ptr/txt/bib/isi-1.isi'
##         rs = Isi.Reader(file=fn)
##         for i in rs:
##             print i.write_xml()
        
##     def test_bibtex (self):
##         fn = '/home/ptr/txt/bib/isi-1.isi'
##         rs = Isi.Reader(file=fn)
##         for i in rs:
##             print i.write_bibtex()
        
    def test_simple (self):
        fn = '/home/ptr/txt/bib/isi-1.isi'
        rs = Isi.Reader(file=fn)
        print '\n\nWRITE SIMPLE\n\n'
        for i in rs:
            print i.write_simple()

#----------------------------------------------------------------------
class LongTestCase(pybut.TestCase):
    
    
    def test_3r (self):
        fn = '/home/ptr/txt/bib/isi-1.isi'
        self.rs = Isi.Reader(file=fn)
        out = file('ut_output.txt', 'a')
        out.write (
            '''\n\n\nLONG TEST CASE: write_long output
---------------------------------\n\n\n''')
        
        for i in self.rs:
            i.write_long(out)

##         aix = self.rs.index('author')
##         for i in aix:
##             i.write_simple(out)
##             for j in i.works:
##                 j.write_simple(out)
##             out.write ("\n\n")

##         bix = self.rs.index ('journal')
##         for i in bix:
##             i.write_simple(out)
##             for j in i.content:
##                 j.write_simple(out)
##             out.write('\n\n')

##         cix = self.rs.index('title')
##         for i in cix:
##             i.write_simple(out)
        
        
         

#----------------------------------------------------------------------

def suite():
    theSuite = pybut.TestSuite()

    theSuite.addTest(pybut.makeSuite(ATestCase))

    return theSuite

def main ():
    pybut.run (pybut.makeSuite (SimpleTestCase, 'test'))
    pybut.run (pybut.makeSuite (AuthorTestCase, 'test'))
    pybut.run (pybut.makeSuite (FileTestCase, 'test'))
    pybut.run (pybut.makeSuite (LongTestCase, 'test'))
    pybut.run (pybut.makeSuite (OtherTestCase, 'test'))
   
if __name__ == '__main__':
    main()

### Local Variables:
### Mode: python
### End:
