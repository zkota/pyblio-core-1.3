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


'''
Overview
========

  Contains the base classes and interfaces used to define a database of records.
  
  The databases can be managed in different L{physical stores
  <Pyblio.Stores>}.  To create a new database, get a specific store
  implementation with the L{get <Pyblio.Store.get>} function, and call
  the provided L{dbcreate <Pyblio.Stores.File.dbcreate>} function:
  
    >>> db = get ('file').dbcreate (path, schema)
  
  Once this is done, the database is ready to accept L{records <Pyblio.Store.Record>}.

  @see: the L{Database} class
'''

import os, string, copy

from xml import sax
from xml.sax.saxutils import escape, quoteattr

from gettext import gettext as _

from Pyblio import Schema, Attribute, Exceptions, I18n, XML


class StoreError (Exception):
    """ Generic error occuring while accessing a database storage """
    
    pass


class Key (int):

    ''' A key that uniquely identifies a record in a database.

    @note: this class is shared by all backend stores.
    '''

    pass


class Record (dict):

    """
    A database record.

    It behaves like a dictionnary, which returns a B{list} of
    attributes for each key. The attributes types depend on the
    database L{Schema <Pyblio.Schema>}.

    @ivar key: the key of the record, unique over the whole
    database. It is generated by the actual storage layer.

    @type key: instance of L{Key <Pyblio.Store.Key>} 

    @note: this class is shared by all stores
    """

    def __init__ (self):
	self.key    = None
        return

    def xmlwrite (self, fd):
        """ Export as XML.

        Writes the content of the record as an XML fragment.

        @param fd: file descriptor to write to.
        """
        
        fd.write (' <entry id=%s>\n' % quoteattr (str (self.key)))

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

# --------------------------------------------------

class View (object):

    """ A view of a Result Set represents the Result Set sorted
    according to a specific criterion.

    DERIVED BY ALL STORES
    """

    def __iter__ (self):
        raise NotImplemented ('please override')

    def itervalues (self):
        raise NotImplemented ('please override')
    
    def iterkeys (self):
        raise NotImplemented ('please override')
    
    def iteritems (self):
        raise NotImplemented ('please override')

    def __len__ (self):
        raise NotImplemented ('please override')

    def __getitem__ (self, idx):
        raise NotImplemented ('please override')

        

# --------------------------------------------------

class ResultSet (object):

    """ A set of keys from the database.

    These sets can be manually managed by the user or be the result of
    a query. They can be made persistent, and are then stored along
    with the database.
    
    @note: this class is usually derived by every backend store.
    """


    def add (self, k):
        """ Add a new item in the set.

        @param k: the key to add to the set
        @type  k: instance of L{Key}
        """
        raise NotImplemented ('please override')
    
    def __delitem__ (self, k):
        """ Remove an item from the set.

        @param k: the key to remove from the set
        @type  k: instance of L{Key}
        """
        raise NotImplemented ('please override')

    def __iter__ (self):
        raise NotImplemented ('please override')

    def itervalues (self):
        raise NotImplemented ('please override')
    
    def iterkeys (self):
        raise NotImplemented ('please override')
    
    def iteritems (self):
        raise NotImplemented ('please override')

    def __len__ (self):
        raise NotImplemented ('please override')

    def has_key (self):
        raise NotImplemented ('please override')
    
    def view (self, criterion):
        raise NotImplemented ('please override')
        
    def xmlwrite (self, fd):

        if self.name:
            name = ' name=%s' % quoteattr (self.name.encode ('utf-8'))
        else:
            name = ''
            
        fd.write (' <resultset id="%d"%s>\n' % (self.id, name))
        
        for v in self:
            fd.write ('  <entry ref="%d"/>\n' % v)
            
        fd.write (' </resultset>\n')
        return


class ResultSetStore (object):

    """ Interface to the stored result sets.

    DERIVED BY ALL STORES
    """

    def __getitem__ (self, k):
        raise NotImplemented ('please override')

    def __delitem__ (self, k):
        raise NotImplemented ('please override')

    def __iter__ (self):
        raise NotImplemented ('please override')
        
    def add (self, permanent = False, rsid = None):
        raise NotImplemented ('please override')
        

# --------------------------------------------------
    
class TxoItem (object):

    """ Definition of a Txo item. This item can then be reused
    as the argument for Attribute.Txo creation.

    SHARED BY ALL STORES
    """

    def __init__ (self):

        self.id     = None
        self.group  = None
        self.parent = None
        
        self.names = {}
        return

    def _name_get (self):

        return I18n.lz.trn (self.names)

    name = property (_name_get)
    

    def xmlwrite (self, fd, space = ''):

        keys = self.names.keys ()
        keys.sort ()

        for k in keys:
            v = self.names [k]
            if k:
                lang = ' lang="%s"' % k
            else:
                lang = ''
            
            fd.write ('   %s<name%s>%s</name>\n' % (
                space, lang, escape (v.encode ('utf-8'))))
        
        return
    

