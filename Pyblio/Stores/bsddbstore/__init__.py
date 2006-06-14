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
# * resultset/sets [HASH]
# 
#   key:   resultset id
#   value: a serialized boolean numpy array containing the records
# 
# * view/<id> [BTREE / RECNUM]
# 
#   key:   field on which we sort
#   value: key from which the field is taken
# 

from gettext import gettext as _

import os, shutil, copy, sys, traceback, string, weakref
from sets import Set

import cPickle as pickle
import logging

log = logging.getLogger('pyblio.stores.bsddb')

from Pyblio.Arrays import KeyArray, match_arrays


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

def _idxadd(_idx, id, words, txn):
    """ Mark id as matching all the words. """
    sid = str(id)

    f, b = _idx

    bw = Set([w.encode('utf-8') for w in words])

    for word in bw:
        # Forward link, from word to record
        a = KeyArray(s=f.get(word))
        a.add(id)

        f.put(word, a.tostring())
        
    b.put(sid, _ps(bw))
    return


def _idxdel(_idx, id, txn):
    """ Remove any secondary index belonging to the entry """
    txn = None

    sid = str(id)
    
    f, b = _idx

    try:
        bw = _pl(b.get(sid))
    except TypeError:
        bw = Set()

    b.delete(sid)
    
    for word in bw:
        a = KeyArray(s=f.get(word))
        try:
            del a[id]
            f.put(word, a.tostring())
        except IndexError:
            pass

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
        txn = self._env.txn_begin(txn)

        try:

            # get a fresh view index
            serial, meta, revert = _pl (self._meta.get ('view', txn = txn))

            meta [serial] = rs.id
            
            info = revert.get (rs.id, {})
            info [serial] = self._crit
            revert [rs.id]  = info

            self._meta.put ('view', _ps ((serial + 1, meta, revert)), txn = txn)

            # create the new view
            
            self._v = db.DB(self._env.e)
            self._v.set_flags (db.DB_RECNUM)
            self._v.set_bt_compare (_compare)
            
            self._v.open ('view', str (serial), db.DB_BTREE, db.DB_CREATE, txn = txn)

            # fill the view with the current content of the result set
            for e in rs.itervalues (): self._add (e, txn)
            
        except:
            self._env.txn_abort(txn)
            raise

        self._id = serial
        
        self._env.txn_commit(txn)
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
        data = self._v.get(idx + 1)

        if data is None:
            raise IndexError ('no such index: %d' % idx)
        return Store.Key (data [1])

    
    def __len__ (self):
        return self._v.stat () ['nkeys']

        
    def __del__ (self):

        if self._id is None: return
        
        txn = self._env.txn_begin()

        try:
            # remove oneself from the meta list
            (serial, meta, revert) = _pl (self._meta.get ('view', txn = txn))

            rs = meta [self._id]
            
            del revert [rs] [self._id]
            del meta [self._id]

            self._meta.put ('view', _ps ((serial, meta, revert)), txn = txn)
            
            self._v.close ()
            
            db.DB(self._env.e).remove ('view', str (self._id))

        except:
            # exceptions in __del__ methods are not reported by default
            etype, value, tb = sys.exc_info ()
            traceback.print_exception (etype, value, tb)
            
            self._env.txn_abort(txn)
            raise

        self._env.txn_commit(txn)
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
                  rs, id, permanent = False, txn = None):

        Callback.Publisher.__init__ (self)
        
        # RS id as a string and as an integer
        self.id  = id
        self._id = str(id)
        
        self._name = None

        self._db   = _db
        self._env  = _env
        self._meta = _meta
        self._idx  = _idx
        
        self._permanent = permanent

        self._rs = rs

        self._views = []

        # check that the RS already exists
        txn = self._env.txn_begin(txn)

        try:
            a = self._rs.get(self._id, txn=txn)
            if a is None:
                self._rs.put(self._id, _ps(KeyArray()), txn=txn)

        except:
            self._env.txn_abort(txn)
            raise

        self._env.txn_commit(txn)
        return

    def _name_set (self, name):

        txn = self._env.txn_begin()

        try:
            (rsid, avail) = _pl (self._meta.get('rs', txn=txn))

            if avail.has_key (self.id):
                avail [self.id] = (name, self._permanent)
        
            self._meta.put ('rs', _ps ((rsid, avail)), txn = txn)

        except:
            self._env.txn_abort(txn)
            raise

        self._env.txn_commit(txn)
        self._name = name
        
        return

    def _name_get (self):
        return self._name


    name = property (_name_get, _name_set)


    def iterkeys(self):
        a = _pl(self._rs.get(self._id))

        for key, status in enumerate(a.a):
            if status:
                yield Store.Key(key+1)
        return

    __iter__ = iterkeys
    

    def itervalues (self):

        for key in self.iterkeys():
            yield _pl(self._db.get(str(key)))
        
        return

    
    def iteritems (self):
        for key in self.iterkeys():
            yield key, _pl(self._db.get(str(key)))

        return


    def add(self, k, txn=None):

        if not isinstance (k, Store.Key):
            raise ValueError ('the key must be a Store.Key, not %s' % `k`)

        txn = self._env.txn_begin(txn)

        try:
            a = _pl(self._rs.get(self._id, txn=txn))
            a.add(k)
            self._rs.put(self._id, _ps(a), txn=txn)

            # Update the views of the result set
            if self._views:
                e = _pl(self._db.get(str(k), txn=txn))
                
                for vref in self._views[:]:
                    try:
                        vref()._add(e, txn)

                    except AttributeError:
                        self._views.remove(vref)
                
        except:
            self._env.txn_abort(txn)
            raise

        self._env.txn_commit(txn)
        return

    def __delitem__ (self, k, txn = None):

        txn = self._env.txn_begin(txn)

        try:

            a = _pl(self._rs.get(self._id, txn=txn))

            try:
                if not a.a[k-1]:
                    raise KeyError('key %s not in result set' % str(k))

            except IndexError:
                raise KeyError('key %s not in result set' % str(k))

            del a[k]

            self._rs.put(self._id, _ps(a), txn=txn)

            # Update the views of the result set
            for vref in [] + self._views:
                v = vref ()
                
                if v is None:
                    self._views.remove (vref)
                    continue

                v._del (k, txn)

        except KeyError:
            self._env.txn_abort(txn)
            raise
        
        except:
            etype, value, tb = sys.exc_info ()
            traceback.print_exception (etype, value, tb)

            self._env.txn_abort(txn)
            raise

        self._env.txn_commit(txn)
        return


    def __contains__(self, k):

        try:
            return _pl(self._rs.get(self._id)).a[k-1]

        except IndexError:
            return False

        
    def has_key (self, k):
        return k in self


    def view (self, criterion):

        v = View (self._db, self._env, self._meta,
                  self, criterion)

        # keep a weakref for easy updating of the view
        self._views.append (weakref.ref (v))
        
        return v
    

    def __del__ (self):
        if self._permanent:
            return

        txn = self._env.txn_begin()

        try:
            # remove oneself from the meta list
            (rsid, avail) = _pl (self._meta.get ('rs', txn = txn))

            if avail.has_key(self.id):
                del avail [self.id]
                self._meta.put ('rs', _ps ((rsid, avail)), txn = txn)

                self._rs.delete(self._id, txn=txn)
                
        except:
            # exceptions in __del__ methods are not reported by default
            etype, value, tb = sys.exc_info ()
            traceback.print_exception (etype, value, tb)
            
            self._env.txn_abort(txn)
            raise

        self._env.txn_commit(txn)
        return

    def destroy(self):
        txn = self._env.txn_begin()
        
        for k in self:
            _idxdel(self._idx, k, txn)
            self._db.delete (str(k), txn)

        self._env.txn_commit(txn)
        return

            
    def __len__ (self):
        return len(_pl(self._rs.get(self._id)))


    def _from_array(self, a):
        txn = self._env.txn_begin()

        try:
            self._rs.put(self._id, _ps(a), txn=txn)

        except:
            self._env.txn_abort(txn)
            raise

        self._env.txn_commit(txn)
        return
        

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


