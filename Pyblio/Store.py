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
  the provided L{dbcreate <Pyblio.Stores.filestore.dbcreate>} function:
  
    >>> db = get ('file').dbcreate (path, schema)
  
  Once this is done, the database is ready to accept L{records
  <Pyblio.Store.Record>}:

    >>> record = Store.Record()
    >>> record.add('title', u'my title', Attribute.Text)
    >>> key = db.add(record)

  @see: the L{Database} class to know what operations can be performed
  on databases.
'''

import os, string, copy

from xml import sax
from xml.sax.saxutils import escape, quoteattr

from gettext import gettext as _

from Pyblio import Schema, Attribute, Exceptions, I18n

from Pyblio.Attribute import TxoItem

from cElementTree import ElementTree, iterparse, tostring

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

    As a convenience, it is possible to use L{Record.add} to build up
    a Record, instead of setting its fields manually.

    @ivar key: the key of the record, unique over the whole
    database. It is generated by the actual storage layer. This key
    has only an internal meaning. Do not expose it.

    @type key: instance of L{Key <Pyblio.Store.Key>} 

    @note: this class is shared by all stores
    """

    def __init__(self):
	self.key = None
        return

    def get (self, key, default = None):
        """ Get a field, understanding the dotted notation of the
        L{add} method"""
        if '.' not in key: return dict.get (self, key, default)

        l, r = key.split ('.')
        try:
            return self [l] [0].q [r]

        except (KeyError, IndexError):
            return default
        

    def xmlwrite (self, fd, offset = 1):
        """ Export as XML.

        Writes the content of the record as an XML fragment.

        @param fd: file descriptor to write to.
        """

        ws = ' ' * offset
        
        fd.write (ws + '<entry id=%s>\n' % quoteattr (str (self.key)))

        keys = self.keys ()
        keys.sort ()

        for k in keys:
            
            fd.write (ws + ' <attribute id=%s>\n' % quoteattr (k))
            
            for v in self [k]:
                v.xmlwrite (fd, offset + 2)
                fd.write ('\n')
            fd.write (ws + ' </attribute>\n')
            
        fd.write (ws + '</entry>\n')
        return

    def add (self, field, value, constructor = None):
        """
        Adds a new value to a field of this record.
        
        This function allows you to add an item to a record. It
        converts the specified 'value' by calling 'constructor' on it,
        and appends the resulting attribute to the record.

        If you specify something like 'a.b' in fields, the 'b'
        qualifier for field 'a' is set, for the last 'a' added. It is
        possible, if you know that you will only have B{one} 'a', to
        set 'a.b' before 'a'.

        Example:

          >>> rec.add ('title', u'My title', Attribute.Text)
          >>> rec.add ('title.subtitle', u'My subtitle', Attribute.Text)

          >>> rec.add ('author', definition, author_parser)
          
          
        @param field: the field we want to add in the record
        @type  field: a string, possibly containing a '.' in the case of structured attributes

        @param value: the 'source' value to set in the record. This
        value has not yet been converted into an
        L{Pyblio.Attribute} instance.

        @param constructor: a function that will turn a 'value' into a
        proper attribute.
        """        
        def generate (value, typ):
            """
            Constructs type with value. Effects neccessary dict-conversion
            operations
            """
            if isinstance (value, Attribute._Qualified):
                #is already of Attribute.XXX-type, so don't do anything.
                return value
            else: 
                if type (value) is dict:
                    return typ (**value)
                else:
                    return typ (value)

        
        if not '.' in field:
            f = self.get (field, [])

            if f and type(f [-1]) == Attribute.UnknownContent:
                q = f [-1].q
                f [-1] = generate (value, constructor)
                f [-1].q = q        
                return

            f = self.get (field, [])

            f.append (generate (value, constructor))
            self [field] = f

        else:        
            main, sub = field.split ('.')

            f = self.get (main, None)
            
            if not f:
                self [main] = [Attribute.UnknownContent ()]
                f = self [main]

            upd = f [-1].q.get (sub, [])
            upd.append (generate (value, constructor))
            f [-1].q [sub] = upd

    def deep_equal (self, other):
        if not isinstance (other, Record): return False

        for k in self:
            if not k in other or not len (self [k]) == len (other [k]):
                return False
            
            for x, y in zip (self [k], other [k]):
                if not x.deep_equal (y):
                    return False
            
        for k in other:
            if not k in self:
                return False
            
        return True

# --------------------------------------------------

class View(object):

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

    def index(self, key):
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

    def destroy(self, k):
        """ Delete and B{all the records} contained in the result set."""
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
            fd.write ('  <ref id="%d"/>\n' % v)
            
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

    @cvar entries: a L{resultset <Pyblio.Store.ResultSet>} containing
    all the records of the database.

    @cvar txo: a L{TxoGroup} instance, containing all the taxonomy
    definitions in the database. See L{TxoItem
    <Pyblio.Attribute.TxoItem>}.

    @cvar rs: a L{ResultSetStore} instance, containing all the result
    sets defined on this database.
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
                vals = [ vals ]

            entry [k] = vals = [ x for x in vals if x is not None ]
                
            if len (vals) == 0:
                del entry [k]
                continue

            for v in vals:
                for qk, qs in v.q.items ():
                    if type (qs) not in (list, tuple):
                        qs = [ qs ]

                    v.q [qk] = qs = [ x for x in qs if x is not None ]
                    
                    if len (qs) == 0:
                        del v.q [qk]
                    
            # check type and arity
            try:
                s = self.schema [k]
                
            except KeyError:
                raise Exceptions.SchemaError \
                      (_('unknown attribute %s') % `k`)

            for v in vals:
                if not isinstance (v, s.type):
                    raise Exceptions.SchemaError \
                          (_('%s: attribute %s has an incorrect type (should be %s but is %s)') % (
                        entry.key, `k`, `s.type`, repr (v)))
                
                for qk, qs in v.q.items ():
                    for q in qs:
                        if not isinstance (q, s.q [qk].type):
                            raise Exceptions.SchemaError \
                                  (_('%s: qualifier %s in attribute %s has an incorrect type (should be %s but is %s)') % (
                                entry.key, `qk`, `k`, `s.q [qk].type`, repr (q)))
                        
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


    def xmlread (self, fd):

        for event, elem in iterparse (fd, events = ('end',)):
            t = elem.tag

            if t == 'entry':
                k = elem.attrib ['id']
                r = Record ()
                
                for att in elem.findall ('./attribute'):
                    aid = att.attrib ['id']

                    try:
                        tp = self.schema [aid]
                    except KeyError:
                        raise StoreError (_("invalid attribute '%s'") % aid)

                    for sub in att:
                        a = tp.type.xmlread (sub)

                        # check for possible qualifiers
                        for q in sub.findall ('./attribute'):
                            qid = q.attrib ['id']

                            try:
                                stp = self.schema [aid].q [qid]
                            except KeyError:
                                raise StoreError (_("invalid attribute qualifier '%s'") % qid)

                            for subsub in q:
                                qv = stp.type.xmlread (subsub)

                                try:             a.q [qid].append (qv)
                                except KeyError: a.q [qid] = [qv]
                            
                        try:             r [aid].append (a)
                        except KeyError: r [aid] = [a]

                self.add (r, key = Key (k))
                
                elem.clear()

            if t == 'resultset':
                rsid = int (elem.attrib ['id'])
                rs   = self.rs.add (permanent = True, rsid = rsid)

                try:
                    rs.name = elem.attrib ['name']
                    
                except KeyError:
                    pass

                for ref in elem.findall ('./ref'):
                    rs.add (Key (ref.attrib ['id']))
                
                elem.clear()
            
            if t == 'txo-group':
                g = self.txo [elem.attrib ['id'].encode ('ascii')]
                def nesting (tree, parent):
                    for item in tree.findall ('./txo-item'):
                        i = TxoItem ()
                        
                        i.id = int (item.attrib ['id'])
                        i.parent = parent

                        for name in item.findall ('./name'):
                            lang = name.attrib.get ('lang', '')
                            i.names [lang] = name.text

                        g.add (i, i.id)

                        nesting (item, i.id)

                nesting (elem, None)
                
                elem.clear()
            
            elif elem.tag == 'pyblio-schema':
                self.schema = Schema.Schema ()
                self.schema.xmlread (elem)

                self._txo_create ()
                
            elif t == 'header':
                self.header = elem.text

    def _txo_create (self):
        # Finalize the link between the schema and the db by
        # creating the txo groups defined in the schema, so
        # that they exist when we read their content.

        for txo in self.schema.txo.values():
            try:
                g = self.txo._add (txo.group)
                # Fill in the TxoGroup with the known values
                for key, txo in txo.iteritems():
                    g.add(txo, key=key)
                    
            except Exceptions.ConstraintError:
                # Skip already defined txo groups
                pass                    
        return
    
# --------------------------------------------------

_dir = os.path.normpath(os.path.join(
    os.path.dirname (__file__), 'Stores'))

_modules = {}

for m in os.listdir(_dir):

    full = os.path.join(_dir, m)
    
    if os.path.isdir(full) and \
       m.endswith('store') and \
       os.path.exists(os.path.join(full, '__init__.py')):
        
        _modules[m.lower()[:-5]] = m
        continue
    
    m, ext = os.path.splitext(m)
    if ext != '.py' or not m.endswith('store'):
        continue
    
    _modules[m.lower()[:-5]] = m

_cache = {}

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
    backends, L{Pyblio.Stores.filestore}, L{Pyblio.Stores.bsddbstore}
    and L{Pyblio.Stores.memorystore}.
    """

    try:
        module = _cache [fmt]

        if module is None:
            raise ImportError ("store '%s' is not available" % fmt)

        return module

    except KeyError:
        parts = ('Pyblio', 'Stores', _modules[fmt])

        try:
            module = __import__ (string.join (parts, '.'))

        except ImportError, msg:
            _cache [fmt] = None
            raise

        for comp in parts [1:]:
            module = getattr (module, comp)

        _cache [fmt] = module
        
    return module

def modules ():

    return _modules.keys ()
