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
# 

import atexit, os, string, sys, types

import cPickle as pickle

from gettext import gettext as _

from Pyblio.Callback import Publisher


''' UI configuration framework. This module provides a dynamic model
for typed configuration information '''


class Item (Publisher):
    
    ''' A single configuration information. This object emits a 'set'
    event when a modification of its value is attempted.'''
    
    def __init__ (self, description, vtype = None):

        Publisher.__init__ (self)
        
        self.description = description

        # type definition
        if not isinstance (vtype, PrimaryType):
            raise TypeError ('vtype must be an instance of PrimaryType')
        
        self._type = vtype
        
        # actual data contained in the item
        self._data = None
        return

    
    def _set (self, value):

        self._type.match (value)
        self.emit ('set', value)
        
        self._data = value
        return

    def _get (self):
        return self._data

    value = property (_get, _set)


class Storage (dict):

    """ A Storage is a deferred dictionnary. It contains keys of the form

           domain/subkey

        and domains can be addressed separately."""


    def domains (self):

        """ Return a list of available domains """
        
        # get all domains from the keys
        table = {}

        for k in self.keys ():
            d = string.split (k, '/') [0]
            table [d] = 1
            
        return table.keys ()

    def keys_in_domain (self, domain):

        """ Return a list of keys in a domain """
        
        # simplify the list
        def test_dom (key):
            return string.split (key, '/') [0] == domain
    
        return filter (test_dom, self.keys ())
        
    
class PrimaryType (object):
    
    ''' Base class for simple types '''

    def match (self, value):
        if type (value) is not self._type:
            
            raise TypeError (_('expected %s, got %s') % (
                self._type, type (value)))
        return
    
    
class String (PrimaryType):

    _type = str

    def __str__ (self):
        return _('String')
    
class Boolean (PrimaryType):

    _type = bool

    def __str__ (self):
        return _('Boolean')
    
class Integer (PrimaryType):

    _type = int
    
    def __init__ (self, min = None, max = None):
        self.min  = min
        self.max  = max
        return

    def match (self, value):
        PrimaryType.match (self, value)
        
        if (self.min and value < self.min) or \
               (self.max and value > self.max):

            raise ValueError (_('value should be between %s and %s') % (
                self.min, self.max))

        return

    def __str__ (self):

        if self.min is None and self.max is None:
            return _("Integer")
        if self.min is None:
            return _("Integer under %d") % self.max
        if self.max is None:
            return _("Integer over %d") % self.min

        return _("Integer between %d and %d") % (self.min, self.max)
    

class Element (PrimaryType):
    
    def __init__ (self, elements):
        self._set = elements
        return

    def _expand (self):
        s = self._set
        if callable (s): s = s ()
        
        return s
    
    def match (self, value):
        exp = self._expand ()
        if value in exp: return

        raise ValueError (_('%s not in %s') % (
            `value`, `exp`))

    def __str__ (self):
        return _("Element in `%s'") % str (self._expand ())

    
class Tuple (PrimaryType):
    
    ''' A tuple composed of different subtypes '''

    _type = tuple
    
    def __init__ (self, subtypes):
        self._sub = subtypes
        return

    def match (self, value):
        PrimaryType.match (self, value)

        for sub, val in zip (self._sub, value):
            sub.match (val)
            
        return

    def __str__ (self):
        return _("Tuple (%s)") % \
               string.join (map (str, self._sub), ', ')
    

class List (PrimaryType):
    
    ''' An enumeration of items of the same type '''

    _type = list

    def __init__ (self, subtype):
        self._sub = subtype
        return

    def match (self, value):
        PrimaryType.match (self, value)

        for v in value:
            self._sub.match (v)
        return

    def __str__ (self):
        return _("List (%s)") % str (self._sub)
    

class Dict (PrimaryType):
    
    ''' A dictionnary '''

    _type = dict
    
    def __init__ (self, key, value):
        self._k = key
        self._v = value
        return

    def match (self, value):
        PrimaryType.match (self, value)
        
        for k, v in value.items ():
            self._k.match (k)
            self._v.match (v)
                
        return

    def __str__ (self):
        return _("Dictionary (%s, %s)") % (str (self._k),
                                           str (self._v))


_changes = {}

def set_and_save  (key, value):
    set (key, value)
    print 'SET AND SAVE:', key, value
    global _changes
    _changes [key] = value

def load_user ():
    # load the saved items
    try:
        file = open (os.path.expanduser ('~/.pybrc.conf'), 'r')
    except IOError: return

    changed = pickle.load (file)
    file.close ()

    for item in changed.keys ():
        _items._maybe_resolve (item)
        set (item, changed [item])
        
    return
        
def save_user (changed):

    if not changed:
        return
    # read what has to be saved again
    try:
        file = open (os.path.expanduser ('~/.pybrc.conf'), 'r')
        previous = pickle.load (file)
        file.close ()
    except IOError: previous = {}
    previous.update(changed)
    
    file = open (os.path.expanduser ('~/.pybrc.conf'), 'w')
    pickle.dump (previous, file)
    file.close ()
    return


#   TERMINATION ROUTINE

atexit.register(save_user, _changes)

