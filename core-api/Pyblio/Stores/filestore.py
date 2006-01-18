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

"""
Provides an in-memory store, which can read and save the database in
Pyblio's XML format.

This store is useful for relatively small databases (up to a few
thousand entries) and that are processed in batch once for instance,
as the reading and writing can be slow.
"""

from gettext import gettext as _

import os, copy, string

from Pyblio import Store, Callback, Attribute, Exceptions, Tools, Query, Sort


class TxoGroup (dict, Store.TxoGroup, Callback.Publisher):

    def __init__ (self, group):

        Callback.Publisher.__init__ (self)
        
        self._id = 1
        self._group = group
        self._byname = {}
        return

    def _check (self, item):
    
        if item.parent is not None and \
               not self.has_key (item.parent):

            raise Exceptions.ConstraintError \
                  (_('txo has unknown parent %s') % `item.parent`)

        return


    def __setitem__ (self, key, item):

        self._check (item)

        if not self.has_key (key):
            raise KeyError (_('txo %s does not exist') % `key`)
        
        v = copy.deepcopy (item)
        
        v.id    = key
        v.group = self._group
        
        dict.__setitem__ (self, key, v)

        try: self._byname [v.names ['C']] = v
        except KeyError: pass
        
        return


    def byname (self, key):

        return self._byname [key]

    
    def add (self, item, key = None):

        self._check (item)

        self._id, key = Tools.id_make (self._id, key)

        v = copy.deepcopy (item)
        
        v.id    = key
        v.group = self._group
        
        dict.__setitem__ (self, key, v)

        try: self._byname [v.names ['C']] = v
        except KeyError: pass
        
        return key

    def __delitem__ (self, k):

        # Internal check for coherency: is the entry used as a parent
        # for someone ?
        for v in self.values ():

            if v.parent == k:
                raise Exceptions.ConstraintError \
                      (_('txo %s is parent of %s') % (
                    `k`, `v.id`))

        self.emit ('delete', self._group, k)

        dict.__delitem__ (self, k)
        return
    

class TxoStore (dict, Store.TxoStore):

    def __init__ (self, db):

        self._db = db
        return
    

    def _add (self, group):        
        if self.has_key (group):
            raise Exceptions.ConstraintError \
                  (_('group %s exists') % `group`)
        
        gp = TxoGroup (group)
        gp.register ('delete', self._db._txo_use_check)
        
        self [group] = gp
        
        return gp


# --------------------------------------------------
class View (object):

    def __init__ (self, src, crit):

        self._crit = crit
        self._src  = src
        
        self._update (None)

        self._src.register ('add-item', self._update)
        self._src.register ('delete-item', self._update)
        self._src.register ('update-item', self._update)
        return
    
    def _update (self, key):

        view = [ (self._crit.cmp_key (e), e.key) for e in self._src.itervalues () ]
        view.sort (lambda a, b: Sort.compare (a [0], b [0]))

        self._view = [ x [1] for x in view ]
        return

    def __len__ (self):

        return len (self._view)


    def __getitem__ (self, i):

        return self._view [i]

    def __iter__ (self):

        return iter (self._view)

    def iterkeys (self):

        return iter (self._view)
    
    def iteritems (self):

        for i in self._view:
            yield (i, self._src._dict [i])
            
    def itervalues (self):

        for i in self._view:
            yield self._src._dict [i]

    def index(self, key):
        return self._view.index(key)

    
class Viewable (object):

    def view (self, criterion):

        return View (self, criterion)
        

class ResultSet (dict, Viewable, Store.ResultSet, Callback.Publisher):

    def __init__ (self, rsid, db):

        Callback.Publisher.__init__ (self)
        dict.__init__ (self)

        self.id   = rsid
        self.name = None

        self._dict = db
        return


    def add (self, k):
        
        self [k] = 1
        self.emit ('add-item', k)
        return

    def __delitem__ (self, k):

        dict.__delitem__ (self, k)
        self.emit ('delete-item', k)
        return
    
    def itervalues (self):
        
        for k in dict.iterkeys (self):
            yield self._dict [k]

    def iteritems (self):
        
        for k in dict.iterkeys (self):
            yield (k, self._dict [k])


    def _on_db_delete (self, k):
        """ invoked when the database removes an item """

        try:
            del self [k]
            self.emit ('delete-item', k)
            
        except KeyError:
            pass
        
        return

    def _on_db_update (self, k):

        self.emit ('update-item', k)
        return
    

