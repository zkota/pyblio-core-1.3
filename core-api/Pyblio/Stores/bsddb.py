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

from gettext import gettext as _

import os, shutil, copy
import cPickle as pickle

from bsddb3 import db

from Pyblio import Store, Schema, Callback, Attribute, Exceptions

_pl = pickle.loads
_ps = pickle.dumps

# --------------------------------------------------

class DBIterBase:
    """ Iterators on the full database """
    
    def __init__ (self, cursor):
        self._cursor = cursor
        self._data   = self._cursor.first ()
        return

    def __iter__ (self):
        return self


    def next (self):
        if self._data is None:
            raise StopIteration ()

        data = self._data
        self._data = self._cursor.next ()
        
        return self._content (data)

class DBIter (DBIterBase):
    """ Iterate over the keys """
    def _content (self, data):

        return Store.Key (data [0])

class DBIterValues (DBIterBase):
    """ Iterate over the values """
    def _content (self, data):

        return _pl (data [1])

class DBIterItems (DBIterBase):
    """ Iterate over (key, value) pairs """
    def _content (self, data):

        return Store.Key (data [0]), _pl (data [1])


# --------------------------------------------------

class ResultSet (Store.ResultSet):

    def __init__ (self, env, rs, id, name = None):
        self.name = name

        self._db = env
        self._rs = rs
        self._id = id
        
        self._cursor = rs.cursor ()
        self._permanent = self.name is not None

        self._restart ()
        return

    def __iter__ (self):
        return self

    def _restart (self):
        self._data   = self._cursor.first ()
        return

    def add (self, k, txn = None):

        self._rs.put (str (k), '', txn = txn)
        self._restart ()
        return

    def __delitem__ (self, k, txn = None):

        self._rs.delete (str (k), txn = txn)
        self._restart ()
        return
    

    def next (self):
        if self._data is None:
            self._restart ()
            raise StopIteration ()

        data = self._data
        self._data = self._cursor.next ()
        
        return Store.Key (data [0])


    def __del__ (self):
        self._rs.close ()

        if self._permanent: return

        # physically destroy the database
        _db = db.DB (self._db)

        try: _db.remove ('rs', self._id)
        except db.DBNoSuchFileError: pass
        
        return


    def _on_delete (self, key, txn = None):

        try:
            self.__delitem__ (key, txn)
            self._restart ()
            
        except KeyError:
            pass

        return
    

class ResultSetStore (dict, Store.ResultSetStore):

    def __init__ (self, db):

        self._env  = db._env
        self._meta = db._meta

        self._db = db
        return
    

    def __delitem__ (self, k):

        self [k]._permanent = False
        dict.__delitem__ (self, k)
        return


    def __iter__ (self):
        return self.itervalues ()


    def add (self, name = None, txn = None):
        """ Create an empty result set """

        txn = self._env.txn_begin (parent = txn)
        
        # get the next rs id
        (rsid, avail) = _pl (self._meta.get ('rs'))

        if name: avail [name] = str (rsid)

        self._meta.put ('rs', _ps ((rsid + 1, avail)))

        rsid = str (rsid)
        
        rs = db.DB (self._env)
        rs.open ('rs', rsid, db.DB_HASH, db.DB_CREATE)
        
        txn.commit ()

        rs = ResultSet (self._env, rs, rsid, name)
        if name: self [name] = rs

        self._db.register ('delete-item', rs._on_delete)
        
        return rs
    
# --------------------------------------------------

class EnumGroup (Store.EnumGroup, Callback.Publisher):


    def __init__ (self, parent, group):

        Callback.Publisher.__init__ (self)

        self._db   = parent._db
        self._env  = parent._env
        self._enum = parent._enum
        
        self._group = group
        return

    
    def add (self, item, key = None):

        v = self._enum.get (self._group)

        vid, data = _pl (v)

        # Key is the key that will be used for the entry, id is
        # the current serial (which can be different)
        if key:
            if key > vid: vid = key
        else:
            key = vid

        v = copy.deepcopy (item)
        v.id    = key
        v.group = self._group
        
        data [key] = v
        
        self._enum.put (self._group, _ps ((vid + 1, data)))
        
        return key


    def keys (self):

        return _pl (self._enum.get (self._group)) [1].keys ()

    def values (self):

        return _pl (self._enum.get (self._group)) [1].values ()
        
    
    def __delitem__ (self, k):

        for v in self._db.itervalues ():
            for attrs in v.values ():
                for attr in attrs:
                    if not isinstance (attr, Attribute.Enumerated):
                        break

                    if (attr.id, attr.group) == (k, self._group):
                        raise Exceptions.ConstraintError \
                              (_('enum %s/%d used in item %d') % (
                            self._group, k, v.key))

        v = _pl (self._enum.get (self._group))
        del v [1] [k]

        self._enum.put (self._group, _ps (v))
        return
    

    def __getitem__ (self, k):
        v = self._enum.get (self._group)

        return _pl (v) [1] [k]


class EnumStore (Store.EnumStore):

    def __init__ (self, parent):

        self._db  = parent
        self._env = parent._env

        self._enum = db.DB (self._env)
        self._enum.open ('pybliographer', 'enum',
                         db.DB_HASH, db.DB_CREATE)
        return

    
    def __getitem__ (self, group):

        return EnumGroup (self, group)


    def keys (self):
        k = []
        c = self._enum.cursor ()

        d = c.first ()
        while d:
            key, data = d
            k.append (key)
            
            d = c.next ()

        return k

    
    def add (self, group):

        v = self._enum.get (group)

        if v is not None:
            raise Exceptions.ConstraintError (_('group %s exists') % `group`)
        
        self._enum.put (group, _ps ((1, {})))

        return EnumGroup (self, group)
    