class TxoGroup (object):

    """ Definition of a group of Txo items. Items in such a group can
    be accessed with a numeric key as a dictionnary, but also with
    logical names.

    DERIVED BY ALL STORES
    """

    def add (self, item, key = None):
        raise NotImplemented ('please override')

    def __getitem__ (self, k):
        raise NotImplemented ('please override')
        
    def __setitem__ (self, k):
        raise NotImplemented ('please override')
        
    def __delitem__ (self, k):
        raise NotImplemented ('please override')

    def __iter__ (self, k):
        raise NotImplemented ('please override')

    def keys (self):
        raise NotImplemented ('please override')

    def values (self):
        raise NotImplemented ('please override')

    def byname (self, name):
        """
        Return the L{TxoItem} whose name in the 'C' language is passed
        as parameter. This 'C' language is meant to be the name used
        by programs, rather than people.
        """
        raise NotImplemented ('please override')
        

    def _reverse (self):

        """ Create the reversed taxonomy tree """
        
        children = { None: [] }

        for k in self.keys ():
            children [k] = []

        for v in self.values ():
            children [v.parent].append (v.id)

        return children


    def expand (self, k):
        """ Return a txo and all its children """

        children = self._reverse ()

        full = []
        for c in children [k]:
            full = full + self.expand (c)

        full.append (k)
        
        return full

    
    def xmlwrite (self, fd):

        children = self._reverse ()
        
        def subwrite (node, depth = 0):
            child = self [node]

            space = ' ' * depth
            
            fd.write ('  %s<txo-item id="%d">\n' % (
                space, child.id))

            child.xmlwrite (fd, space)

            for n in children [node]:
                subwrite (n, depth + 1)
                
            fd.write ('  %s</txo-item>\n' % space)
            return

        for n in children [None]:
            subwrite (n)
        
        return


class TxoStore (object):

    """ This class is the interface via which Txo items can be
    manipulated.

    DERIVED BY ALL STORES
    """


    def __getitem__ (self, k):
        raise NotImplemented ('please override')
        
    def keys (self):
        raise NotImplemented ('please override')
        
    def xmlwrite (self, fd):

        keys = self.keys ()
        keys.sort ()

        for k in keys:
            fd.write (' <txo-group id="%s">\n' % k)
            self [k].xmlwrite (fd)
            fd.write (' </txo-group>\n\n')
            
        return

    # These methods are to be inherited, but are private

    def _add (self, group):
        raise NotImplemented ('please override')

    
# --------------------------------------------------

