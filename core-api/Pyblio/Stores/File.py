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

import os, copy, string

from Pyblio import Store, Callback, Attribute, Exceptions, Tools


class EnumGroup (dict, Store.EnumGroup, Callback.Publisher):

    def __init__ (self, group):

        Callback.Publisher.__init__ (self)
        
        self._id = 1
        self._group = group

        return
    

    def add (self, item, key = None):

        self._id, key = Tools.id_make (self._id, key)

        v = copy.deepcopy (item)
        
        v.id    = key
        v.group = self._group
        
        self [key] = v

        return key

    def __delitem__ (self, k):

        self.emit ('delete', self._group, k)

        dict.__delitem__ (self, k)
        return
    

class EnumStore (dict, Store.EnumStore):

    def __init__ (self, db):

        self._db = db
        return
    

    def add (self, group):

        if self.has_key (group):
            raise Exceptions.ConstraintError \
                  (_('group %s exists') % `group`)
        
        gp = EnumGroup (group)
        gp.register ('delete', self._db._enum_use_check)
        
        self [group] = gp
        
        return gp


# --------------------------------------------------

class Viewable (object):

    def view (self, criterion):
        view = []
        
        for e in self.itervalues ():
            try:
                value = e [criterion]
                value = string.join (map (lambda x: x.sort (), value), '\0')
                
            except KeyError:
                value = ''
                
            view.append ((value, e.key))

        view.sort (lambda a, b: cmp (a [0], b [0]))

        return map (lambda x: x [1], view)
    

class ResultSet (dict, Viewable, Store.ResultSet):

    def __init__ (self, rsid, db):

        dict.__init__ (self)

        self.id   = rsid
        self.name = None

        self._dict = db
        return


    def add (self, k):
        
        self [k] = 1
        return


    def itervalues (self):
        
        for k in dict.iterkeys (self):
            yield self._dict [k]

    def iteritems (self):
        
        for k in dict.iterkeys (self):
            yield (k, self._dict [k])


    def _on_db_delete (self, k):
        """ invoked when the database removes an item """

        try: del self [k]
        except KeyError: pass
        
        return


class RODict (Viewable):

    """ Read-only dictionnary """

    def __init__ (self, _dict):
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
        
        if permanent:
            self [rs.id] = rs
        
        return rs

    def __iter__ (self):

        return self.itervalues ()

# --------------------------------------------------

class Database (Store.Database, Callback.Publisher):

    def __init__ (self, schema = None, file = None,
                  create = False):

        Callback.Publisher.__init__ (self)

        self._dict   = {}
        self._rodict = RODict (self._dict)
        
        self.file = file

        self.schema = schema
        
        self.header = None
        self.enum   = EnumStore (self)
        self.rs     = ResultSetStore (self)
        
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

            except IOError, msg:
                raise Store.StoreError (_("cannot open '%s': %s") % (file, msg))
            
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

        value = copy.deepcopy (value)
        value.key = key

        value = self.validate (value)
        
        self._dict [key] = value
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
        return


    def __getitem__ (self, key):
        return self._dict [key]


    def query (self, word, permanent = False):

        res = self.rs.add (permanent)
        
        for entry in self.entries.itervalues ():

            found = False
            
            for attrs in entry.values ():

                for attr in attrs:
                    idx = attr.index ()
                
                    if word in idx:
                        found = True
                        break

                if found: break
                
            if not found: continue

            res.add (entry.key)

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


def dbimport (target, source):

    db = Database (file = source)
    db.file = target

    return db


