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

class Schema:

    def __init__ (self, file = None, template = None):

        self.documents = {}

        if not (file or template): return

        handler = SchemaParse (self)

        sax.parse (file, handler)
        return


    def save (self, file):

        pass
    
    
class Document:

    def __init__ (self, id):

        self.id = id

        self.name  = None
        self.names = {}
        
        self.mandatory = {}
        self.optional  = {}
        return


class Attribute:

    def __init__ (self, id):

        self.id = id

        self.name = None
        self.type = None

        self.names = {}
        return

    
class SchemaParse (sax.handler.ContentHandler):

    """ This class parses the XML format of a Schema """

    def __init__ (self, schema):
        import locale

        lang, charset = locale.getlocale (locale.LC_MESSAGES)

        self.lang = lang or ''
        self.lang_one = self.lang.split ('_') [0]

        self.schema = schema
        return

    def setDocumentLocator (self, locator):
        
        self.locator = locator
        return
    
    
    def startDocument (self):
        # Start with an empty schema
        
        self.schema.documents = {}

        self._attributes = {}
        self._attribute = None

        self._document = None
        self._started  = False
        
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

        if name == 'pyblio-schema':
            self._started = True
            return
        
        if not self._started:
            self._error (_("this is not a pybliographer schema"))

        if name == 'document':

            if self._document is not None:
                self._error (_("'document' tags cannot be nested"))

            id = self._attr ('id', attrs)
            self._document = Document (id)
            return

        if name == 'attribute':
            if self._attribute is not None:
                self._error (_("'attribute' tags cannot be nested"))

            id = self._attr ('id', attrs)
            self._attribute = Attribute (id)
            return
        
        if name in ('mandatory', 'optional'):
            if self._document is None:
                self._error (_("'%s' must be in a 'document'") % name)

            id = self._attr ('id', attrs)
            if not self._attributes.has_key (id):
                self._error (_("unknown document attribute '%s'") % id)

            if name == 'mandatory':
                self._document.mandatory [id] = self._attributes [id]
            else:
                self._document.optional [id] = self._attributes [id]
            return
        
        if name == 'name':
            if self._attribute is None and self._document is None:
                self._error (_("'name' must be in a 'document' or 'attribute'"))
            self._namelang = attrs.get ('lang', '')
            self._namedata = ''
            return
        
        self._error ("unknown tag '%s'" % name)

    def characters (self, data):

        if self._namedata is not None:
            self._namedata = self._namedata + data
        return


    def _trn (self, table):

        if table.has_key (self.lang):
            return table [self.lang]
        
        if table.has_key (self.lang_one):
            return table [self.lang_one]

        try:
            return table ['']
        except KeyError:
            self._error (_("missing default name"))
            

    def endElement (self, name):

        if name == 'document':

            self._document.name = self._trn (self._document.names)
            
            self.schema.documents [self._document.id] = self._document
            self._document = None
            return
        
        if name == 'pyblio-schema':
            self._started = False
            return
        
        if name == 'attribute':
            self._attribute.name = self._trn (self._attribute.names)

            self._attributes [self._attribute.id] = self._attribute
            self._attribute = None
            return

        if name == 'name':
            if self._attribute:
                self._attribute.names [self._namelang] = self._namedata

            elif self._document:
                self._document.names [self._namelang] = self._namedata
        return
    