class ResultSetStore(dict, Store.ResultSetStore, Callback.Publisher):

    def __init__ (self, _db, _env, _meta, _idx, txn):

        Callback.Publisher.__init__ (self)

        self._db   = _db
        self._env  = _env
        self._meta = _meta
        self._idx  = _idx

        (rsid, avail) = _pl(self._meta.get('rs', txn=txn))

        txn = self._env.txn_begin(parent=txn)

        try:

            self._rs = db.DB(self._env.e)
            self._rs.open('resultset', 'sets', db.DB_HASH,
                          db.DB_CREATE, txn=txn)
        
            # initialize with the existing result sets
            for rsid, data in avail.items():
                name, status = data
            
                rs = ResultSet(self._db, self._env, self._meta, self._idx,
                               self._rs, rsid, status, txn=txn)
                rs._name = name

                self.register('item-delete', rs._on_delete)
                self.register('item-update', rs._on_update)

                # assume some non-permanent result sets might still exist
                if status:
                    self[rsid] = rs

            self._env.txn_commit(txn)

        except:
            self._env.txn_abort(txn)
            raise
        
        return
    
    def _close (self):

        self._rs.close()
        return

    def _save (self):
        self._rs.sync()
        return


    def __delitem__ (self, k):

        rs = self [k]
        rs._permanent = False

        txn = self._env.txn_begin ()

        try:
            # get the rs dict
            (last, avail) = _pl(self._meta.get('rs', txn = txn))

            # Avail contains the name of the RS, which is initially
            # None, and the state (permanent / not permanent)
            if avail.has_key (rs.id):
                avail [rs.id] = (rs._name, False)
            
            self._meta.put('rs', _ps ((last, avail)), txn = txn)

        except:
            self._env.txn_abort(txn)
            raise

        self._env.txn_commit(txn)
        dict.__delitem__ (self, k)
        return


    def __iter__ (self):
        return self.itervalues ()


    def add(self, permanent=False, rsid=None, txn=None):
        """ Create an empty result set """

        txn = self._env.txn_begin (parent = txn)

        try:
            # get the next rs id
            (last, avail) = _pl (self._meta.get('rs', txn=txn))
            (last, rsid)  = Tools.id_make(last, rsid)
            
            # Avail contains the name of the RS, which is initially
            # None, and the state (permanent / not permanent)
            avail[rsid] = (None, permanent)
            
            self._meta.put('rs', _ps((last, avail)), txn=txn)
            
            rs = ResultSet(self._db, self._env, self._meta, self._idx,
                           self._rs, rsid, permanent, txn=txn)
            
        except:
            self._env.txn_abort(txn)
            raise
        
        self._env.txn_commit(txn)

        if permanent:
            self[rsid] = rs

        self.register('item-delete', rs._on_delete)
        self.register('item-update', rs._on_update)
        
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

        Callback.Publisher.__init__(self)

        self._env  = env
        self._enum = enum
        
        self._group = group

        self._byname = {}

        for k in self:
            v = self[k]
            
            try:
                self._byname[v.names['C']] = v.id
            except KeyError:
                pass
            
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
            self._env.txn_abort(txn)
            raise

        self._env.txn_commit(txn)
        
        return key

    def byname (self, name):
        i = self._byname [name]
        return self [i]

    def keys (self):
        return _pl (self._enum.get (self._group)) [1].keys ()

    def values (self):
        return _pl (self._enum.get (self._group)) [1].values ()
        
    def items(self):
        return _pl(self._enum.get(self._group))[1].items()
        

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
            self._env.txn_abort(txn)
            raise

        self._env.txn_commit(txn)
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
            self._env.txn_abort(txn)
            raise
        
        self._env.txn_commit(txn)
        return

    def __iter__ (self):

        return iter (self.keys ())

    def __getitem__ (self, k):
        v = self._enum.get(self._group)
        return _pl(v)[1][k]



