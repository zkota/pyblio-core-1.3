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

from Pyblio import Store, Callback, Arrays, Sort

class ResultSet(Store.ResultSet, Callback.Publisher):
    def __init__(self, rsid, db, contents=None):
        Callback.Publisher.__init__ (self)
        if contents is None:
            self._contents = Arrays.KeyArray()
        else:
            self._contents = contents
        self.id   = rsid
        self.name = None
        self._db   = db
        self._db.register('delete-item', self._on_db_delete)
        self._db.register('update-item', self._on_db_update)
        
    def view (self, criterion):
        return View(self, criterion)

    def add(self, k):
        self._contents.add(k)
        self.emit('add-item', k)
        return

    def __delitem__(self, k):
        del self._contents[k]
        self.emit ('delete-item', k)
        return
    
    def itervalues (self):
        for k in self._contents:
            yield self._db[k]

    def iteritems (self):
        for k in self._contents:
            yield (k, self._db[k])

    def iterkeys(self):
        return iter(self._contents)
    
    __iter__ = iterkeys

    def __len__(self):
        return len(self._contents)

    def destroy(self):
        for k in list(self._contents):
            del self._db[k]

    def _from_array(self, contents):
        self._contents = contents

    def _on_db_delete (self, k):
        """ invoked when the database removes an item """
        try:
            del self[k]
        except IndexError:
            pass

    def _on_db_update(self, k):
        if k in self._contents:
            self.emit('update-item', k)

class View(Callback.Publisher):

    def __init__ (self, src, crit):
        Callback.Publisher.__init__(self)
        
        self._crit = crit
        self._src  = src
        
        self._update(None, '')

        self._src.register('add-item', self._update, 'add-item')
        self._src.register('delete-item', self._update, 'delete-item')
        self._src.register('update-item', self._update, 'update-item')
        return
    
    def _update(self, key, signal):
        view = [(self._crit.cmp_key(e), e.key) for e in self._src.itervalues()]
        view.sort(lambda a, b: Sort.compare(a[0], b[0]))

        self._view = [x[1] for x in view]
        self.emit(signal, key)
        return

    def __len__ (self):
        return len(self._view)

    def __getitem__ (self, i):
        return self._view[i]

    def __iter__ (self):
        return iter (self._view)

    def iterkeys (self):
        return iter(self._view)
    
    def iteritems(self):
        for i in self._view:
            yield (i, self._src._db[i])
            
    def itervalues(self):
        for i in self._view:
            yield self._src._db[i]

    def index(self, key):
        try:
            return self._view.index(key)
        except ValueError:
            raise KeyError(key)
