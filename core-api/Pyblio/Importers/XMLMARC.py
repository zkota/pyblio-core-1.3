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

import string

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

    def record_parse (self, record):

        self.record = Store.Record ()
        self.record_begin ()

        for field in record:

            (maj, ind1, ind2), values = field

            fn = getattr (self, 'do_%d' % maj, self.do_default)

            fn (maj, ind1, ind2, values)
            
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

        else:
            self._error ('unknown tag: %s' % `name`)
            
        return

    def endElement (self, name):
        
        if name == 'record':
            self.record_parse (self._record)
            self._record = None
            return

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
            attribute = db.schema [v]

            self._mapping [k] = (v, self._physical [attribute.type])

        return Importer.parse (self, fd, db)

    def date_add (self, field, value):

        f = self.record.get (field, [])

        # heuristic to match a date
        f.append (Attribute.Date (year = int (value)))
        
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
    


    
