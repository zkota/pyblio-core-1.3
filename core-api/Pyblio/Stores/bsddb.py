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

import os, shutil, copy, sys, traceback

import cPickle as pickle

from bsddb3 import db

from Pyblio import Store, Schema, Callback, Attribute, Exceptions, Tools

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

class RSIter (object):
    def __init__ (self, cursor, id):
        self._id     = id
        self._cursor = cursor
        
        self._cursor.set (self._id + '/')
        return


    def __iter__ (self):
        return self

    
    def next (self):
        data = self._cursor.next ()

        if data is None:
            raise StopIteration ()

        rs, key = data [0].split ('/')
        
        if rs != self._id:
            raise StopIteration ()

        return Store.Key (key)


class ResultSet (Store.ResultSet):

    def __init__ (self, env, meta, rs, id, permanent = None):
        # RS id as a string and as an integer
        self.id  = id
        self._id = str (id)
        
        self._name = None

        # Useful db accesses
        self._env  = env
        self._rs   = rs
        self._meta = meta

        self._permanent = permanent
        return

    def _name_set (self, name):

        txn = self._env.txn_begin ()

        try:
            (rsid, avail) = _pl (self._meta.get ('rs', txn = txn))
        
            avail [int (self._id)] = name
        
            self._meta.put ('rs', _ps ((rsid, avail)), txn = txn)

        except:
            txn.abort ()
            raise

        txn.commit ()
        self._name = name
        
        return

    def _name_get (self):
        return self._name


    name = property (_name_get, _name_set)


    def __iter__ (self):
        cursor = self._rs.cursor ()
        
        return RSIter (cursor, self._id)


    def add (self, k, txn = None):

        txn = self._env.txn_begin (txn)

        try:
            self._rs.put (self._id + '/' + str (k), '', txn = txn)
        except:
            txn.abort ()
            raise

        txn.commit ()
        return

    def __delitem__ (self, k, txn = None):

        txn = self._env.txn_begin (txn)

        try:
            self._rs.delete (self._id + '/' + str (k), txn = txn)
        except:
            txn.abort ()
            raise

        txn.commit ()
        return


    def __del__ (self):
        if self._permanent: return

        txn = self._env.txn_begin ()

        try:
            c = self._rs.cursor (txn = txn)
            c.set (self._id + '/')

            while 1:
                c.delete ()

                d = c.next ()
                if d is None: break

                rs, key = d [0].split ('/')
                if rs != self._id: break

            c.close ()

            # remove oneself from the meta list
            (rsid, avail) = _pl (self._meta.get ('rs', txn = txn))
            
            del avail [int (self._id)]
            
            self._meta.put ('rs', _ps ((rsid, avail)), txn = txn)
            
        except:
            # exceptions in __del__ methods are not reported by default
            etype, value, tb = sys.exc_info ()
            traceback.print_exception (etype, value, tb)
            
            txn.abort ()
            raise

        txn.commit ()
        return


    def _on_delete (self, key, txn = None):

        try:
            self.__delitem__ (key, txn)
            
        except KeyError:
            pass

        return
    

class ResultSetStore (dict, Store.ResultSetStore, Callback.Publisher):

    def __init__ (self, env, meta, txn):

        Callback.Publisher.__init__ (self)
        
        self._env  = env
        self._meta = meta

        self._rs = db.DB (self._env)
        self._rs.open ('pybliographer', 'rs', db.DB_BTREE,
                       db.DB_CREATE, txn = txn)

        (rsid, avail) = _pl (self._meta.get ('rs', txn = txn))

        # initialize with the existing permanent result sets
        for rsid, name in avail.items ():
            rs = ResultSet (self._env, self._meta, self._rs, rsid, True)
            rs._name = name
            
            self [rsid] = rs
        
        return
    
    def _close (self):

        self._rs.close ()
        return


    def __delitem__ (self, k):

        self [k]._permanent = False
        dict.__delitem__ (self, k)
        return


    def __iter__ (self):
        return self.itervalues ()


    def add (self, permanent = False, rsid = None, txn = None):
        """ Create an empty result set """

        txn = self._env.txn_begin (parent = txn)

        try:
            # get the next rs id
            (last, avail) = _pl (self._meta.get ('rs', txn = txn))
            (last, rsid)  = Tools.id_make (last, rsid)
            
            # Avail contains the name of the RS, which is initially None
            avail [rsid] = None
            
            self._meta.put ('rs', _ps ((last, avail)), txn = txn)
            
            srsid = str (rsid) 

            # the result set is simply defined by an entry with its number
            self._rs.put (srsid + '/', '', txn = txn)

        except:
            txn.abort ()
            raise
        
        txn.commit ()

        rs = ResultSet (self._env, self._meta, self._rs, rsid, permanent)
        if permanent: self [rsid] = rs

        self.register ('item-delete', rs._on_delete)
        
        return rs

    def _on_delete (self, k, trn):

        self.emit ('item-delete', k, trn)
        return

    
# --------------------------------------------------

class EnumGroup (Store.EnumGroup, Callback.Publisher):


    def __init__ (self, env, enum, group):

        Callback.Publisher.__init__ (self)

        self._env  = env
        self._enum = enum
        
        self._group = group
        return

    
    def add (self, item, key = None):

        txn = self._env.txn_begin ()

        try:
            v = self._enum.get (self._group, txn = txn)
            
            vid, data = _pl (v)
            vid, key  = Tools.id_make (vid, key)

            v = copy.deepcopy (item)
            v.id    = key
            v.group = self._group
            
            data [key] = v
        
            self._enum.put (self._group, _ps ((vid, data)), txn = txn)

        except:
            txn.abort ()
            raise

        txn.commit ()
        
        return key


    def keys (self):

        return _pl (self._enum.get (self._group)) [1].keys ()

    def values (self):

        return _pl (self._enum.get (self._group)) [1].values ()
        
    
    def __delitem__ (self, k):

        self.emit ('delete', self._group, k)

        txn = self._env.txn_begin ()

        try:
            v = _pl (self._enum.get (self._group, txn = txn))
            del v [1] [k]

            self._enum.put (self._group, _ps (v), txn = txn)

        except:
            txn.abort ()
            raise
        
        txn.commit ()
        return
    

    def __getitem__ (self, k):
        v = self._enum.get (self._group)

        return _pl (v) [1] [k]



