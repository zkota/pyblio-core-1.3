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

from xml.sax.saxutils import escape, quoteattr

from Pyblio import Attribute, Store, Exceptions, Tools

from gettext import gettext as _

import cElementTree as ElementTree

class Importer (object):

    def record_begin (self):

        pass

    def record_end (self):

        pass

    def do_default (self, tag, ind1, ind2, values):

        pass

    def do_control (self, field, value):

        pass

    def parse (self, fd, db):

        self.db = db

        # We support both the NS-aware and non-NS aware versions of the MARC file
        subs = {
            'record': ('controlfield', 'datafield', 'subfield'),

            '{http://www.loc.gov/MARC21/slim}record': (
                                    '{http://www.loc.gov/MARC21/slim}controlfield',
                                    '{http://www.loc.gov/MARC21/slim}datafield',
                                    '{http://www.loc.gov/MARC21/slim}subfield'
                                )
            }
        
        for event, elem in ElementTree.iterparse (fd, events = ('end',)):
            try: controlfield, datafield, subfield = subs [elem.tag]
            except KeyError: continue
            
            self.record = Store.Record ()
            self.record_begin ()

            # get all the control fields first, then the datafields
            # (as the controlfields can have an impact on the
            # datafields)
            for ctr in elem.findall (controlfield):
                self.do_control (int (ctr.attrib ['tag']), ctr.text)

            for data in elem.findall (datafield):
                attrs = data.attrib
                tag, ind1, ind2 = int (attrs ['tag']), attrs ['ind1'], attrs ['ind2']

                values = [ (x.attrib ['code'], x.text or '') for x in data.findall (subfield) ]

                fn = getattr (self, 'do_%d' % tag, self.do_default)
                fn (tag, ind1, ind2, values)

            self.record_end ()

            if self.record is not None:
                self.db.add (self.record)
            
            elem.clear()
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
    
