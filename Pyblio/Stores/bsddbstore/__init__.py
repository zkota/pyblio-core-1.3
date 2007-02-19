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
from Pyblio.Stores import resultset

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

class RSDB(Callback.Publisher):
    """ Virtual result set that loops over the full database"""

    def __init__ (self, _db):
        Callback.Publisher.__init__(self)
        
        self.id  = 0
        self._db = _db

        _db.register('add-item',    self._add)
        _db.register('delete-item', self._delete)
        _db.register('update-item', self._update)
        return
    
    def itervalues (self):
        c = self._db._db.cursor()
        d = c.first()
        
        while d:
            yield _pl(d[1])
            d = c.next()

        c.close()
        return
    
    def iterkeys(self):
        
        c = self._db._db.cursor()
        d = c.first()
        
        while d:
            yield Store.Key(d[0])
            d = c.next()

        c.close()
        return

    __iter__ = iterkeys
    
    def iteritems(self):
        c = self._db._db.cursor()
        d = c.first()
        
        while d:
            yield Store.Key(d[0]), _pl(d[1])
            d = c.next()

        c.close()
        return

    def __len__(self):
        return self._db._db.stat()['nkeys']

    def view(self, criterion):
        return resultset.View(self, criterion)

    def _add(self, k):
        self.emit('add-item', k)
        return

    def _delete(self, k):
        self.emit('delete-item', k)
        return

    def _update(self, k):
        self.emit('update-item', k)
        return
    
# --------------------------------------------------
class ResultSetStore(Store.ResultSetStore):
    def __init__ (self, _db, txn):
        _db.register('delete', self._on_delete_item)

        self._db = weakref.ref(_db)
        txn = _db._env.txn_begin(parent=txn)
        try:
            self._rs = db.DB(_db._env.e)
            self._rs.open('resultset', 'sets', db.DB_HASH, db.DB_CREATE, txn=txn)
            _db._env.txn_commit(txn)
        except:
            _db._env.txn_abort(txn)
            raise
        return
    
    def _close(self):
        self._rs.close()
        return

    def _save(self):
        self._rs.sync()
        return

    def __getitem__(self, k):
        data = self._rs.get(str(k))
        if data is None:
            raise KeyError("unknown resultset %r" % k)
        contents, name = _pl(data)
        rs = resultset.ResultSet(k, self._db(), contents=contents)
        rs.name = name
        return rs
    
    def __delitem__(self, k):
        _db = self._db()
        txn = _db._env.txn_begin ()
        try:
            self._rs.delete(str(k), txn)
            # get the rs dict
            (last, avail) = _pl(_db._meta.get('rs', txn=txn))
            del avail[k]
            _db._meta.put('rs', _ps ((last, avail)), txn = txn)
        except:
            _db._env.txn_abort(txn)
            raise
        _db._env.txn_commit(txn)
        return

    def iteritems(self):
        (last, avail) = _pl(self._db()._meta.get('rs'))
        for k, name in avail.iteritems():
            yield k, self[k]
    
    def itervalues(self):
        for k, v in self.iteritems():
            yield v
    
    def iterkeys(self):
        for k, v in self.iteritems():
            yield k

    __iter__ = itervalues

    def new(self, rsid=None, txn=None):
        """ Create an empty result set """
        _db = self._db()
        txn = _db._env.txn_begin(parent=txn)
        try:
            # get the next rs id
            (last, avail) = _pl(_db._meta.get('rs', txn=txn))
            (last, rsid)  = Tools.id_make(last, rsid)
            _db._meta.put('rs', _ps((last, avail)), txn=txn)
            rs = resultset.ResultSet(rsid, _db)
        except:
            _db._env.txn_abort(txn)
            raise
        _db._env.txn_commit(txn)
        return rs

    def update(self, result_set, txn=None):
        _db = self._db()
        txn = _db._env.txn_begin(parent=txn)
        try:
            (last, avail) = _pl(_db._meta.get('rs', txn=txn))
            avail[result_set.id] = result_set.name
            _db._meta.put('rs', _ps((last, avail)), txn=txn)

            self._rs.put(str(result_set.id),
                         _ps((result_set._contents,
                              result_set.name)), txn=txn)
        except:
            _db._env.txn_abort(txn)
            raise
        _db._env.txn_commit(txn)

    def _on_delete_item(self, key, txn):
        for v in self.itervalues():
            if key in v:
                del v[key]
                self.update(v, txn=txn)
    
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
            flag = db.DB_CREATE
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
            self.rs = ResultSetStore(self, txn)
        except:
            self._env.txn_abort(txn)
            raise
        
        self._env.txn_commit(txn)
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
        self.emit('add-item', val)
        return key
    

    def __setitem__ (self, key, val):
        assert self.has_key (key), \
               _('entry %s does not exist') % `key`

        val = self.validate(val)
        val.key = key
        
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
        self.emit('update-item', key)
        return


    def __delitem__ (self, key):
        id = str (key)
        
        txn = self._env.txn_begin ()

        try:
            # Start by cleaning up dependencies, as they might wish to
            # access the item a last time.
            self.emit('delete', key, txn)

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
        self.emit('delete-item', key)
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

    def _q_to_rs(self, res):
        rs = self.rs.new()
        rs._from_array(res)
        return rs
    
    def __getitem__ (self, key):
        return _pl(self._db.get(str(key)))

    def _entries_get(self):
        return RSDB(self)

    entries = property(_entries_get)
    
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