class RODict (Viewable, Callback.Publisher):

    """ Read-only dictionnary """

    def __init__ (self, _dict):
        Callback.Publisher.__init__ (self)
        
        self._dict = _dict
        return

    def itervalues (self):
        
        return self._dict.itervalues ()

    def iteritems (self):
        
        return self._dict.iteritems ()

    def iterkeys (self):
        
        return self._dict.iterkeys ()

    __iter__ = iterkeys

    def __len__ (self):

        return len (self._dict)

    def _forward (self, * args):

        """ forward messages. the message name is passed last """
        
        args, msg = args [:-1], args [-1]
        
        return apply (self.emit, (msg,) + args)


class ResultSetStore (dict, Store.ResultSetStore):

    def __init__ (self, db):
        self._db = db
        self._id = 1
        return
    

    def add (self, permanent = False, rsid = None):
        """ Create an empty result set """

        (self._id, rsid) = Tools.id_make (self._id, rsid)
        
        rs = ResultSet (rsid, self._db._dict)
        
        self._db.register ('delete-item', rs._on_db_delete)
        self._db.register ('update-item', rs._on_db_update)
        
        if permanent:
            self [rs.id] = rs
        
        return rs

    def __iter__ (self):

        return self.itervalues ()

# --------------------------------------------------

class Database (Query.Queryable, Store.Database, Callback.Publisher):

    def __init__ (self, schema = None, file = None,
                  create = False):

        Callback.Publisher.__init__ (self)

        self._dict   = {}
        self._rodict = RODict (self._dict)

        self.register ('add-item', self._rodict._forward, 'add-item')
        self.register ('delete-item', self._rodict._forward, 'delete-item')
        self.register ('update-item', self._rodict._forward, 'update-item')
        
        self.file = file

        self.schema = schema
        
        self.header = None
        self.txo    = TxoStore (self)
        self.rs     = ResultSetStore (self)
        
        self._id = 1

        if create:
            self._txo_create ()

            # WARNING: this code contains a race condition. This
            # exception is only here to trap blatant errors, not to
            # avoid concurrent accesses. How does one open a file with
            # O_CREAT, BTW ? Mabe this would not be portable at all.
            
            if os.path.exists (file):
                raise Store.StoreError (_("database '%s' already exists") % file)
            
            self.save ()

        else:
            try:
                self.xmlread (open (file))

            except IOError, msg:
                raise Store.StoreError (_("cannot open database: %s") % msg)
            
        return

    def _entries_get (self):
        """ Return the result set that contains all the entries. """

        return self._rodict

    entries = property (_entries_get, None)


    def add (self, value, key = None):
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

        value = copy.copy (value)
        value.key = key

        value = self.validate (value)
        
        self._dict [key] = value

        self.emit ('add-item', key)
        
        return key


    def __delitem__ (self, k):

        del self._dict [k]
        self.emit ('delete-item', k)

        return


    def has_key (self, k):
        return self._dict.has_key (k)


    def __setitem__ (self, key, value):

        # Ensure the key is not added, only updated.
        assert self.has_key (key), \
               _("use self.add () to add a new entry")

        value = copy.deepcopy (value)
        value.key = key

        value = self.validate (value)
        
        self._dict [key] = value

        self.emit ('update-item', key)
        return


    def __getitem__ (self, key):
        return self._dict [key]


    def save (self):

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
    

def dbdestroy (path, nobackup = False):

    os.unlink (path)

    if nobackup:
        try:
            os.unlink (path + '.bak')
            
        except OSError:
            pass
    return

    
def dbcreate (path, schema):

    return Database (schema = schema, file = path,
                     create = True)


def dbopen (path):

    return Database (file = path)


def dbimport (target, source):

    db = Database (file = source)
    db.file = target

    return db


description = _("Flat XML file storage")