# --------------------------------------------------
    
class Database (Store.Database, Callback.Publisher):
    """ A Pyblio database stored in a BSD DB3 engine """
    
    def __init__ (self, path, schema = None, create = False):

        Callback.Publisher.__init__ (self)
        
        if create:
            try:
                os.mkdir (path)

            except OSError, msg:
                raise Store.StoreError (_("cannot create '%s': %s") % (
                    path, msg))
            
            flag = db.DB_CREATE

        else:
            flag = 0

        self._path = path
        
        self._env = db.DBEnv ()
        self._env.open (path, flag | db.DB_INIT_MPOOL | db.DB_INIT_TXN)

        # DB containing the actual entries
        self._db  = db.DB (self._env)
        self._db.open ('pybliographer', 'db', db.DB_HASH, flag)

        # DB with meta informations
        self._meta  = db.DB (self._env)
        self._meta.open ('pybliographer', 'meta', db.DB_HASH, flag)

        self.rs = ResultSetStore (self)

        if create:
            self.schema = schema
            self._meta.put ('schema', _ps (schema))
            self._meta.put ('rs', _ps ((0, {})))
            self._meta.put ('serial', '1')
        else:
            self.schema = _pl (self._meta.get ('schema'))
            id, store = _pl (self._meta.get ('rs'))

            for k, v in store.items ():
                d = db.DB (self._env)

                try:
                    d.open ('rs', v, db.DB_HASH)
                    
                except db.DBNoSuchFileError:
                    del store [k]
                    continue
                
                rs = ResultSet (self._env, d, v, k)
                self.rs [k] = rs

            # store the updated rs list
            self._meta.put ('rs', _ps ((id, store)))

        
        # Full text indexing DB
        self._idx = db.DB (self._env)
        self._idx.set_flags (db.DB_DUP)
        self._idx.open ('pybliographer', 'idx', db.DB_HASH, flag)

        # Store for Enumerated values
        self.enum = EnumStore (self)

        # No header in this db yet
        self.header = None
        return


    def save (self):

        # Flush the databases
        self._db.sync ()
        self._meta.sync ()
        self._idx.sync ()
        return


    def add (self, val, id = None):

        val = self.validate (val)

        # Be careful to always point after the last serial id used.
        txn = self._env.txn_begin ()

        try:
            serial = int (self._meta.get ('serial'))

            if id:
                if id > serial: serial = id
            else:
                id = serial
            
            self._meta.put ('serial', str (serial + 1),
                            txn = txn)
            
            key = Store.Key (self._insert (id, val, txn))

        except:
            txn.abort ()
            raise

        txn.commit ()
        return key
    

    def __setitem__ (self, key, val):

        assert self.has_key (key), \
               _('entry %s does not exist') % `key`

        val = self.validate (val)

        txn = self._env.txn_begin ()

        try:
            self._idxdel (str (key), txn)
            self._insert (key, val, txn)

        except:
            txn.abort ()
            raise

        txn.commit ()
        return


    def __delitem__ (self, key):
        id = str (key)
        
        txn = self._env.txn_begin ()

        try:
            self._idxdel (id, txn)
            self._db.delete (id, txn)

        except:
            txn.abort ()
            raise

        self.emit ('delete-item', key, txn)

        txn.commit ()
        return
    

    def has_key (self, k):

        id = str (k)
        
        try:
            self._db.get (id)
            
        except db.DBNotFoundError:
            return False

        return True


    def _idxdel (self, id, txn):
        """ Remove any secondary index belonging to the entry """

        cursor = self._idx.cursor (txn)
        data   = cursor.first ()
        
        while 1:
            if data is None: break
            
            if data [1] == id:
                cursor.delete ()

            data = cursor.next ()
        return


    def _idxadd (self, id, val, txn):
        
        for attribs in val.values ():
            for attrib in attribs:
                
                for idx in attrib.index ():
                    idx = idx.encode ('utf-8')
                    self._idx.put (idx, id, txn = txn)
        return

    
    def _insert (self, key, val, txn):
        
        id  = str (key)
        
        self._idxadd (id, val, txn)

        val = copy.copy (val)
        val.key = key
        
        val = _ps (val)
        
        self._db.put (id, val, txn = txn)
        return id


    def query (self, word, name = None):

        txn = self._env.txn_begin ()

        rs = self.rs.add (name, txn = txn)
        
        cursor = self._idx.cursor ()

        try:
            data = cursor.set (word.encode ('utf-8'))
            
        except db.DBNotFoundError:
            return rs
        
        while 1:
            if data is None: break

            rs.add (Store.Key (data [1]), txn = txn)
            data = cursor.next_dup ()

        txn.commit ()

        return rs
    
    
    def __getitem__ (self, key):
        
        return _pl (self._db.get (str (key)))

    def __iter__ (self):
        
        return DBIter (self._db.cursor ())

    def itervalues (self):
        
        return DBIterValues (self._db.cursor ())
    
    def iterkeys (self):
        
        return DBIter (self._db.cursor ())
    
    def iteritems (self):
        
        return DBIterItems (self._db.cursor ())


    
def dbdestroy (path, nobackup = False):
    shutil.rmtree (path + '.db')
    return

    
def dbcreate (path, schema):
    
    return Database (path   = path + '.db',
                     schema = schema, create = True)


def dbopen (path):

    try:
        return Database (path = path + '.db', create = False)
    
    except db.DBNoSuchFileError, msg:
        raise Store.StoreError (_("cannot open '%s': %s") % (
            path, msg))
                                
