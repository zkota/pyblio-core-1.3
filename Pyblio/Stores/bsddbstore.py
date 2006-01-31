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
Store implementation on top of Berkeley DB (>= 4.1)

This store is suitable for large databases, or for cases where the
startup time is more important.
"""


# Tables in use:
# 
# * database/entries [HASH]
# 
#   key:   string value of an entry key
#   value: Store.Record as a pickled object
# 
# * database/meta [HASH]
# 
#   key:   a meta parameter (next available key,...)
#   value: its value
# 
# * database/enum [HASH]
# 
#   key:   id of the enum
#   value: pickled dict containing the values
# 
# * index/full [HASH / DUP]
# 
#   key:   the indexed value
#   value: the entry that contains the value
# 
# * resultset/<id> [HASH]
# 
#   key:   string value of the entry's key
#   value: no meaning
# 
# * view/<id> [BTREE / RECNUM]
# 
#   key:   field on which we sort
#   value: key from which the field is taken
# 

from gettext import gettext as _

import os, shutil, copy, sys, traceback, string, weakref

import cPickle as pickle

# Python ships the bsddb module as 'bsddb', whereas when fetched as a
# standalone package it is named 'bsddb3'. For the moment, we need a
# version that is not yet shipped.

def _numver (txt):
    v = [ int (x) for x in txt.split ('.') ]
    v = v + [0] * (5 - len (v))

    return tuple (v)

_REQUIRED = (4,3,3,0,0)

def _checkver (module):
    version = _numver (module.__version__)
    
    if version < _REQUIRED:
        raise ImportError ('bsddb is too old (%s instead of %s)' % (version, _REQUIRED))

    return module.db
    
try:
    import bsddb3
    db = _checkver (bsddb3)
    
except ImportError, msg:

    import bsddb
    db = _checkver (bsddb)

from Pyblio import Store, Schema, Callback, Attribute, Exceptions, Tools, Query, Sort

_pl = pickle.loads
_ps = pickle.dumps

# --------------------------------------------------

def _idxdel (_idx, id, txn):
    """ Remove any secondary index belonging to the entry """

    cursor = _idx.cursor (txn)
    data   = cursor.first ()

    while 1:
        if data is None: break

        if data [1] == id:
            cursor.delete ()

        data = cursor.next ()

    cursor.close ()
    return


# --------------------------------------------------

class RSDB (object):

    """ Virtual result set that loops over the full database """

    def __init__ (self, _db, _env, _meta):

        self.id  = 0
        
        self._db   = _db
        self._env  = _env
        self._meta = _meta

        self._views = []
        return
    
    def itervalues (self):
        c = self._db.cursor ()
        d = c.first ()
        
        while d:
            yield _pl (d [1])
            d = c.next ()
        return
    
    def iterkeys (self):
        
        c = self._db.cursor ()
        d = c.first ()
        
        while d:
            yield Store.Key (d [0])
            d = c.next ()

        return

    __iter__ = iterkeys
    
    
    def iteritems (self):
        c = self._db.cursor ()
        d = c.first ()
        
        while d:
            yield Store.Key (d [0]), _pl (d [1])
            d = c.next ()

        return

    def __len__ (self):

        return self._db.stat () ['nkeys']


    def view (self, criterion):

        v = View (self._db, self._env, self._meta,
                  self, criterion)

        self._views.append (weakref.ref (v))
        
        return v

    def _add (self, e, txn):
        
        for vref in [] + self._views:
            v = vref ()

            if v is None:
                self._views.remove (vref)
                continue

            v._add (e, txn)
        return

    def _delete (self, key, txn):

        # Update the views of the result set

        for vref in [] + self._views:
            v = vref ()

            if v is None:
                self._views.remove (vref)
                continue

            v._del (key, txn)

        return

    def _update (self, k, val, txn):
        
        # Update the views of the result set

        for vref in [] + self._views:
            v = vref ()

            if v is None:
                self._views.remove (vref)
                continue

            v._del (k, txn)
            v._add (val, txn)
        return
    
# --------------------------------------------------

def _compare (a, b):
    # orders the keys according to the criterion determined by cmp_key
    # (). As the binary tree does not allow for multiple identical
    # keys, use the records key to compute a strict order.

    try:
        (a, ka), (b, kb) = [ x.split ('\0') for x in (a, b) ]
        r = Sort.compare (_pl (a), _pl (b))

    except: return 0
    
    if r: return r
    return cmp (ka, kb)

class View (Store.View):

    def __init__ (self, _db, _env, _meta, rs, criterion, txn = None):

        self._db   = _db
        self._env  = _env
        self._meta = _meta
        self._crit = criterion
        self._id   = None

        # Create the new view on top of the result set
        txn = self._env.txn_begin (txn)

        try:

            # get a fresh view index
            serial, meta, revert = _pl (self._meta.get ('view', txn = txn))

            meta [serial] = rs.id
            
            info = revert.get (rs.id, {})
            info [serial] = self._crit
            revert [rs.id]  = info

            self._meta.put ('view', _ps ((serial + 1, meta, revert)), txn = txn)

            # create the new view
            
            self._v = db.DB (self._env)
            self._v.set_flags (db.DB_RECNUM)
            self._v.set_bt_compare (_compare)
            
            self._v.open ('view', str (serial), db.DB_BTREE, db.DB_CREATE, txn = txn)

            # fill the view with the current content of the result set
            for e in rs.itervalues (): self._add (e, txn)
            
        except:
            txn.abort ()
            raise

        self._id = serial
        
        txn.commit ()
        return

    def iterkeys (self):

        c = self._v.cursor ()
        d = c.first ()
        
        while d:
            key = d [1]
            yield Store.Key (key)

            d = c.next ()
            
        return

    __iter__ = iterkeys

    def iteritems (self):

        c = self._v.cursor ()
        d = c.first ()
        
        while d:
            key = d [1]
            yield Store.Key (key), _pl (self._db.get (key))

            d = c.next ()
            
        return

    def itervalues (self):

        c = self._v.cursor ()
        d = c.first ()
        
        while d:
            key = d [1]
            yield _pl (self._db.get (key))

            d = c.next ()
        return

    def index(self, key):
        c = self._v.cursor()
        e = _pl(self._db.get(str(key)))

        c.set(self._make_key(e))
        return c.get_recno() - 1
    
    def __getitem__ (self, idx):
        data = self._v.get (idx + 1)

        if data is None:
            raise IndexError ('no such index: %d' % idx)
        return Store.Key (data [1])

    
    def __len__ (self):
        return self._v.stat () ['nkeys']

        
    def __del__ (self):

        if self._id is None: return
        
        txn = self._env.txn_begin ()

        try:
            # remove oneself from the meta list
            (serial, meta, revert) = _pl (self._meta.get ('view', txn = txn))

            rs = meta [self._id]
            
            del revert [rs] [self._id]
            del meta [self._id]

            self._meta.put ('view', _ps ((serial, meta, revert)), txn = txn)
            
            self._v.close ()
            
            db.DB (self._env).remove ('view', str (self._id))

        except:
            # exceptions in __del__ methods are not reported by default
            etype, value, tb = sys.exc_info ()
            traceback.print_exception (etype, value, tb)
            
            txn.abort ()
            raise

        txn.commit ()
        return

    def _make_key (self, e):
        # In order to store multiple values in a DB_RECNUM BTree, it
        # is necessary to "cheat" a bit, and disambiguate between the
        # duplicates; this is done by appending the entry key to the
        # value, separated by null bytes

        return _ps (self._crit.cmp_key (e)) + '\0%d' % e.key

    def _add (self, e, txn):
        
        self._v.put (self._make_key (e), str (e.key), txn = txn)
        return

    def _del (self, k, txn):

        # To remove an entry, we have to assume the way we compute the
        # sorting key has not changed since it has been created. It
        # should be the case, because the update of the result sets
        # and views is performed as the initial step of a record
        # update.
        e = _pl (self._db.get (str (k), txn = txn))

        self._v.delete (self._make_key (e), txn = txn)
        return

    
# --------------------------------------------------

class ResultSet (Store.ResultSet, Callback.Publisher):

    def __init__ (self, _db, _env, _meta, _idx,
                  id, permanent = False, txn = None):

        Callback.Publisher.__init__ (self)
        
        # RS id as a string and as an integer
        self.id  = id
        self._id = str (id)
        
        self._name = None

        self._db   = _db
        self._env  = _env
        self._meta = _meta
        self._idx  = _idx
        
        self._permanent = permanent

        self._rs = db.DB (self._env)
        self._rs.open ('resultset', self._id, db.DB_HASH,
                       db.DB_CREATE, txn = txn)

        self._views = []
        return

    def _name_set (self, name):

        txn = self._env.txn_begin ()

        try:
            (rsid, avail) = _pl (self._meta.get ('rs', txn = txn))

            if avail.has_key (self.id):
                avail [self.id] = (name, self._permanent)
        
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


    def iterkeys (self):
        c = self._rs.cursor ()
        d = c.first ()
        
        while d:
            key = d [0]
            yield Store.Key (key)

            d = c.next ()
            
        return

    __iter__ = iterkeys
    

    def itervalues (self):
        c = self._rs.cursor ()
        d = c.first ()
        
        while d:
            key = d [0]

            k = Store.Key (key)
            yield _pl (self._db.get (key))

            d = c.next ()
        
        return

    
    def iteritems (self):
        c = self._rs.cursor ()
        d = c.first ()
        
        while d:
            key = d [0]

            k = Store.Key (key)
            yield k, _pl (self._db.get (key))

            d = c.next ()
        
        return


    def add (self, k, txn = None):

        if not isinstance (k, Store.Key):
            raise ValueError ('the key must be a Store.Key, not %s' % `k`)

        k = str (k)
        
        txn = self._env.txn_begin (txn)

        try:
            e = _pl (self._db.get (k, txn = txn))
            
            self._rs.put (k, '', txn = txn)

            # Update the views of the result set
            
            for vref in [] + self._views:
                v = vref ()
                if v is None:
                    self._views.remove (vref)
                    continue

                v._add (e, txn)
                
        except:
            txn.abort ()
            raise

        txn.commit ()
        return

    def __delitem__ (self, k, txn = None):

        txn = self._env.txn_begin (txn)

        try:

            try:
                self._rs.delete (str (k), txn = txn)

            except db.DBNotFoundError:
                raise KeyError ('unknown key %s' % str (k))

            # Update the views of the result set
            
            for vref in [] + self._views:
                v = vref ()
                
                if v is None:
                    self._views.remove (vref)
                    continue

                v._del (k, txn)

        except KeyError:
            txn.abort ()
            raise
        
        except:
            etype, value, tb = sys.exc_info ()
            traceback.print_exception (etype, value, tb)

            txn.abort ()
            raise

        txn.commit ()
        return


    def has_key (self, k):

        return self._rs.get (str (k)) is not None


    def view (self, criterion):

        v = View (self._db, self._env, self._meta,
                  self, criterion)

        # keep a weakref for easy updating of the view
        self._views.append (weakref.ref (v))
        
        return v
    

    def __del__ (self):
        if self._permanent: return

        txn = self._env.txn_begin ()

        try:
            # remove oneself from the meta list
            (rsid, avail) = _pl (self._meta.get ('rs', txn = txn))

            if avail.has_key (self.id):
                
                del avail [self.id]
                self._meta.put ('rs', _ps ((rsid, avail)), txn = txn)

                self._rs.close ()

                db.DB (self._env).remove ('resultset', self._id)
                
        except:
            # exceptions in __del__ methods are not reported by default
            etype, value, tb = sys.exc_info ()
            traceback.print_exception (etype, value, tb)
            
            txn.abort ()
            raise

        txn.commit ()
        return

    def destroy(self):
        txn = self._env.txn_begin ()
        
        for k in self:
            k = str(k)
            
            _idxdel(self._idx, k, txn)
            self._db.delete (k, txn)

        txn.commit ()
        return

            
    def __len__ (self):
        return self._rs.stat () ['nkeys']


    def _on_update (self, k, val, txn):
        
        # Update the views of the result set

        for vref in [] + self._views:
            v = vref ()

            if v is None:
                self._views.remove (vref)
                continue

            v._del (k, txn)
            v._add (val, txn)
        return

    
    def _on_delete (self, key, txn = None):

        try:
            self.__delitem__ (key, txn)
            
        except KeyError:
            pass

        return
    

class ResultSetStore (dict, Store.ResultSetStore, Callback.Publisher):

    def __init__ (self, _db, _env, _meta, _idx, txn):

        Callback.Publisher.__init__ (self)

        self._db   = _db
        self._env  = _env
        self._meta = _meta
        self._idx  = _idx
        
        (rsid, avail) = _pl (self._meta.get ('rs', txn = txn))

        txn = self._env.txn_begin (parent = txn)

        try:
            # initialize with the existing result sets
            for rsid, data in avail.items ():
                name, status = data
            
                rs = ResultSet(self._db, self._env, self._meta, self._idx,
                               rsid, status, txn = txn)
                rs._name = name

                self.register ('item-delete', rs._on_delete)

                # assume some non-permanent result sets might still exist
                if status: self [rsid] = rs

            txn.commit ()

        except:
            txn.abort ()
            raise
        
        return
    
    def _close (self):

        self._rs.close ()
        return


    def __delitem__ (self, k):

        rs = self [k]
        rs._permanent = False

        txn = self._env.txn_begin ()

        try:
            # get the rs dict
            (last, avail) = _pl (self._meta.get ('rs', txn = txn))

            # Avail contains the name of the RS, which is initially
            # None, and the state (permanent / not permanent)
            if avail.has_key (rs.id):
                avail [rs.id] = (rs._name, False)
            
            self._meta.put ('rs', _ps ((last, avail)), txn = txn)

        except:
            txn.abort ()
            raise

        txn.commit ()
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
            
            # Avail contains the name of the RS, which is initially
            # None, and the state (permanent / not permanent)
            avail [rsid] = (None, permanent)
            
            self._meta.put ('rs', _ps ((last, avail)), txn = txn)
            
            rs = ResultSet (self._db, self._env, self._meta, self._idx,
                            rsid, permanent, txn = txn)
            
        except:
            txn.abort ()
            raise
        
        txn.commit ()

        if permanent: self [rsid] = rs

        self.register ('item-delete', rs._on_delete)
        self.register ('item-update', rs._on_update)
        
        return rs

    def _on_delete (self, k, trn):

        self.emit ('item-delete', k, trn)
        return

    def _on_update (self, k, val, trn):

        self.emit ('item-update', k, val, trn)
        return

    
# --------------------------------------------------

class TxoGroup (Store.TxoGroup, Callback.Publisher):


    def __init__ (self, env, enum, group):

        Callback.Publisher.__init__ (self)

        self._env  = env
        self._enum = enum
        
        self._group = group

        self._byname = {}

        for k in self:
            v = self [k]
            
            try: self._byname [v.names ['C']] = v.id
            except KeyError: pass
            
        return

    def _check (self, item):
    
        if item.parent is not None:

            try:
                i = self [item.parent]

            except KeyError:
                raise Exceptions.ConstraintError \
                      (_('txo has unknown parent %s') % `item.parent`)

        return

    
    def add (self, item, key = None):

        self._check (item)
        
        txn = self._env.txn_begin ()

        try:
            v = self._enum.get (self._group, txn = txn)
            
            vid, data = _pl (v)
            vid, key  = Tools.id_make (vid, key)

            v = copy.deepcopy (item)
            v.id    = key
            v.group = self._group
            
            data [key] = v

            try: self._byname [v.names ['C']] = v.id
            except KeyError: pass
            
            self._enum.put (self._group, _ps ((vid, data)), txn = txn)

        except:
            txn.abort ()
            raise

        txn.commit ()
        
        return key

    def byname (self, name):
        i = self._byname [name]
        return self [i]

    def keys (self):

        return _pl (self._enum.get (self._group)) [1].keys ()

    def values (self):

        return _pl (self._enum.get (self._group)) [1].values ()
        

    def __setitem__ (self, key, item):

        self._check (item)
        
        try:
            i = self [key]
            
        except KeyError:
            raise KeyError (_('invalid txo key %s') % `key`)
        
        txn = self._env.txn_begin ()

        try:
            v = self._enum.get (self._group, txn = txn)
            
            vid, data = _pl (v)

            v = copy.deepcopy (item)
            v.id    = key
            v.group = self._group
            
            data [key] = v

            try: self._byname [v.names ['C']] = v.id
            except KeyError: pass
        
            self._enum.put (self._group, _ps ((vid, data)), txn = txn)

        except:
            txn.abort ()
            raise

        txn.commit ()
        return
    
    def __delitem__ (self, k):

        for v in self.values ():

            if v.parent == k:
                raise Exceptions.ConstraintError \
                      (_('txo %s is parent of %s') % (
                    `k`, `v.id`))
        
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

    def __iter__ (self):

        return iter (self.keys ())

    def __getitem__ (self, k):
        v = self._enum.get (self._group)

        return _pl (v) [1] [k]



class TxoStore (Store.TxoStore, Callback.Publisher):

    def __init__ (self, env, txn):

        Callback.Publisher.__init__ (self)

        self._env = env

        self._enum = db.DB (self._env)
        self._enum.open ('database', 'enum',
                         db.DB_HASH, db.DB_CREATE, txn = txn)
        return

    def _close (self):

        self._enum.close ()
        return
    
    
    def __getitem__ (self, group):

        g = TxoGroup (self._env, self._enum, group)
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

    
    def _add (self, group):

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
        
        g = TxoGroup (self._env, self._enum, group)
        g.register ('delete', self._on_delete)
        
        return g
    

# --------------------------------------------------
    
class Database (Query.Queryable, Store.Database, Callback.Publisher):
    """ A Pyblio database stored in a Berkeley DB engine """
    
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
            self._db.open ('database', 'entries', db.DB_HASH, flag, txn = txn)

            # DB with meta informations
            self._meta  = db.DB (self._env)
            self._meta.open ('database', 'meta', db.DB_HASH, flag, txn = txn)

            if create:
                self._schema = schema
                self._meta.put ('schema', _ps (schema), txn = txn)
                self._meta.put ('rs', _ps ((1, {})), txn = txn)
                self._meta.put ('serial', '1', txn = txn)
                self._meta.put ('view', _ps ((1, {}, {})), txn = txn)
                
            else:
                self._schema = _pl (self._meta.get ('schema', txn = txn))

            # Full text indexing DB
            self._idx = db.DB (self._env)
            self._idx.set_flags (db.DB_DUP)
            self._idx.open ('index', 'full', db.DB_HASH, flag, txn = txn)

            # Result sets handler
            self.rs = ResultSetStore (self._db, self._env, self._meta, self._idx, txn)
            self.register ('delete', self.rs._on_delete)
            self.register ('update', self.rs._on_update)

            # Store for Txo values
            self.txo = TxoStore (self._env, txn)
            self.txo.register ('delete', self._txo_use_check)


            if create and schema:
                self._txo_create ()
            
        except:
            txn.abort ()
            raise
        
        txn.commit ()

        # Result set containing the full db
        self._entries_rs = RSDB (self._db, self._env, self._meta)

        self.register ('add',    self._entries_rs._add)
        self.register ('delete', self._entries_rs._delete)
        self.register ('update', self._entries_rs._update)
        
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


    def add (self, val, key = None):

        val = self.validate (val)

        # Be careful to always point after the last serial id used.
        txn = self._env.txn_begin ()

        try:
            serial = int (self._meta.get ('serial', txn = txn))

            serial, key = Tools.id_make (serial, key)
            
            self._meta.put ('serial', str (serial), txn = txn)

            key = Store.Key (key)
            val.key = key
            
            self._insert (key, val, txn)

            self.emit ('add', val, txn)
            
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
            # Start by doing the update in the external tables, which
            # might still want to access the previous version
            self.emit ('update', key, val, txn)
            
            _idxdel (self._idx, str (key), txn)
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
            # Start by cleaning up dependencies, as they might wish to
            # access the item a last time.
            self.emit ('delete', key, txn)

            # Then, remove the index and entry itself
            _idxdel (self._idx, id, txn)
            self._db.delete (id, txn)

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


    def _q_anyword (self, query, rs):

        word = query.word.lower ()

        txn = self._env.txn_begin ()

        try:
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
    

    def _q_and (self, query, permanent):

        # BSDDB allows to remove the item under the cursor, therefore
        # we do not need to use three result sets.
        
        ra = self._q_run (query.a, permanent)
        rb = self._q_run (query.b, False)

        for k in ra:
            if not rb.has_key (k): del ra [k]

        return ra
        

    
    def __getitem__ (self, key):
        
        return _pl (self._db.get (str (key)))


    def entries_get (self):

        return self._entries_rs

    entries = property (entries_get)

    


    
def dbdestroy (path, nobackup = False):
    # sanity checks
    if not os.path.isdir (path):
        raise ValueError ('%s is not a directory' % path)

    if not os.path.exists (os.path.join (path, 'database')):
        raise ValueError ('%s is not a pybliographer database' % path)
    
    shutil.rmtree (path)
    return

    
def dbcreate (path, schema):
    
    return Database (path   = path,
                     schema = schema, create = True)


def dbopen (path):

    try:
        return Database (path = path, create = False)
    
    except db.DBNoSuchFileError, msg:
        raise Store.StoreError (_("cannot open '%s': %s") % (
            path, msg))
                                

def dbimport (target, source):

    db = Database (path   = target,
                   schema = None, create = True)


    try:
        db.xmlread (open (source))

    except IOError, msg:

        dbdestroy (target)
        raise Store.StoreError (_("cannot open '%s': %s") % (file, msg))

    return db

description = _("Berkeley DB storage")