class TxoStore (Store.TxoStore, Callback.Publisher):

    def __init__ (self, env, txn):

        Callback.Publisher.__init__ (self)

        self._env = env

        self._enum = db.DB(self._env.e)
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
            self._env.txn_abort(txn)
            raise

        self._env.txn_commit(txn)
        
        if v is not None:
            raise Exceptions.ConstraintError (_('group %s exists') % `group`)
        
        g = TxoGroup (self._env, self._enum, group)
        g.register ('delete', self._on_delete)
        
        return g
    

# --------------------------------------------------

class _TxnEnv(object):
    """ I pretend to be a DBEnv, with overloadable txn management
    functions. I work when transactions are enabled. """
    
    def __init__(self, *args, **kargs):
        self.e = db.DBEnv(*args, **kargs)

    def txn_begin(self, *args, **kargs):
        return self.e.txn_begin(*args, **kargs)
    
    def open(self, *args, **kargs):
        return self.e.open(*args, **kargs)
    
    def txn_commit(self, txn):
        txn.commit()
    
    def txn_abort(self, txn):
        txn.abort()
    

class _NoTxnEnv(_TxnEnv):
    """ I pretend to be a DBEnv, with overloadable txn management
    functions. I work when transactions are disabled. """

    def txn_begin(self, *args, **kargs):
        return None
    
    def txn_commit(self, txn):
        return
    
    def txn_abort(self, txn):
        return