class Database (object):

    ''' A bibliographic database.

    A database behaves like a dictionnary, linking a L{key
    <Pyblio.Store.Key>} with a L{record <Pyblio.Store.Record>}. The
    records are B{typed}, and must follow the specifications of a
    L{Schema <Pyblio.Schema>}.

    Adding a new record
    ===================
    
      To add a new record r to a database db:
      
        >>> record = Record ()
        >>> record ['title'] = Attribute.Text ('my title')
        >>> # ...
        >>> key = db.add (record)
      
      When the record is added, a L{key <Pyblio.Store.Key>} is generated
      which uniquely references the record.
    
    Accessing a record
    ==================
    
      It is possible to use the database as a dictionnary. So, given a key k:
      
        >>> r = db [k]
      
      Alternatively, one can access all the records in a database in random
      order:
      
        >>> for key, record in db.entries.iteritems ():
        >>>    # do something with the record...
      
    Updating a record
    =================
    
      Simply store the record back once it is updated:
      
        >>> record = db [key]
        >>> ... # update the record
        >>> db [key] = record
        
        
    @see: L{queries <Pyblio.Query>}
    
    @attention: getting a record from the database returns a I{new copy}
    at each access. Updating this copy I{does not} change the stored
    value.

    @var entries: a L{resultset <Pyblio.Store.ResultSet>} containing
    all the records of the database.
    '''

    def __init__ (self):
        raise NotImplemented ('please override')


    def _entries_get (self):
        """ Return the result set that contains _all_ the entries. """
        
        raise NotImplemented ('please override')

    entries = property (_entries_get, None)
    

    def add (self, record, key = None):
        """ Insert a new entry in the database.

        New entries B{MUST} be added with this method, not via an
        update with a hand-made Key.

        @param record: the new record to add
        @type record: a L{Record <Pyblio.Store.Record>}
        
        @param key: only useful for importing an existing database, by
        I{proposing} a key choice.
        @type key: a L{Key <Pyblio.Store.Key>}
        """

        raise NotImplemented ('please override')


    def __setitem__ (self, key, record):
        """ Update a record.

        Updates a record with a new value.

        @param key: the record's key
        @type key: a L{Key <Pyblio.Store.Key>}

        @param record: the new value of the record
        @type record: a L{Record <Pyblio.Store.Record>}
        """
        
        raise NotImplemented ('please override')

    def __getitem__ (self, key):
        """ Get a record by key.

        @param key: the key of the requested record
        @type key: a L{Key <Pyblio.Store.Key>}
        """
        
        raise NotImplemented ('please override')

    def has_key (self, key):
        """ Check for the existence of a key.

        @param key: the key to check for
        @type key: a L{Key <Pyblio.Store.Key>}
        """
        
        raise NotImplemented ('please override')

    def query (self, query, permanent = False):
        raise NotImplemented ('please override')
    
    def collate (self, rs, field):
        """ Partition the result set in a list of sets for every value
        taken by the specified field"""
        
        sets = {}

        for k, rec in rs.iteritems ():
            try: value = rec [field] [0]
            except KeyError: value = None
            
            try:
                sets [value].add (k)

            except KeyError:
                rs = self.rs.add ()
                sets [value] = rs

                rs.add (k)

        return sets
    

    def save (self):
        raise NotImplemented ('please override')


    def validate (self, entry):
        """ Check an entry for conformance against the Schema. This
        method may modify the entry to normalize certain fields."""

        for k in entry.keys ():

            vals = entry [k]

            if type (vals) not in (list, tuple):
                vals      = [ vals ]
                entry [k] = vals
                
            elif len (vals) == 0:
                del entry [k]
                continue

            # check type and arity
            try:
                s = self.schema [k]
                
            except KeyError:
                raise Exceptions.SchemaError \
                      (_('unknown attribute %s') % `k`)

            for v in vals:
                if not isinstance (v, s.type):
                    raise Exceptions.SchemaError \
                          (_('attribute %s has an incorrect type (should be %s)') % (
                        `k`, `s.type`))

            l = len (vals)
            lb, ub = s.range
            
            if (lb is not None and l < lb) or (ub is not None and l > ub):
                raise Exceptions.SchemaError \
                      (_('attribute %s should have %s - %s values, not %d') % (
                    k, str (lb), str (ub), l))


            # additional special checks
            if s.type is Attribute.Txo:

                
                for v in vals:

                    # check if the enum is in the group defined in the schema
                    if v.group != s.group:
                        raise Exceptions.SchemaError (
                            _('txo item %s/%d should be in %s') % (
                            v.group, v.id, s.group))

                    # check for the enum existence
                    try:
                        self.txo [v.group] [v.id]
                        
                    except KeyError:
                        raise Exceptions.SchemaError (
                            _('invalid txo item %s/%d') % (
                            v.group, v.id))

                # Remove unnecessary txo items (for instance when a
                # more specific item is also present, there is no need
                # to keep the parent)
                g   = self.txo [s.group]
                ids = map (lambda x: x.id, vals)
                
                for v in [] + vals:

                    # exp is the list of children of the current txo item
                    exp = g.expand (v.id)
                    exp.remove (v.id)

                    # If another txo is a child of the current txo,
                    # the current one can be removed.
                    for i in ids:
                        if i in exp:
                            vals.remove (v)
                            break
                
                
        return entry

    def _txo_use_check (self, group, key):
        
        """ Check if a Txo can be safely removed """
        
        to_check = []
        # get the attributes that contain the txos of interest
        for s in self.schema.values ():
            if s.type is not Attribute.Txo: continue
            if s.group != group: continue

            to_check.append (s.id)


        for v in self.entries.itervalues ():
            for name in to_check:
                try:
                    attrs = v [name]
                except KeyError:
                    continue
                
                for attr in attrs:
                    if attr.id != key: continue
                    
                    raise Exceptions.ConstraintError \
                          (_('txo %s/%d still used in item %d') % (
                        group, key, v.key))

        return

    def xmlwrite (self, fd):
        """ Output a database in XML format """
        
        fd.write ('<?xml version="1.0" encoding="utf-8"?>\n\n')
        fd.write ('<pyblio-db>\n')

        self.schema.xmlwrite (fd, embedded = True)

        self.txo.xmlwrite (fd)

        if self.header:
            fd.write ('<header>%s</header>\n' % escape (self.header))
        
        for v in self.entries.itervalues ():
            v.xmlwrite (fd)

        for rs in self.rs:
            rs.xmlwrite (fd)
        
        fd.write ('</pyblio-db>\n')
        return


# ==================================================


