# This file is part of pybliographer
# 
# Copyright (C) 1998-2006 Frederic GOBRY
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

import string, re, StringIO, sys, logging

from xml import sax
from xml.sax.saxutils import escape, quoteattr

from Pyblio import Attribute, Store, Exceptions, Tools

import cElementTree as ElementTree

from gettext import gettext as _

# Unofficial mapping from EndNote type codes to type names
typemap = [
    (0  , "Journal Article"),
    (1  , "Book"),
    (2  , "Thesis"),
    (3  , "Conference Proceedings"),
    (4  , "Personal Communication"),
    (5  , "Newspaper Article"),
    (6  , "Computer Program"),
    (7  , "Book Section"),
    (8  , "Magazine Article"),
    (9  , "Edited Book"),
    (10 , "Report"),
    (11 , "Map"),
    (12 , "Audiovisual Material"),
    (13 , "Artwork"),
    (15 , "Patent"),
    (16 , "Electronic Source"),
    (17 , "Bill"),
    (18 , "Case"),
    (19 , "Hearing"),
    (20 , "Manuscript"),
    (21 , "Film or Broadcast"),
    (22 , "Statute"),
    (25 , "Figure"),
    (26 , "Chart or Table"),
    (27 , "Equation"),
    (31 , "Generic"),
]

        
class Reader(object):

    # The official channel in which messages must be sent
    log = logging.getLogger('pyblio.import.xmlendnote')
    
    id2type = dict (typemap)

    def clean_tag (self, tag):
        #dash cannot be called. convert to underscore.
        #and assume case doesn't matter
        return tag.lower ().replace ('-','_')

    def process_children (self, elem):
        for cont in elem.getchildren ():
            tag = self.clean_tag (cont.tag)
            getattr (self, 'do_' + tag, self.do_default) (cont)
        
    def style_genocide (self, elem):
        for ch in list (elem):
            if ch.tag == "style":                
                if elem.text == None: elem.text = ""
                elem.text += ch.text
            else:
                ch = self.style_genocide (ch)
        return elem
        
    def record_begin (self):
        pass

    def record_end (self):
        pass

    def do_default (self, elem):
        pass

    def add (self, field, value):
        """
        Use this function to add anything to your record. It's auto-typeing, even
        for Txo's.
        """
        t = self.db.schema[field].type
        
        if t == Attribute.Txo:
            value = self.db.txo [field].byname (value)

        self.record.add (field, value, t)
        
    def id_add (self, field, value):
        """
        Deprecated: use L{add} instead.
        """
        self.record.add (field, value, Attribute.ID)
        
    def text_add (self, field, value):
        """
        Deprecated: use L{add} instead.
        """
        self.record.add (field, value.text, Attribute.Text)

    def url_add (self, field, value):
        """
        Deprecated: use L{add} instead.
        """        
        self.record.add (field, value, Attribute.URL)

    def person_add (self, field, value):
        f = self.record.get (field, [])
        

        def mkauthor (txt):
            parts = map (string.strip, txt.text.split (','))
            if len (parts) == 2:
                return Attribute.Person (last  = parts [0],
                                         first = parts [1])
            else:
                return Attribute.Person (last = txt.text.strip ())

        f += [ mkauthor (x) for x in value ]

        self.record [field] = f
        return

    def parse (self, fd, db):
        self.db = db

        rs = db.rs.add(True)
        rs.name = _('Imported from XML EndNote')
        
        for event, elem in ElementTree.iterparse (fd, events = ('end',)):
            if elem.tag != 'RECORD' and elem.tag != 'record': continue

            self.record = Store.Record ()
            self.record_begin ()            
            
            for field in elem:
                tag = self.clean_tag (field.tag)
                elem = self.style_genocide (field)
                getattr (self, 'do_' + tag, self.do_default) (field)

            self.record_end ()

            if self.record is not None:
                k = self.db.add (self.record)
                rs.add(k)
                
            elem.clear()
        
        return rs

 
class Writer(object):

    # The official channel in which messages must be sent
    log = logging.getLogger('pyblio.export.xmlendnote')
    

    type2id = dict ([ (x [1], x [0]) for x in typemap ])

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
                txt = person.last

            if txt: txts.append ('<%s>%s</%s>' % (
                tag, self._encode (txt), tag))

        if not txts: return
        
        self.fd.write ('<%sS>' % tag)
        for txt in txts: self.fd.write (txt)
        self.fd.write ('</%sS>' % tag)
        
        return

    def header_add (self, key, reftype):
        
        self.fd.write ('<REFERENCE_TYPE>%d</REFERENCE_TYPE>' % reftype)
        self.fd.write ('<REFNUM>%d</REFNUM>' % key)
        return

    
    def record_parse (self, record):
        pass

    
    def write (self, fd, rs, db):

        self.db = db
        
        fd.write ('<XML><RECORDS>')

        for r in rs.itervalues ():

            self.fd = StringIO.StringIO ()

            self.record_parse (r)

            record = self.fd.getvalue ().strip ()
            
            self.fd.close ()

            if not record: continue
            
            fd.write ('<RECORD>%s</RECORD>' % record)
            
        fd.write ('</RECORDS></XML>\n')
        return
    
    