class EnumStore (Store.EnumStore, Callback.Publisher):

    def __init__ (self, env, txn):

        Callback.Publisher.__init__ (self)

        self._env = env

        self._enum = db.DB (self._env)
        self._enum.open ('pybliographer', 'enum',
                         db.DB_HASH, db.DB_CREATE, txn = txn)
        return

    def _close (self):

        self._enum.close ()
        return
    
    
    def __getitem__ (self, group):

        g = EnumGroup (self._env, self._enum, group)
        g.register ('delete', self._on_delete)
        
        return g

    def _on_delete (self, g, k):

        self.emit ('delete', g, k)
        return
    

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

        txn = self._env.txn_begin ()
        
        try:
            v = self._enum.get (group, txn = txn)

            if v is None:
                self._enum.put (group, _ps ((1, {})), txn = txn)

        except:
            txn.abort ()
            raise

        txn.commit ()
        
        if v is not None:
            raise Exceptions.ConstraintError (_('group %s exists') % `group`)
        
        g = EnumGroup (self._env, self._enum, group)
        g.register ('delete', self._on_delete)
        
        return g
    

# --------------------------------------------------
    
class Database (Store.Database, Callback.Publisher):
    """ A Pyblio database stored in a BSD DB3 engine """
    
    def __init__ (self, path, schema = None, create = False):

        Callback.Publisher.__init__ (self)
        
        self._env = db.DBEnv ()

        if create:
            try:
                os.mkdir (path)

            except OSError, msg:
                raise Store.StoreError (_("cannot create '%s': %s") % (
                    path, msg))
            
            flag = db.DB_CREATE
            self._env.open (path, db.DB_CREATE | db.DB_INIT_MPOOL | db.DB_INIT_TXN)

        else:
            flag = 0
            self._env.open (path, db.DB_INIT_MPOOL | db.DB_INIT_TXN)

        self._path = path

        txn = self._env.txn_begin ()

        try:
            # DB containing the actual entries
            self._db  = db.DB (self._env)
            self._db.open ('pybliographer', 'db', db.DB_HASH, flag, txn = txn)

            # DB with meta informations
            self._meta  = db.DB (self._env)
            self._meta.open ('pybliographer', 'meta', db.DB_HASH, flag, txn = txn)

            if create:
                self._schema = schema
                self._meta.put ('schema', _ps (schema), txn = txn)
                self._meta.put ('rs', _ps ((1, {})), txn = txn)
                self._meta.put ('serial', '1', txn = txn)
            else:
                self._schema = _pl (self._meta.get ('schema', txn = txn))

            # Result sets handler
            self.rs = ResultSetStore (self._env, self._meta, txn)
            self.register ('delete', self.rs._on_delete)

            # Full text indexing DB
            self._idx = db.DB (self._env)
            self._idx.set_flags (db.DB_DUP)
            self._idx.open ('pybliographer', 'idx', db.DB_HASH, flag, txn = txn)

            # Store for Enumerated values
            self.enum = EnumStore (self._env, txn)
            self.enum.register ('delete', self._enum_use_check)

        except:
            txn.abort ()
            raise
        
        txn.commit ()
        
        # No header in this db yet
        self.header = None
        return

    def _schema_get (self):

        return self._schema

    def _schema_set (self, schema, txn = None):

        txn = self._env.txn_begin (txn)
        try:
            self._meta.put ('schema', _ps (schema), txn = txn)

        except:
            txn.abort ()
            raise

        txn.commit ()
        self._schema = schema
        return

    schema = property (_schema_get, _schema_set)
    

    def save (self):

        # Flush the databases
        self._db.sync ()
        self._meta.sync ()
        self._idx.sync ()
        return

    def __len__ (self):

        return self._db.stat () ['nkeys']
    

    def add (self, val, key = None):

        val = self.validate (val)

        # Be careful to always point after the last serial id used.
        txn = self._env.txn_begin ()

        try:
            serial = int (self._meta.get ('serial', txn = txn))

            serial, key = Tools.id_make (serial, key)
            
            self._meta.put ('serial', str (serial), txn = txn)
            
            key = Store.Key (self._insert (key, val, txn))

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

            self.emit ('delete', key, txn)

        except:
            txn.abort ()
            raise

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

        cursor.close ()
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


    def query (self, word, permanent = False):

        txn = self._env.txn_begin ()

        try:
            rs = self.rs.add (permanent, txn = txn)

            cursor = self._idx.cursor ()

            try:
                data = cursor.set (word.encode ('utf-8'))

            except db.DBNotFoundError:
                txn.commit ()
                return rs

            while 1:
                if data is None: break

                rs.add (Store.Key (data [1]), txn = txn)
                data = cursor.next_dup ()

            cursor.close ()
            
        except:
            txn.abort ()
            raise
        
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
                                

def dbimport (target, source):

    db = Database (path   = target + '.db',
                   schema = None, create = True)

    handler = Store.DatabaseParse (db)

    try:
        handler.parse (source)

    except ValueError, msg:

        dbdestroy (target)
        raise Store.StoreError (_("cannot open '%s': %s") % (file, msg))

    return db
