# This file is part of pybliographer
# 
# Copyright (C) 1998-2004 Frederic GOBRY
# Email : gobry@pybliographer.org
# 	   
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2 
# of the License, or (at your option) any later version.
#   
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details. 
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
# 

import string, re

from xml import sax
from xml.sax.saxutils import escape, quoteattr

from Pyblio import Attribute, Store, Exceptions, Tools, XML

from gettext import gettext as _


class Importer (XML.Parser):

    def parse (self, fd, db):

        self.db = db
        
        parser  = sax.make_parser ()
        parser.setFeature (sax.handler.feature_validation, False)
        parser.setContentHandler (self)
        
        parser.parse (fd)
        return


    def startDocument (self):

        self._tdata = None
        return


    def startElement (self, name, attrs):
        self._error ('unknown tag: %s' % `name`)
            
        return

    def endElement (self, name):
        
        return
        
    def characters (self, data):

        if self._tdata is not None:
            self._tdata = self._tdata + data
            
        return


class Exporter (object):

    id2type = {
        0  : "Journal Article",
        1  : "Book",
        2  : "Thesis",
        3  : "Conference Proceedings",
        4  : "Personal Communication",
        5  : "Newspaper Article",
        6  : "Computer Program",
        7  : "Book Section",
        8  : "Magazine Article",
        9  : "Edited Book",
        10 : "Report",
        11 : "Map",
        12 : "Audiovisual Material",
        13 : "Artwork",
        15 : "Patent",
        16 : "Electronic Source",
        17 : "Bill",
        18 : "Case",
        19 : "Hearing",
        20 : "Manuscript",
        21 : "Film or Broadcast",
        22 : "Statute",
        25 : "Figure",
        26 : "Chart or Table",
        27 : "Equation",
        31 : "Generic",
        }

    type2id = {}

    for k, v in id2type.items (): type2id [v] = k

    _charref = re.compile (r'.*&#(\d+);')
    
    def _encode (self, txt):
        
        txt = escape (txt).encode ('ascii', 'xmlcharrefreplace')

        while 1:
            d = self._charref.match (txt)
            if d is None: break

            s, e = d.start (1), d.end (1)

            v = int (d.group (1))
            
            txt = txt [:s] + 'x%X' % v + txt [e:]
            
        return txt.replace ('\n', '&#xD;')

    def text_add (self, text, tag):

        text = self._encode ('\n'.join (text))
        if not text: return

        self.fd.write ('<%s>%s</%s>' % (tag, text, tag))
        return

    def keywords_add (self, keywords):

        txts = []
        for k in keywords:
            k = self._encode (k)
            if k: txts.append ('<KEYWORD>%s</KEYWORD>' % k)

        if not txts: return

        self.fd.write ('<KEYWORDS>')
        for txt in txts: self.fd.write (txt)
        self.fd.write ('</KEYWORDS>')

        return
    
    def person_add (self, persons, tag = 'AUTHOR'):

        txts = []

        for person in persons:
            if person.first:
                txt = '%s, %s' % (person.last, person.first)
            else:
                txt = self.last

            if txt: txts.append ('<%s>%s</%s>' % (
                tag, self._encode (txt), tag))

        if not txts: return
        
        self.fd.write ('<%sS>' % tag)
        for txt in txts: self.fd.write (txt)
        self.fd.write ('</%sS>' % tag)
        
        return

    def header_add (self, key, reftype):
        
        self.fd.write ('<REFNUM>%d</REFNUM>' % key)
        self.fd.write ('<REFERENCE_TYPE>%d</REFERENCE_TYPE>' % reftype)
        return

    
    def record_parse (self, record):
        pass

    
    def write (self, fd, rs, db):

        self.fd = fd
        
        fd.write ('<XML><RECORDS>')

        for r in rs.itervalues ():

            fd.write ('<RECORD>')

            self.record_parse (r)
            
            fd.write ('</RECORD>')
            
        fd.write ('</RECORDS></XML>\n')
        return
    
    

