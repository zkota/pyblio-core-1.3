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


''' This Module contains the interfaces one might want to inherit from
in order to provide a specific database _storage_.

By itself, this base classes provide the XML import and export layers.
'''

import os, string, copy

from xml import sax
from xml.sax.saxutils import escape, quoteattr

from gettext import gettext as _

from Pyblio import Schema, Attribute


class StoreError (Exception):

    pass


class Key (int):

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

    The entry.native is a 2-uplet (format, native_content)

    For each attribute, it is possible that the returned value is
    lossy compared with the native data, if some information was not
    properly translated. This is known by calling self.has_loss (key)
    """

    def __init__ (self, type):
	self.type   = type
        
	self.key    = None
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
                  (quoteattr (str (self.key)), quoteattr (self.type.id)))

        if self.native:
            fd.write ('\n <native type=%s>%s</native>\n\n' %
                      (quoteattr (self.native [0]),
                       escape (self.native [1].encode ('utf-8'))))
        
        keys = self.keys ()
        keys.sort ()

        for k in keys:
            if self.has_loss (k): lossy = ' loss="1"'
            else:                 lossy = ''
            
            fd.write ('  <attribute id=%s%s>\n' % (quoteattr (k), lossy))
            
            for v in self [k]:
                fd.write ('   ')
                v.xmlwrite (fd)
                fd.write ('\n')
            fd.write ('  </attribute>\n')
            
        fd.write (' </entry>\n')
        return


class ResultSet:

    """ This class defines a result set, which is the product of a
    query on the database. ResultSets can be named and are then
    persistent. """

    def __init__ (self, name = None):
        self.name = name
        return

    def __iter__ (self):
        raise NotImplemented ('please override')
        


class Database (dict):

    ''' This class represents a full bibliographic database.  It also
    looks like a dictionnary, linking a Core.Key with a Core.Entry.

    [UPDATE RULE] Entries returned by a Database MUST be considered
    read-only. Modifications MUST be performed on a copy of the entry,
    and the resulting Entry MUST be set again in the database for the
    modification to be kept.
    '''

    def __init__ (self, schema = None, file = None):
	''' Create a new empty database with the specified schema '''

        self.schema = schema
        self.header = None
        
        self._id = 1

        if file:
            handler = DatabaseParse (self)

            try:
                sax.parse (file, handler)

            except ValueError, msg:
                raise StoreError (_("cannot open '%s': %s") % (file, msg))
                                  
	return


    def add (self, value, id = None):
        """ Insert a new entry in the database.

        New entries MUST be added with this method, not via an update
        with a hand-made Key.

        key is only useful for importing an existing database, by
        proposing a key choice.
        """

        if id:
            v = int (id)
            if v >= self._id:
                self._id = v + 1
        else:
            id = Key (self._id)
            self._id = self._id + 1

        assert not self.has_key (id), \
               _("a duplicate key has been generated: %d") % id

        value = copy.deepcopy (value)
        value.key = id
        
        dict.__setitem__ (self, id, value)
        return id
    

    def __setitem__ (self, key, value):

        # Ensure the key is not added, only updated.
        assert self.has_key (key), \
               _("use self.add () to add a new entry")

        value = copy.deepcopy (value)
        value.key = key
        
        dict.__setitem__ (self, key, value)
        return


    def rs_get (self):
        """ Return the available Result Sets """
        return []


    def rs_del (self, name):
        return


    def query (self, word, sort, name = None):
        raise NotImplemented ('please override')
    
    
    def save (self):
        raise NotImplemented ('please override')


    def xmlwrite (self, fd, schema = True):
        fd.write ('<?xml version="1.0" encoding="utf-8"?>\n\n')
        fd.write ('<pyblio-db>\n')

        if schema:
            self.schema.xmlwrite (fd, embedded = True)

        if self.header:
            fd.write ('<header>%s</header>\n' % escape (self.header))
        
        for v in self.itervalues ():
            v.xmlwrite (fd)
        
        fd.write ('</pyblio-db>\n')
        return


# ==================================================


class DatabaseParse (sax.handler.ContentHandler):

    def __init__ (self, db):

        self.db = db
        
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
        self._attribute = None
        self._tdata = None
        self._ntype = None
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

        # --------------------------------------------------
        if name == 'header':
            self._tdata = ''
            return
        
        if name == 'entry':
            id = self._attr ('id', attrs)
            tp = self._attr ('type', attrs)

            try:
                tp = self.db.schema [tp]
            except KeyError:
                self._error (_("document type '%s' is unsupported") % tp)

            self._entry = Entry (tp)
            self._ekey  = Key (id)
            return

        if name == 'native':
            if self._entry is None:
                self._error (_("tag 'native' must be in an 'entry'"))

            self._ntype = self._attr ('type', attrs)
            self._tdata = ''
            return
        
        if name == 'attribute':
            if self._entry is None:
                self._error (_("tag 'attribute' must be in an 'entry'"))

            id = self._attr ('id', attrs)

            try:
                tp = self._entry.type.typeof (id)

            except KeyError:
                self._error (_("invalid attribute '%s' in document '%s'") %
                             (id, self._entry.type.name))

            self._attribute = (id, tp.type)

            # Add loss information to the entry
            loss = attrs.get ('loss', '0')
            try:
                if int (loss) != 0:
                    self._entry.loss_set (id, True)
            except ValueError:
                pass

            return

        if name in Attribute.N_to_C.keys ():
            if self._attribute is None:
                self._error (_("attribute '%s' must be in an 'attribute' tag") % name)

            id = self._attribute [0]

            if self._attribute [1] is not Attribute.N_to_C [name]:
                self._error (_("attribute '%s' does not match type of '%s'") %
                             (name, id))
                
            if name == 'person':
                self._o = Attribute.Person (honorific = attrs.get ('honorific', None),
                                            first     = attrs.get ('first', None),
                                            last      = attrs.get ('last', None),
                                            lineage   = attrs.get ('lineage', None))
            elif name == 'date':

                d = []
                for v in (attrs.get ('day', None),
                          attrs.get ('month', None),
                          attrs.get ('year', None)):
                    if v: d.append (int (v))
                    else: d.append (None)

                self._o = Attribute.Date (day   = d [0],
                                          month = d [1],
                                          year  = d [2])

            elif name == 'reference':
                self._o = Attribute.Reference (self._attr ('ref', attrs))

            elif name == 'text':
                self._tdata = ''
                
            elif name == 'url':
                self._o = Attribute.URL (self._attr ('href', attrs))

            else:
                assert False, _("unexpected tag: %s") % name

            return
        
        self._error ("unknown tag '%s'" % name)
        return

    def characters (self, data):
        if self._in_schema:
            self._sparse.characters (data)
            return

        if self._tdata is not None:
            self._tdata = self._tdata + data
            
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

        if name == 'header':
            self.db.header = self._tdata
            self._tdata = None
            return

        if name == 'entry':
            self.db.add (self._entry, id = self._ekey)
            self._entry = None
            return

        if name == 'native':
            self._entry.native = (self._ntype, self._tdata)
            self._ntype = None
            self._tdata = None
            return
        
            
        if name in Attribute.N_to_C.keys ():

            if name == 'text':
                self._o = Attribute.Text (self._tdata)
                self._tdata = None
            
            id = self._attribute [0]
            
            try:
                self._entry [id].append (self._o)
            except KeyError:
                self._entry [id] = [self._o]

            self._o = None
            
        return


# --------------------------------------------------

_dir = os.path.normpath (os.path.join (
    os.path.dirname (__file__), 'Stores'))

_modules = {}

for m in os.listdir (_dir):

    m = os.path.splitext (m) [0]
    _modules [m.lower ()] = m

del _modules ['__init__']


def get (fmt):

    parts = ('Pyblio', 'Stores', _modules [fmt])

    module = __import__ (string.join (parts, '.'))

    for comp in parts [1:]:
        module = getattr (module, comp)
        
    return module
