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

"""
Provides an in-memory store, which can read and save the database in
Pyblio's XML format.

This store is useful for relatively small databases (up to a few
thousand entries) and that are processed in batch once for instance,
as the reading and writing can be slow.
"""
import weakref
from gettext import gettext as _

import os, copy, string

from Pyblio import Store, Callback, Attribute, Exceptions, Tools, Query, Sort
from Pyblio.Stores import resultset

from Pyblio.Arrays import KeyArray, match_arrays

class RODict(Callback.Publisher):
    """ Read-only dictionnary """

    def __init__ (self, _dict):
        Callback.Publisher.__init__ (self)
        self._db = _dict
        return

    def view(self, criterion):
        return resultset.View(self, criterion)        

    def itervalues (self):
        return self._db.itervalues ()

    def iteritems (self):
        return self._db.iteritems ()

    def iterkeys (self):
        return self._db.iterkeys ()

    __iter__ = iterkeys

    def __len__ (self):
        return len(self._db)

    def _forward (self, * args):
        """ forward messages. the message name is passed last """
        args, msg = args [:-1], args [-1]
        return apply (self.emit, (msg,) + args)


class ResultSetStore(dict, Store.ResultSetStore):
    def __init__ (self, db):
        self._db = weakref.ref(db)
        self._id = 1
        return

    def new(self, rsid=None):
        """ Create an empty result set """
        db = self._db()
        assert db is not None
        (self._id, rsid) = Tools.id_make(self._id, rsid)
        # a result set keeps a strong reference on the database, as it
        # accesses its content pretty naturally
        rs = resultset.ResultSet(rsid, db)
        return rs

    def __iter__ (self):
        return self.itervalues()

    def update(self, result_set):
        self[result_set.id] = result_set
    
# --------------------------------------------------

class Database (Query.Queryable, Store.Database, Callback.Publisher):

    def __init__ (self, schema = None, file = None,
                  create = False):

        Callback.Publisher.__init__ (self)

        self._dict   = {}
        self._rodict = RODict (self._dict)

        self.register('add-item', self._rodict._forward, 'add-item')
        self.register('delete-item', self._rodict._forward, 'delete-item')
        self.register('update-item', self._rodict._forward, 'update-item')
        
        self.file = file

        self.schema = schema
        
        self.header = None
        self.rs     = ResultSetStore (self)
        
        self._id = 1
        self._indexed = False

        if not create:
            try:
                self.xmlread(open(file))

            except IOError, msg:
                raise Store.StoreError(_("cannot open database: %s") % msg)

        return

    def _entries_get(self):
        """ Return the result set that contains all the entries. """

        return self._rodict

    entries = property(_entries_get, None)


    def add(self, record, key = None):
        """ Insert a new entry in the database.

        New entries MUST be added with this method, not via an update
        with a hand-made Key.

        key is only useful for importing an existing database, by
        proposing a key choice.
        """

        self._id, key = Tools.id_make (self._id, key)

        key = Store.Key (key)
        
        assert not self.has_key (key), \
               _("a duplicate key has been generated: %d") % key

        record = copy.copy (record)
        record.key = key

        record = self.validate (record)
        
        self._dict [key] = record

        if self._indexed:
            self._idxadd(key, record)
            
        self.emit ('add-item', key)
        
        return key


    def __delitem__(self, k):

        del self._dict [k]
        self.emit ('delete-item', k)

        if self._indexed:
            self._idxdel(k)
        return


    def has_key(self, k):
        return self._dict.has_key(k)


    def __setitem__ (self, key, value):

        # Ensure the key is not added, only updated.
        assert self.has_key (key), \
               _("use self.add () to add a new entry")

        value = copy.deepcopy (value)
        value.key = key

        value = self.validate (value)
        
        self._dict [key] = value

        if self._indexed:
            self._idxdel(key)
            self._idxadd(key, value)
            
        self.emit ('update-item', key)
        return


    def __getitem__ (self, key):
        return self._dict [key]


    def save(self):

        if self.file is None:
            return
        
        try:
            os.unlink (self.file + '.bak')
        except OSError:
            pass

        if os.path.exists (self.file):
            os.rename (self.file, self.file + '.bak')

        fd = open (self.file, 'w')
        self.xmlwrite (fd)
        fd.close ()

        return

    def _idxadd(self, key, val):
        
        for attribs in val.values():
            for attrib in attribs:
                
                for idx in attrib.index():
                    self._idx_b.setdefault(key, {})[idx] = True

                    try:
                        self._idx_f[idx].add(key)
                    except KeyError:
                        a = KeyArray()
                        a.add(key)
                        
                        self._idx_f[idx] = a
        return

    def _idxdel(self, key):

        try:
            ws = self._idx_b[key]

        except KeyError:
            return

        del self._idx_b[key]
        
        for w in ws:
            del self._idx_f[w][key]

        return
    
    def index(self):
        """ Turn on indexing of the db content. """

        if self._indexed:
            return
        
        self._idx_f = {}
        self._idx_b = {}

        for key, rec in self.entries.iteritems():
            self._idxadd(key, rec)

        self._indexed = True
        return

    def _q_anyword(self, query):
        if self._indexed:
            word = query.word.lower()

            try:
                return self._idx_f[word]
            except KeyError:
                return KeyArray()

        return Query.Queryable._q_anyword(self, query)
        
def dbdestroy(path, nobackup=False):
    os.unlink(path)
    if nobackup:
        try:
            os.unlink (path + '.bak')
        except OSError:
            pass
    return
    
def dbcreate(path, schema, args={}):
    # Ensure we are the ones creating the file
    try:
        fd = os.open(path, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0666)
    except OSError, msg:
        raise Store.StoreError (_("cannot create database '%s': %s") % (
            path, msg))
    os.close(fd)
    db = Database (schema=schema, file=path, create=True)
    db.save ()
    return db

def dbopen(path, args={}):
    return Database(file=path)

def dbimport(target, source, args={}):
    db = Database(file=source)
    db.file = target
    return db

description = _("Flat XML file storage")
