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

from Pyblio import Store, Schema

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

        return int (data [0], 16)

class DBIterValues (DBIterBase):
    """ Iterate over the values """
    def _content (self, data):

        return pickle.loads (data [1])

class DBIterItems (DBIterBase):
    """ Iterate over (key, value) pairs """
    def _content (self, data):

        return int (data [0], 16), pickle.loads (data [1])


# --------------------------------------------------

class ResultSet:

    def __init__ (self, env, rs, id, name = None):
        self.name    = name

        self._db = env
        self._rs = rs
        self._id = id
        
        self._cursor = rs.cursor ()
        self._data   = self._cursor.first ()
        return

    def __iter__ (self):
        return self


    def next (self):
        if self._data is None:
            raise StopIteration ()

        data = self._data
        self._data = self._cursor.next ()
        
        return int (data [1], 16)


    def __del__ (self):
        if self.name:
            # This is a long-lived result set
            return

        self._rs.close ()

        _db = db.DB (self._db)
        _db.remove ('rs', self._id)
        return
    
    
# --------------------------------------------------


class EnumStore (Store.EnumStore):


    def __init__ (self, env):

        Store.EnumStore.__init__ (self)

        self._env = env

        self._enum = db.DB (self._env)
        self._enum.open ('pybliographer', 'enum',
                         db.DB_HASH, db.DB_CREATE)
        return

    
    def __getitem__ (self, k):
        v = self._enum.get (k)

        if v is None:
            raise KeyError, _('unknown group %s' % `k`)

        return pickle.loads (v) [1]

    def keys (self):
        k = []
        c = self._enum.cursor ()

        d = c.first ()
        while d:
            key, data = d
            k.append (key)
            
            d = c.next ()

        return k
    
    def add (self, group, item, key = None):

        v = self._enum.get (group)

        if v is None:
            id, data = 1, Store.EnumGroup ()
        else:
            id, data = pickle.loads (v)

        # Key is the key that will be used for the entry, id is
        # the current serial (which can be different)
        if key:
            if key > id: id  = key
        else:
            key = id

        txn = self._env.txn_begin ()

        v = copy.deepcopy (item)
        v.id    = key
        v.group = group
        
        data [key] = v
        
        self._enum.put (group, pickle.dumps ((id + 1, data)))

        txn.commit ()
        
        return key



# --------------------------------------------------
    
class Database (Store.Database):
    """ A Pyblio database stored in a BSD DB3 engine """
    
    def __init__ (self, path, schema = None, create = False):

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

        if create:
            self.schema = schema
            self._meta.put ('schema', pickle.dumps (schema))
            self._meta.put ('rs', '0')
            self._meta.put ('serial', '1')
        else:
            self.schema = pickle.loads (self._meta.get ('schema'))

        # Full text indexing DB
        self._idx = db.DB (self._env)
        self._idx.set_flags (db.DB_DUP)
        self._idx.open ('pybliographer', 'idx', db.DB_HASH, flag)

        # Store for Enumerated values
        self.enum = EnumStore (self._env)

        self.header = None
        return


    def save (self):

        # Flush the databases
        self._db.sync ()
        self._meta.sync ()
        self._idx.sync ()
        return


    def add (self, val, id = None):

        # Be careful to always point after the last serial id used.
        txn = self._env.txn_begin ()

        try:
            serial = int (self._meta.get ('serial'))

            if id:
                if id > serial: serial = id
            else:
                id = serial
            
            self._meta.put ('serial', str (serial + 1))
            
            key = int (self._insert (id, val), 16)

        except:
            txn.abort ()
            raise

        txn.commit ()
        return key
    

    def __setitem__ (self, key, val):

        assert self.has_key (key), \
               _('entry %s does not exist') % `key`

        txn = self._env.txn_begin ()

        try:
            self._idxdel ('%.16x' % key)
            self._insert (key, val)

        except:
            txn.abort ()
            raise

        txn.commit ()
        return


    def __delitem__ (self, key):
        id = '%.16x' % key
        
        txn = self._env.txn_begin ()

        try:
            self._idxdel (id)
            self._db.delete (id)

        except:
            txn.abort ()
            raise

        txn.commit ()
        return
    

    def has_key (self, k):

        id = '%.16x' % k
        
        try:
            self._db.get (id)
            
        except db.DBNotFoundError:
            return False

        return True


    def _idxdel (self, id):
        """ Remove any secondary index belonging to the entry """

        cursor = self._idx.cursor ()
        data   = cursor.first ()
        
        while 1:
            if data is None: break
            
            if data [1] == id:
                cursor.delete ()

            data = cursor.next ()
        return


    def _idxadd (self, id, val):
        
        for attribs in val.values ():
            for attrib in attribs:
                
                for idx in attrib.index ():
                    idx = idx.encode ('utf-8')
                    self._idx.put (idx, id)
        return

    
    def _insert (self, key, val):
        
        id  = '%.16x' % key
        
        self._idxadd (id, val)

        val = copy.copy (val)
        val.key = key
        
        val = pickle.dumps (val)
        
        self._db.put (id, val)
        return id


    def query (self, word, sort, name = None):

        # get the next rs id
        rsid = self._meta.get ('rs')
        self._meta.put ('rs', '%d' % (int (rsid) + 1))
        
        rs = db.DB (self._env)
        rs.open ('rs', rsid, db.DB_BTREE, db.DB_CREATE)
        
        cursor = self._idx.cursor ()

        try:
            data = cursor.set (word.encode ('utf-8'))
            
        except db.DBNotFoundError:
            return ResultSet (self._env, rs, rsid, name)
        
        while 1:
            if data is None: break

            key   = data [1]
            entry = pickle.loads (self._db.get (key))
            
            # Insert the new value in a table according to the sort key
            
            sortkey = entry [sort] [0].sort ().encode ('utf-8')
            rs.put (sortkey, key)

            data = cursor.next_dup ()

        return ResultSet (self._env, rs, rsid, name)
    
    
    def __getitem__ (self, key):
        
        return pickle.loads (self._db.get ('%.16x' % key))

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
                                
