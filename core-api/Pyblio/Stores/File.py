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

import os, copy

from Pyblio import Store


class EnumGroup (Store.EnumGroup, dict):

    pass


class EnumStore (dict, Store.EnumStore):
    def __init__ (self):

        self._id = 1
        return
    

    def add (self, group, item, key = None):

        if key:
            if key >= self._id:
                self._id = key + 1
        else:
            key = self._id
            self._id = self._id + 1

        if not self.has_key (group):
            self [group] = EnumGroup ()

        v = copy.deepcopy (item)
        
        v.id    = key
        v.group = group
        
        self [group] [key] = v

        return key
    

class ResultSet (dict, Store.ResultSet):

    def __init__ (self, rs_name):

        dict.__init__ (self)
        
        self.name = rs_name
        return


    def add (self, k):
        
        self [k] = 1
        return

    
    def __iter__ (self):
        return self.iterkeys ()
    

class ResultSetStore (dict, Store.ResultSetStore):

    def add (self, rs_name = None):
        """ Create an empty result set """

        rs = ResultSet (rs_name)
        
        if rs_name:
            self [rs_name] = rs
        
        return rs

    def __iter__ (self):

        return self.itervalues ()


class Database (dict, Store.Database):

    def __init__ (self, schema = None, file = None,
                  create = False):

        self.file = file

        self.schema = schema
        
        self.header = None
        self.enum   = EnumStore ()
        self.rs     = ResultSetStore ()
        
        self._id = 1

        if create:
            # WARNING: this code contains a race condition. This
            # exception is only here to trap blatant errors, not to
            # avoid concurrent accesses. How does one open a file with
            # O_CREAT, BTW ? Mabe this would not be portable at all.
            
            if os.path.exists (file):
                raise Store.StoreError (_("database '%s' already exists") % file)
            
            self.save ()

        else:
            handler = Store.DatabaseParse (self)

            try:
                handler.parse (file)

            except ValueError, msg:
                raise Store.StoreError (_("cannot open '%s': %s") % (file, msg))
            
        return


    def add (self, value, id = None):
        """ Insert a new entry in the database.

        New entries MUST be added with this method, not via an update
        with a hand-made Key.

        key is only useful for importing an existing database, by
        proposing a key choice.
        """

        if id:
            v = int (id)
            if v >= self._id:
                self._id = v + 1
        else:
            id = Store.Key (self._id)
            self._id = self._id + 1

        assert not self.has_key (id), \
               _("a duplicate key has been generated: %d") % id

        value = copy.deepcopy (value)
        value.key = id
        
        dict.__setitem__ (self, id, value)
        return id


    def __setitem__ (self, key, value):

        # Ensure the key is not added, only updated.
        assert self.has_key (key), \
               _("use self.add () to add a new entry")

        value = copy.deepcopy (value)
        value.key = key
        
        dict.__setitem__ (self, key, value)
        return

    def query (self, word, name = None):

        res = ResultSet (name)
        
        for entry in self.itervalues ():

            found = False
            
            for attrs in entry.values ():
                idx = sum (map (lambda x: x.index (), attrs), [])
                
                if word in idx:
                    found = True
                    break
                
            if not found: continue

            res.add (entry.key)

        if name: self.rs [name] = res

        return res
        
    
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

