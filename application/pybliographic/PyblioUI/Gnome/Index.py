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
    
    def __init__(self, rs, db = None):
	gtk.GenericTreeModel.__init__(self)

        self._rs = rs
        self._db = db
        return

    def on_get_flags (self):
	return gtk.TREE_MODEL_LIST_ONLY | gtk.TREE_MODEL_ITERS_PERSIST

    
    def on_get_n_columns (self):
	'''returns the number of columns in the model'''
	return len (self._columns)

    
    def on_get_column_type (self, index):
	'''returns the type of a column in the model'''
	return self._columns [index]
    
    def on_get_path (self, node):
	'''returns the tree path. in our case, it is the first part of
	the node tuple '''
        
	return (node [0],)
    
    def on_get_iter(self, path):

        '''returns the node corresponding to the given path.  In our
        case, the node is the path'''

        if len (path) != 1: return None

        # FIXME: obviously very inefficient !
        
        p = path [0]
        
        i = p + 1
        n = iter (self._rs)

        try:
            while i:
                d = n.next ()
                i = i - 1
                
        except StopIteration:
            return None
        
        return (path [0], d, n)
    
    def on_get_value (self, node, column):
	'''returns the value stored in a particular column for the node'''

        k = node [1]
        # column 0 is simply the entry's key
        if column == 0: return k

        # column 1 is an actual description
        if self._db is not None:
            db = self._db
        else:
            db = self._rs
            
        e = db [k]
        
	return Entry.summary (e)
    
    def on_iter_next (self, node):
	'''returns the next node at this level of the tree'''

        p, d, n = node
        try:
            d = n.next ()

        except StopIteration:
            return None

        return (p + 1, d, n)
    
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
        return None
        
    def on_iter_parent(self, node):
	'''returns the parent of this node'''
        return None
