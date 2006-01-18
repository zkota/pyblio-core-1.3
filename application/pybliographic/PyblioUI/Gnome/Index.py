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

""" Data model, UI side """

from gettext import gettext as _

import gtk, gobject, string

from PyblioUI import Entry


class DatabaseModel (gtk.GenericTreeModel):

    ''' This class represents the model of a list containing a full
    database or a result set. '''

    _columns = (gobject.TYPE_PYOBJECT,
                gobject.TYPE_STRING)

    COL_CONTENT = 1
    
    def __init__(self, vw, db):
	gtk.GenericTreeModel.__init__(self)

        self._vw = vw
        self._db = db

        self._db.register('record-added', self._record_added)
        self._db.register('record-deleting', self._record_deleting)
        return

    def _record_deleting(self, key):
        """ Called _before_ a key is about to be deleted."""

        idx = self._vw.index(key)
        path = self.on_get_path(idx)
        
        self.row_deleted(path)
        return

    def _record_added(self, key):
        """ Called when the underlying model has an additional record."""

        # We need to find out the place of this new record into the
        # Store.View
        idx = self._vw.index(key)

        path = self.on_get_path(idx)
        iter = self.get_iter(path)
        
        self.row_inserted(path, iter)
        return
    
    def on_get_flags(self):
	return gtk.TREE_MODEL_LIST_ONLY | gtk.TREE_MODEL_ITERS_PERSIST

    
    def on_get_n_columns(self):
	'''returns the number of columns in the model'''
	return len(self._columns)

    
    def on_get_column_type(self, index):
	'''returns the type of a column in the model'''
	return self._columns[index]
    
    def on_get_path(self, node):
	'''returns the tree path. in our case, it is the first part of
	the node tuple '''
	return (node,)
    
    def on_get_iter(self, path):
        '''returns the node corresponding to the given path.  In our
        case, the node is the path'''

        if len(path) != 1: return None

        n = path[0]
        
        if n >= len(self._vw): return None
        return n

    
    def on_get_value(self, node, column):
	'''returns the value stored in a particular column for the node'''

        k = self._vw [node]
        
        # column 0 is simply the entry's key
        if column == 0: return k

        # column 1 is an actual description
        e = self._db.db [k]
	return Entry.summary (e)
    
    def on_iter_next(self, node):
	'''returns the next node at this level of the tree'''

        node += 1
        if node >= len(self._vw): return None
        
        return node
    
    def on_iter_children(self, node):
	'''returns the first child of this node'''
        return None
    
    def on_iter_has_child(self, node):
	'''returns true if this node has children'''
	return False
    
    def on_iter_n_children(self, node):
	'''returns the number of children of this node'''
        return 0
        
    def on_iter_nth_child(self, node, n):
	'''returns the nth child of this node'''
        if node is None: return (n,)
        return None
        
    def on_iter_parent(self, node):
	'''returns the parent of this node'''
        return None
