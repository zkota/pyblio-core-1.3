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

import os, shutil
import cPickle as pickle

from bsddb3 import db

from Pyblio import Store, Schema

class DBIterBase:

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

    def _content (self, data):

        return data [0]

class DBIterValues (DBIterBase):
    
    def _content (self, data):

        return pickle.loads (data [1])

class DBIterItems (DBIterBase):
    
    def _content (self, data):

        return data [0], pickle.loads (data [1])
    
    
class Database:

    def __init__ (self, path, schema = None, create = False):

        if create:
            try:
                os.mkdir (path)

            except OSError, msg:
                raise Store.StoreError (_("cannot create '%s': %s") % (
                    path, msg))
            
            flag = db.DB_CREATE

            self.schema = schema
        else:
            flag = 0

            # the schema is in the directory
            try:
                s = os.path.join (path, 'schema.xml')
                self.schema = Schema.Schema (s)
                
            except ValueError, msg:
                raise Store.StoreError (_("cannot open '%s': %s") % (
                    path, msg))
            
        self._path = path
        
        self._env = db.DBEnv ()
        self._env.open (path, flag | db.DB_INIT_MPOOL)
        
        self._db  = db.DB (self._env)
        self._db.open (path, 'db', db.DB_HASH, flag)

        return


    def save (self):

        # store the schema
        file = os.path.join (self._path, 'schema.xml')
        
        try:
            os.unlink (file + '.bak')
        except OSError:
            pass

        if os.path.exists (file):
            os.rename (file, file + '.bak')

        fd = open (file, 'w')
        self.schema.xmlwrite (fd)
        fd.close ()

        # Flush the database
        self._db.sync ()
        return
    

    def __setitem__ (self, key, val):
        val = pickle.dumps (val)
        self._db.put (key, val)
        return
    
    def __getitem__ (self, key):
        
        return pickle.loads (self._db.get (key))

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

    return Database (path = path + '.db', create = False)