_units = {
    'k': 1024,
    'M': 1024 ** 2,
    'G': 1024 ** 3,
    }


class Database(Query.Queryable, Store.Database, Callback.Publisher):
    """ A Pyblio database stored in a Berkeley DB engine """
    
    def __init__ (self, path, schema=None, create=False, args={}):

        Callback.Publisher.__init__(self)

        self._use_txn = args.get('transactions', True)

        # Instantiate the proper environment (yes, this could be done
        # with an if :-))
        self._env = {True:  _TxnEnv,
                     False: _NoTxnEnv}[self._use_txn]()

        cache = args.get('cachesize', '10M')

        if cache[-1] in _units.keys():
            cache = int(cache[:-1]) * _units[cache[-1]]
        else:
            cache = int(cache)

        gbytes = cache / _units['G']
        bytes  = cache - (gbytes * _units['G'])
        
        self._env.e.set_cachesize(gbytes, bytes)

        log.debug('environment configured with (%d Gb, %d b) cache, transactions: %s' % (
            gbytes, bytes, str(self._use_txn)))
        
        if create:
            try:
                os.mkdir(path)

            except OSError, msg:
                raise Store.StoreError(_("cannot create '%s': %s") % (
                    path, msg))
            
            flag = db.DB_CREATE
            oflag = db.DB_CREATE | db.DB_INIT_MPOOL

            if self._use_txn:
                oflag |= db.DB_INIT_TXN
            
            self._env.open(path, oflag)

        else:
            flag = 0
            oflag = db.DB_INIT_MPOOL

            if self._use_txn:
                oflag |= db.DB_INIT_TXN
                
            self._env.open(path, oflag)

        self._path = path

        txn = self._env.txn_begin()

        try:
            # DB containing the actual entries
            self._db = db.DB(self._env.e)
            self._db.open('database', 'entries', db.DB_HASH, flag, txn=txn)

            # DB with meta informations
            self._meta  = db.DB(self._env.e)
            self._meta.open('database', 'meta', db.DB_HASH, flag, txn=txn)

            if create:
                self._schema = schema
                self._meta.put('schema', _ps (schema), txn=txn)
                self._meta.put('rs', _ps ((1, {})), txn=txn)
                self._meta.put('view', _ps ((1, {}, {})), txn=txn)
                self._meta.put('full', KeyArray().tostring(), txn=txn)
                self._meta.put('serial', '1', txn=txn)
                
                self._header_set(None, txn)

            else:
                self._schema = _pl(self._meta.get('schema', txn = txn))

            # Full text indexes

            # Forward index: for each word as a key, return an array
            # of matches
            f = db.DB(self._env.e)
            f.open('index', 'f', db.DB_BTREE, flag)

            # Backward index: for each record, list the words it matches
            b = db.DB(self._env.e)
            b.open('index', 'b', db.DB_BTREE, flag)

            self._idx = (f, b)
            
            # Result sets handler
            self.rs = ResultSetStore(self._db, self._env, self._meta, self._idx, txn)
            self.register ('delete', self.rs._on_delete)
            self.register ('update', self.rs._on_update)

            # Store for Txo values
            self.txo = TxoStore (self._env, txn)
            self.txo.register ('delete', self._txo_use_check)


            if create and schema:
                self._txo_create ()
            
        except:
            self._env.txn_abort(txn)
            raise
        
        self._env.txn_commit(txn)

        # Result set containing the full db
        self._entries_rs = RSDB(self._db, self._env, self._meta)

        self.register('add',    self._entries_rs._add)
        self.register('delete', self._entries_rs._delete)
        self.register('update', self._entries_rs._update)
        
        return

            
    def _header_get(self):
        return _pl(self._meta.get('header'))

    def _header_set(self, header, txn=None):
        txn = self._env.txn_begin(txn)

        try:
            self._meta.put('header', _ps(header), txn=txn)
        except:
            self._env.txn_abort(txn)
            raise

        self._env.txn_commit(txn)
        return
    
    header = property(_header_get, _header_set)

    def _schema_get (self):
        return self._schema

    def _schema_set (self, schema, txn = None):

        txn = self._env.txn_begin (txn)
        try:
            self._meta.put ('schema', _ps (schema), txn = txn)

        except:
            self._env.txn_abort(txn)
            raise

        self._env.txn_commit(txn)
        self._schema = schema
        return

    schema = property (_schema_get, _schema_set)
    

    def save(self):

        # Flush the databases
        self._db.sync()
        self._meta.sync()
        
        for i in self._idx:
            i.sync()

        self.rs._save()
        return


    def add(self, val, key=None):

        val = self.validate(val)

        # Be careful to always point after the last serial id used.
        txn = self._env.txn_begin()

        try:
            serial = int(self._meta.get('serial', txn=txn))
            full = KeyArray(s=self._meta.get('full', txn=txn))

            serial, key = Tools.id_make(serial, key)
            full.add(key)
            
            self._meta.put('full', full.tostring(), txn=txn)
            self._meta.put('serial', str(serial), txn=txn)
            
            key = Store.Key(key)
            val.key = key
            
            self._insert(key, val, txn)

            self.emit('add', val, txn)
            
        except:
            self._env.txn_abort(txn)
            raise

        self._env.txn_commit(txn)
        
        return key
    

    def __setitem__ (self, key, val):

        assert self.has_key (key), \
               _('entry %s does not exist') % `key`

        val = self.validate (val)

        txn = self._env.txn_begin ()

        try:
            # Start by doing the update in the external tables, which
            # might still want to access the previous version
            self.emit('update', key, val, txn)
            
            _idxdel(self._idx, key, txn)
            self._insert(key, val, txn)

        except:
            etype, value, tb = sys.exc_info ()
            traceback.print_exception (etype, value, tb)

            self._env.txn_abort(txn)
            raise

        self._env.txn_commit(txn)
        return


    def __delitem__ (self, key):
        id = str (key)
        
        txn = self._env.txn_begin ()

        try:
            # Start by cleaning up dependencies, as they might wish to
            # access the item a last time.
            self.emit ('delete', key, txn)

            # Then, remove the index and entry itself
            _idxdel (self._idx, key, txn)
            self._db.delete (id, txn)

            full = KeyArray(s=self._meta.get('full', txn=txn))
            del full[key]
            self._meta.put('full', full.tostring(), txn=txn)
            
        except:
            self._env.txn_abort(txn)
            raise

        self._env.txn_commit(txn)
        return
    

    def has_key (self, k):

        id = str (k)
        
        try:
            self._db.get (id)
            
        except db.DBNotFoundError:
            return False

        return True


    def _idxadd (self, id, val, txn):

        # We need to insert the current record in both the backward
        # and forward indexes.

        def words():
            for attribs in val.values():
                for attrib in attribs:
                
                    for idx in attrib.index():
                        yield idx

        _idxadd(self._idx, id, words(), txn)
        return

    
    def _insert(self, key, val, txn):
        
        id  = str(key)
        
        self._idxadd(key, val, txn)

        val = copy.copy (val)
        val.key = key
        
        val = _ps(val)
        
        self._db.put(id, val, txn=txn)
        return id


    def _q_all(self):
        return KeyArray(s=self._meta.get('full'))


    def _q_anyword(self, query):

        word = query.word.lower().encode('utf-8')
        
        return KeyArray(s=self._idx[0].get(word))


    def _q_to_rs(self, res, permanent):

        rs = self.rs.add(permanent)
        rs._from_array(res)

        return rs

    
    def __getitem__ (self, key):
        return _pl(self._db.get(str(key)))


    def entries_get (self):

        return self._entries_rs

    entries = property (entries_get)

    
    def index(self):
        pass
    

    
def dbdestroy(path, nobackup=False):
    # sanity checks
    if not os.path.isdir (path):
        raise ValueError ('%s is not a directory' % path)

    if not os.path.exists (os.path.join (path, 'database')):
        raise ValueError ('%s is not a pybliographer database' % path)
    
    shutil.rmtree (path)
    return

    
def dbcreate(path, schema, args={}):
    return Database (path=path, schema=schema, create=True, args=args)


def dbopen(path, args={}):

    try:
        return Database(path=path, create=False, args=args)
    
    except db.DBNoSuchFileError, msg:
        raise Store.StoreError (_("cannot open '%s': %s") % (
            path, msg))
                                

def dbimport(target, source, args={}):

    db = Database (path=target, schema=None, create=True, args=args)


    try:
        db.xmlread (open (source))

    except IOError, msg:

        dbdestroy (target)
        raise Store.StoreError (_("cannot open '%s': %s") % (file, msg))

    return db

description = _("Berkeley DB storage")

