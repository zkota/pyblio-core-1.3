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

    def record_begin (self):

        pass

    def record_end (self):

        pass

    def do_default (self, tag, ind1, ind2, values):

        pass

    def do_control (self, field, value):

        pass

    def record_parse (self, record):

        self.record = Store.Record ()
        self.record_begin ()

        for field in record:

            try:
                (maj, ind1, ind2), values = field
                fn = getattr (self, 'do_%d' % maj, self.do_default)
                fn (maj, ind1, ind2, values)
                
            except TypeError:
                ctrl, value = field
                self.do_control (ctrl, value)
            
        self.record_end ()

        if self.record is not None:
            self.db.add (self.record)
        
        return

    def parse (self, fd, db):

        self.db = db
        
        parser  = sax.make_parser ()
        parser.setFeature (sax.handler.feature_validation, False)
        parser.setContentHandler (self)
        
        parser.parse (fd)
        return


    def startDocument (self):

        self._tdata = None

        self._tag    = None
        self._record = None
        self._fields = None
        self._field  = None
        return


    def startElement (self, name, attrs):

        if name == 'collection':
            pass

        elif name == 'record':
            self._record = []
            return

        elif name == 'datafield':
            if self._record is None:
                self._error ('datafield must be in a record')

            self._tag = (int (self._attr ('tag', attrs)),
                         str (attrs.get ('ind1', '')),
                         str (attrs.get ('ind2', '')))
            self._fields = []
            return

        elif name == 'subfield':
            self._field = str (self._attr ('code', attrs))
            self._tdata = ''

        elif name == 'controlfield':
            if self._record is None:
                self._error ('datafield must be in a record')
            
            self._tag   = int (self._attr ('tag', attrs))
            self._tdata = ''
            
        else:
            self._error ('unknown tag: %s' % `name`)
        return

    def endElement (self, name):

        if name == 'record':
            self.record_parse (self._record)
            self._record = None
            return

        elif name == 'controlfield':
            self._record.append ((self._tag, self._tdata))
            self._tdata = None
            self._tag   = None

        elif name == 'subfield':
            self._fields.append ((self._field, self._tdata))
            self._tdata = None
            self._field = None
            return

        elif name == 'datafield':

            self._record.append ((self._tag, self._fields))
            self._tag    = None
            self._fields = None
            return

        return
        
    def characters (self, data):

        if self._tdata is not None:
            self._tdata = self._tdata + data
            
        return


class SimpleImporter (Importer):

    _date_re = re.compile (r'(.*)(\d{4,})')
    
    def __init__ (self, mapping):

        self._logical  = mapping

        self._physical = {
            Attribute.Text  : self.text_add,
            Attribute.URL   : self.url_add,
            Attribute.Person: self.person_add,
            Attribute.ID    : self.id_add,
            Attribute.Date  : self.date_add,
            }
        return

    def parse (self, fd, db):

        self._mapping = {}

        for k, v in self._logical.items ():

            if v is None:
                self._mapping [k] = (v, self.skip)
                continue

            attribute = db.schema [v]

            self._mapping [k] = (v, self._physical [attribute.type])

        
        return Importer.parse (self, fd, db)

    def skip (self, field, value):

        pass

    def date_add (self, field, value):

        f = self.record.get (field, [])

        # heuristic to match a date
        d = self._date_re.match (value)

        if d is None:
            raise Exceptions.ParserError ('unknown date %s' % `value`)

        year = int (d.group (2))
        
        f.append (Attribute.Date (year = year))
        
        self.record [field] = f
        return

    def id_add (self, field, value):

        f = self.record.get (field, [])
        f.append (Attribute.ID (value))
        
        self.record [field] = f
        return
        
    def text_add (self, field, value):

        f = self.record.get (field, [])
        f.append (Attribute.Text (value))
        
        self.record [field] = f
        return

    def url_add (self, field, value):

        f = self.record.get (field, [])
        f.append (Attribute.URL (value))
        
        self.record [field] = f
        return

    def person_add (self, field, value):
        f = self.record.get (field, [])

        parts = map (string.strip, value.split (','))
        if len (parts) == 1:
            f.append (Attribute.Person (last = parts [0]))
        elif len (parts) == 2:
            f.append (Attribute.Person (last  = parts [0],
                                        first = parts [1]))
        else:
            raise Exceptions.ParserError (_('unsupported author syntax: %s') %
                                          `value`)

        self.record [field] = f
        pass
    

    def do_unknown (self, tag, ind1, ind2, key, value):

        raise Exceptions.ParserError (_('unknown field %s%s%s $%s') % (
            tag, ind1, ind2, key))

    
    def do_default (self, tag, ind1, ind2, values):

        for key, value in values:
            try:
                field, fn = self._mapping [(tag, ind1, ind2, key)]
                fn (field, value)

            except KeyError:
                self.do_unknown (tag, ind1, ind2, key, value)

        return

    def do_control (self, field, value):

        try:
            field, fn = self._mapping [field]
            fn (field, value)

        except KeyError:
            pass

        return

class Exporter (object):

    _re_marc = re.compile ('(\d{3,})(\w)(\w)')
    
    def begin (self):

        self.fd.write (' <record>\n')
        self._fields = {}
        return

    def end (self):

        ks = self._fields.keys ()
        ks.sort ()

        for k in ks:
            data = self._fields [k]
            
            r = self._re_marc.match (k)

            if r is None:
                raise SyntaxError ('invalid MARC code: %s' % `k`)

            tag, ind1, ind2  = r.groups ((1, 2, 3, 4))

            if ind1 == '_': ind1 = ''
            if ind2 == '_': ind2 = ''

            for kval in data:
                self.fd.write ('  <datafield tag="%s" ind1="%s" ind2="%s">\n' % (
                    tag, ind1, ind2))
        
                for sub, value in kval.items ():
                    if not value: continue
            
                    self.fd.write ('   <subfield code="%s">%s</subfield>\n' % (
                        sub, escape (value.encode ('utf-8'))))

                self.fd.write ('  </datafield>\n')

        self.fd.write (' </record>\n')
        return

    def single (self, rec, field):

        return rec.get (field, [None]) [0]
    
    def add (self, code, ** kval):

        for k, v in kval.items ():
            if not v: del kval [k]

        if not kval: return

        data = self._fields.get (code, [])
        data.append (kval)
        
        self._fields [code] = data
        return
    

    def record_parse (self, record):

        pass


    def write (self, fd, rs, db):

        self.fd = fd
        self.db = db
        
        fd.write ('''\
<?xml version="1.0" encoding="UTF-8"?>
<collection>
''')

        for r in rs.itervalues ():
            self.record_parse (r)

        fd.write ('''\
</collection>
''')
        return
    