class DatabaseParse (XML.Parser):

    def __init__ (self, db):

        self.db = db
        
        self._schema = Schema.Schema ()
        self._sparse = Schema.SchemaParse (self._schema)

        self._in_schema = False

        from Pyblio.I18n import Localize

        self._i18n = Localize ()
        return

    def parse (self, file):

        sax.parse (file, self)
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

        self._txoi = []
        self._txog = None

        self._rs = None
        
        self._lang = None
        return


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
        if name == 'txo-group':
            if self._txog is not None:
                self._error (_('nested "txo-group" are not supported'))

            name = self._attr ('id', attrs).encode ('ascii')
            self._txog = self.db.txo [name]
            return

        if name == 'txo-item':
            if self._txog is None:
                self._error (_('missing "txo-group"'))

            i = TxoItem ()
            i.id = int (self._attr ('id', attrs))

            # Already add this item as it is needed for potential children
            self._txog.add (i, key = i.id)
            
            self._txoi.append (i)
            return

        if name == 'name':
            if not self._txoi:
                self._error (_('missing "txo-item"'))
            self._tdata = ''
            self._lang = attrs.get ('lang', '')
            return
        

        if name == 'header':
            self._tdata = ''
            return
        
        if name == 'entry':
            if self._rs is not None:
                id = self._attr ('ref', attrs)
                self._rs.add (Key (id))
                
            else:
                id = self._attr ('id', attrs)

                self._entry = Record ()
                self._ekey  = Key (id)
            return

        if name == 'native':
            if self._entry is None:
                self._error (_("tag 'native' must be in an 'entry'"))

            self._ntype = self._attr ('type', attrs)
            self._tdata = ''
            return

        if name == 'resultset':

            rsid = int (self._attr ('id', attrs))
            self._rs = self.db.rs.add (permanent = True, rsid = rsid)
            
            try:
                self._rs.name = attrs ['name']
                
            except KeyError:
                pass
            return
        
        if name == 'attribute':
            if self._entry is None:
                self._error (_("tag 'attribute' must be in an 'entry'"))

            id = self._attr ('id', attrs)

            try:
                tp = self._schema [id]

            except KeyError:
                self._error (_("invalid attribute '%s' in entry '%s'") %
                             (id, self._ekey))

            self._attribute = (id, tp.type)
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

            elif name == 'txo':
                group = self._schema [self._attribute [0]].group
                id    = int (self._attr ('id', attrs))

                item  = self.db.txo [group] [id]
                
                self._o = Attribute.Txo (item)

            elif name == 'id':
                self._o = Attribute.ID (self._attr ('value', attrs))
                
            else:
                self._error (_("unexpected tag: %s") % name)

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
            if name != 'pyblio-schema':
                self._sparse.endElement (name)
                return

            
            self._in_schema = False
            self._sparse    = None
            
            self.db.schema = self._schema

            # Finalize the link between the schema and the db:
            #
            #  1. create txo groups defined in the schema
            #

            for v in self.db.schema.values ():
                if v.type is not Attribute.Txo: continue

                try:
                    self.db.txo._add (v.group)

                except Exceptions.ConstraintError:
                    pass
                
            return

        if name == 'txo-group':
            self._txog = None
            return
        
        if name == 'txo-item':
            i = self._txoi.pop ()

            if self._txoi:
                i.parent = self._txoi [-1].id

            # Update the item with its final value
            self._txog [i.id] = i
            return
        
        if name == 'header':
            self.db.header = self._tdata
            self._tdata = None
            return

        if name == 'entry':
            if self._rs is None:
                self.db.add (self._entry, key = self._ekey)
                self._entry = None
            return

        if name == 'resultset':
            self._rs = None
            return
        
        if name == 'native':
            self._entry.native = (self._ntype, self._tdata)
            self._ntype = None
            self._tdata = None
            return
        
        if name == 'name':
            self._txoi [-1].names [self._lang] = self._tdata
            self._tdata = None
            return
        
        if self._attribute and name in Attribute.N_to_C.keys ():

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

    m, ext = os.path.splitext (m)

    if ext != '.py': continue
    
    _modules [m.lower ()] = m

del _modules ['__init__']


def get (fmt):

    """ Return the methods provided by a specific storage layer.

    For instance:

     >>> fmt = get ('file')
     >>> db = fmt.dbopen (...)
     
    The methods are:

      - dbcreate (file, schema): create a new database
      
      - dbopen (file): open a database in the specific store
      
      - dbimport (file): import an XML database into the specific store
      
      - dbdestroy (file): destroy a database

    For more information, consult the documentation for the specific
    backends, L{Pyblio.Stores.File} and L{Pyblio.Stores.bsddb}.
    """

    parts = ('Pyblio', 'Stores', _modules [fmt])

    module = __import__ (string.join (parts, '.'))

    for comp in parts [1:]:
        module = getattr (module, comp)
        
    return module

def modules ():

    return _modules.keys ()
