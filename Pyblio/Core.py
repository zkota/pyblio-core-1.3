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


''' This Module contains the interfaces one might want to implement in
order to provide a specific database _storage_.

Please note: this is an interface definition, but it can also be used
as a base class.
'''

from xml import sax
from xml.sax.saxutils import escape, quoteattr

from gettext import gettext as _

from Pyblio import Schema


class Key (str):

    ''' A key uniquely identifies an entry in a database '''

    pass


class Entry (dict):

    """
    A database entry. It behaves like a dictionnary, which returns a
    list of attributes for each key. The attributes types depend on
    the database schema.

    The entry.key is an instance of Core.Key, and has to be unique
    over the database.

    The entry.type is an instance of Schema.Document. It links the
    field names with their type.

    For each attribute, it is possible that the returned value is
    lossy compared with the native data, if some information was not
    properly translated. This is known by calling self.has_loss (key)
    """

    def __init__ (self, key, type):
	self.type   = type
	self.key    = key
        self.native = None

        self._loss = {}
        return

    def has_loss (self, key):
	''' Returns wether the entry attribute is converted with loss '''
	return self._loss.get (key, False)

    def loss_set (self, key, flag = True):
        self._loss [key] = flag
        return

    def xmlwrite (self, fd):
        fd.write (' <entry id=%s type=%s>\n' %
                  (quoteattr (self.key), quoteattr (self.type.id)))
        
        keys = self.keys ()
        keys.sort ()

        for k in keys:
            fd.write ('  <attribute id=%s>\n' % quoteattr (k))
            for v in self [k]:
                fd.write ('   ')
                v.xmlwrite (fd)
                fd.write ('\n')
            fd.write ('  </attribute>\n')
            
        fd.write (' </entry>\n')
        return
    


class Database (dict):

    ''' This class represents a full bibliographic database.  It also
    looks like a dictionnary, linking a Core.Key with a Core.Entry.'''


    def __init__ (self, schema):
	''' Create a new empty database with the specified schema '''
        self.schema = schema
	return

    def xmlwrite (self, fd):
        fd.write ('<?xml version="1.0" encoding="utf-8"?>\n\n')
        fd.write ('<pyblio-db>\n')

        self.schema.xmlwrite (fd, embedded = True)

        for v in self.itervalues ():
            v.xmlwrite (fd)
        
        fd.write ('</pyblio-db>\n')
        return


# ==================================================


class DatabaseParse (sax.handler.ContentHandler):

    def __init__ (self):

        self.db = Database (None)
        
        self._schema = Schema.Schema ()
        self._sparse = Schema.SchemaParse (self._schema)

        self._in_schema = False
        return

    def setDocumentLocator (self, locator):
        self.locator = locator
        self._sparse.setDocumentLocator (locator)
        return
    
    
    def startDocument (self):
        self._started = False

        self._entry = None
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

        if self._in_schema:
            self._sparse.startElement (name, attrs)
            return
        

        if name == 'pyblio-schema':
            self._in_schema = True
            
            self._sparse.startDocument ()
            self._sparse.startElement (name, attrs)
            return

        if name == 'pyblio-db' and not self._started:
            self._started = True
            return
        
        if not self._started:
            self._error (_("this is not a pybliographer database"))
        
        self._error ("unknown tag '%s'" % name)


    def characters (self, data):
        if self._in_schema:
            self._sparse.characters (data)
            return
        
        return

    def endElement (self, name):

        if self._in_schema:
            if name == 'pyblio-schema':
                self._in_schema = False
                self._sparse    = None
                
                self.db.schema = self._schema

            else:
                self._sparse.endElement (name)
                
            return
        
        return


def open (file):
    
    handler = DatabaseParse ()
    sax.parse (file, handler)
    
    return handler.db
