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

Tables in use:

* database/entries [HASH]

  key:   string value of an entry key
  value: Store.Entry as a pickled object

* database/meta [HASH]

  key:   a meta parameter (next available key,...)
  value: its value

* database/enum [HASH]

  key:   id of the enum
  value: pickled dict containing the values

* index/full [HASH / DUP]

  key:   the indexed value
  value: the entry that contains the value

* resultset/<id> [HASH]

  key:   string value of the entry's key
  value: no meaning

* view/<id> [BTREE / RECNUM / DUP]

  key:   field on which we sort
  value: key from which the field is taken

"""
from gettext import gettext as _

import os, shutil, copy, sys, traceback, string

import cPickle as pickle

from bsddb3 import db

from Pyblio import Store, Schema, Callback, Attribute, Exceptions, Tools

_pl = pickle.loads
_ps = pickle.dumps

# --------------------------------------------------

class RSDB (object):

    """ Virtual result set that loops over the full database """

    def __init__ (self, _db, _env, _meta):

        self.id  = 0
        
        self._db   = _db
        self._env  = _env
        self._meta = _meta
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

        return View (self._db, self._env, self._meta,
                     self, criterion)
    
    

# --------------------------------------------------

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
            
            self._v.open ('view', str (serial), db.DB_BTREE, db.DB_CREATE, txn = txn)

            # Create the index for the view
            self._vi = db.DB (self._env)
            self._vi.open ('viewidx', str (serial), db.DB_BTREE, db.DB_CREATE, txn = txn)


            # fill the view with the current content of the result set
            for e in rs.itervalues ():
                try:
                    value = e [criterion]
                    value = string.join (map (lambda x: x.sort (), value), '\0')
                    value = value.encode ('utf-8')
                    
                except KeyError:
                    value = ''

                # In order to store multiple values in a DB_RECNUM
                # BTree, it is necessary to "cheat" a bit, and
                # disambiguate between the duplicates; this is done by
                # maintaining a counter by key, which holds the number
                # of similar keys. This counter is appended to each
                # entry.
                
                last = self._vi.get (value)
                
                if last is None: last = 0
                else:            last = int (last)
                
                self._vi.put (value, str (last + 1), txn = txn)

                value = value + '\0%d' % last
                self._v.put (value, str (e.key), txn = txn)
            
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


    def __getitem__ (self, idx):

        return Store.Key (self._v.get (idx + 1) [1])
    
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
            self._vi.close ()
            
            db.DB (self._env).remove ('view', str (self._id))
            db.DB (self._env).remove ('viewidx', str (self._id))
            
        except:
            # exceptions in __del__ methods are not reported by default
            etype, value, tb = sys.exc_info ()
            traceback.print_exception (etype, value, tb)
            
            txn.abort ()
            raise

        txn.commit ()
        return

# --------------------------------------------------

class ResultSet (Store.ResultSet, Callback.Publisher):

    def __init__ (self, _db, _env, _meta, id,
                  permanent = False, txn = None):

        Callback.Publisher.__init__ (self)
        
        # RS id as a string and as an integer
        self.id  = id
        self._id = str (id)
        
        self._name = None

        self._db   = _db
        self._env  = _env
        self._meta = _meta
        
        self._permanent = permanent

        self._rs = db.DB (self._env)
        self._rs.open ('resultset', self._id, db.DB_HASH,
                       db.DB_CREATE, txn = txn)

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

        txn = self._env.txn_begin (txn)

        try:
            self._rs.put (str (k), '', txn = txn)
        except:
            txn.abort ()
            raise

        # read the value and add it to all the views this set is
        # involved in.

        txn.commit ()
        return

    def __delitem__ (self, k, txn = None):

        txn = self._env.txn_begin (txn)

        try:
            self._rs.delete (str (k), txn = txn)
        except:
            txn.abort ()
            raise

        txn.commit ()
        return


    def view (self, criterion):

        return View (self._db, self._env, self._meta,
                     self, criterion)
    

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

    def __len__ (self):

        return self._rs.stat () ['nkeys']


    def _on_delete (self, key, txn = None):

        try:
            self.__delitem__ (key, txn)
            
        except KeyError:
            pass

        return
    

class ResultSetStore (dict, Store.ResultSetStore, Callback.Publisher):

    def __init__ (self, _db, _env, _meta, txn):

        Callback.Publisher.__init__ (self)

        self._db   = _db
        self._env  = _env
        self._meta = _meta
        
        (rsid, avail) = _pl (self._meta.get ('rs', txn = txn))

        txn = self._env.txn_begin (parent = txn)

        try:
            # initialize with the existing result sets
            for rsid, data in avail.items ():
                name, status = data
            
                rs = ResultSet (self._db, self._env, self._meta, rsid, status, txn = txn)
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
            
            rs = ResultSet (self._db, self._env, self._meta, rsid,
                            permanent, txn = txn)
            
        except:
            txn.abort ()
            raise
        
        txn.commit ()

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
        self._enum.open ('database', 'enum',
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

            # Result sets handler
            self.rs = ResultSetStore (self._db, self._env, self._meta, txn)
            self.register ('delete', self.rs._on_delete)

            # Full text indexing DB
            self._idx = db.DB (self._env)
            self._idx.set_flags (db.DB_DUP)
            self._idx.open ('index', 'full', db.DB_HASH, flag, txn = txn)

            # Store for Enumerated values
            self.enum = EnumStore (self._env, txn)
            self.enum.register ('delete', self._enum_use_check)

        except:
            txn.abort ()
            raise
        
        txn.commit ()

        # Result set containing the full db
        self._entries_rs = RSDB (self._db, self._env, self._meta)
        
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

    handler = Store.DatabaseParse (db)

    try:
        handler.parse (source)

    except ValueError, msg:

        dbdestroy (target)
        raise Store.StoreError (_("cannot open '%s': %s") % (file, msg))

    return db
