# This file is part of pybliographer
# 
# Copyright (C) 1998-2003 Frederic GOBRY
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

""" Schema definition for a pyblio database. When a database is
created, the schema is instantiated from a template. The user can then
customize it.

At the moment, a schema contains a dictionnary of known document
types. For each document, it is possible to know the mandatory and
optional fields that describe the document. These fields are typed.

"""

from gettext import gettext as _

from xml import sax
from xml.sax.saxutils import escape

from Pyblio.Attribute import N_to_C, C_to_N
from Pyblio import I18n

class Schema (dict):

    def __init__ (self, file = None):

        if file:
            handler = SchemaParse (self)

            parser  = sax.make_parser ()
            parser.setFeature (sax.handler.feature_validation, False)
            parser.setContentHandler (handler)
            
            parser.parse (file)
        return


    def xmlwrite (self, fd, embedded = False):

        if not embedded:
            fd.write ('<?xml version="1.0" encoding="utf-8"?>\n\n')
        
        fd.write ('<pyblio-schema>\n')

        keys = self.keys ()
        keys.sort ()

        for k in keys:
            self [k].xmlwrite (fd)
            fd.write ('\n')
            
        fd.write ('</pyblio-schema>\n')
        return
    
    
class Attribute:

    def __init__ (self, id):

        self.id = id

        self.type  = None

        # Is the attribute to be indexed ?
        self.indexed = False

        # A grouping information (for Enumerated types for instance)
        self.group = None
        
        self.names = {}

        self.range = (1, None)
        return

    def _name_get (self):

        return I18n.lz.trn (self.names)

    name = property (_name_get)

    def xmlwrite (self, fd):

        if self.range [1] is None:
            card = ""
        else:
            card = ' max="%d"' % self.range [1]
        
        if self.group is None:
            group = ""
        else:
            group = ' group="%s"' % self.group

        if self.indexed:
            idx = ' indexed="1"'
        else:
            idx = ''
        
        fd.write (' <attribute id="%s" type="%s"%s%s%s>\n' % (
            self.id, C_to_N [self.type], card, group, idx))

        names = self.names.keys ()
        names.sort ()

        for k in names:
            v = escape (self.names [k].encode ('utf-8'))
            if k: k = ' lang="%s"' % k
            fd.write ('  <name%s>%s</name>\n' % (k, v))

        fd.write (' </attribute>\n')
        return


# ==================================================

    
class SchemaParse (sax.handler.ContentHandler):

    """ This class parses the XML format of a Schema """

    def __init__ (self, schema):
        self.schema = schema
        return

    def setDocumentLocator (self, locator):
        
        self.locator = locator
        return
    
    
    def startDocument (self):
        # Start with an empty schema
        
        self.schema.clear ()

        self._attribute = None
        self._started   = False
        
        self._namelang = None
        self._namedata = None
        return

    def _error (self, msg):
        raise sax.SAXParseException (msg, None, self.locator)

    def _attr (self, attr, attrs):

        try:
            val = attrs [attr]
        except KeyError:
            self._error (_("missing '%s' attribute") % attr)

        return val
    
    def startElement (self, name, attrs):

        if name == 'pyblio-schema' and not self._started:
            self._started = True
            return
        
        if not self._started:
            self._error (_("this is not a pybliographer schema"))

        if name == 'attribute':
            if self._attribute is not None:
                self._error (_("'attribute' tags cannot be nested"))

            id = self._attr ('id', attrs)
            self._attribute = Attribute (id)

            tname = self._attr ('type', attrs)
            try:
                self._attribute.type = N_to_C [tname]
            except KeyError:
                self._error ('unknown attribute type "%s"' % tname)

            if attrs.has_key ('max'):
                try:
                    self._attribute.range = (1, int (attrs ['max']))

                except ValueError:
                    self._error ('invalid range value in attribute "%s"' % tname)

            if attrs.has_key ('group'):
                self._attribute.group = attrs ['group']

            if attrs.has_key ('indexed'):
                try:
                    v = int (attrs ['indexed'])
                except ValueError:
                    self._error ("invalid 'indexed' attribute")
                
                if v: self._attribute.indexed = True
            return
        
        
        if name == 'name':
            if self._attribute is None and self._document is None:
                self._error (_("'name' must be in an 'attribute'"))
            self._namelang = attrs.get ('lang', '')
            self._namedata = ''
            return
        
        self._error ("unknown tag '%s'" % name)

    def characters (self, data):

        if self._namedata is not None:
            self._namedata = self._namedata + data
        return

    def endElement (self, name):

        if name == 'pyblio-schema':
            self._started = False
            return
        
        if name == 'attribute':
            self.schema [self._attribute.id] = self._attribute
            self._attribute = None
            return

        if name == 'name':
            if self._attribute:
                self._attribute.names [self._namelang] = self._namedata

            elif self._document:
                self._document.names [self._namelang] = self._namedata
        return


