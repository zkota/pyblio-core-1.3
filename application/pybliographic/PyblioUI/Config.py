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
    
    def __init__ (self, name, description, vtype = None):

        Publisher.__init__ (self)
        
        self.name        = name
        self.description = description

        # type definition
        if not isinstance (vtype, PrimaryType):
            raise TypeError ('vtype must be an instance of PrimaryType')
        
        self._type = vtype
        
        # actual data contained in the item
        self._data = None
        return

    
    def _set (self, value):

        if not self._type.match (value):
            raise RuntimeError ('invalid value for type %s' % `self._type`)
        
        self.emit ('set', value)
        
        self._data = value
        return

    def _get (self):
        return self._data

    value = property (_get, _set)


class Storage (dict):

    """ A Storage is a deferred dictionnary. It contains keys of the form

           domain/subkey

       ...where domain refers to some configuration file, which is
       loaded when the first key requiring it is requested. """

    def __init__ (self):
        dict.__init__ (self)
        self._sources = {}
        return


    def _maybe_resolve (self, key):

        """ Ensure a given domain has been loaded """
        
        if dict.has_key (self, key): return
        domain = string.split (key, '/') [0]

        from PyblioUI import Config

        env = {'Config': Config}
        
        if self._sources.has_key (domain):
            file = self._sources [domain]

            # Ensure the domain is loaded once
            del self._sources [domain]

            execfile (file, env, env)
        return


    def domains (self):

        """ Return a list of available domains """
        
        # get all domains from the keys
        doms = map (lambda key: string.split (key, '/') [0], self.keys ())
        
        # simplify the list
        table = {}
        def mark (x): table [x] = 1
        
        map (mark, doms + self._sources.keys ())

        return table.keys ()

    def keys_in_domain (self, domain):

        """ Return a list of keys in a domain """
        
        self._maybe_resolve (domain)

        # simplify the list
        def test_dom (key, dom = domain):
            f = string.split (key, '/')
            if f [0] == dom:
                return 1
            return 0
    
        return filter (test_dom, self.keys ())
        
    
    def has_key (self, key):

        """ Check that a given key is defined. """
        
        self._maybe_resolve (key)
        return dict.has_key (self, key)


    def __getitem__ (self, key):

        """ Get a given key. """
        
        self._maybe_resolve (key)
        return dict.__getitem__ (self, key)
        

    def __setitem__ (self, key, value):

        """ Set a given key. """

        self._maybe_resolve (key)
        return dict.__setitem__ (self, key, value)


    def parse (self, directory):
        files = map (lambda x: \
                     os.path.join (directory, x),
                     os.listdir (directory))

        for filename in files:
            if filename [-3:] == '.py':
                domain = string.lower (os.path.split (filename [:-3]) [1])
                self._sources [domain] = filename
        return


class PrimaryType (object):
    
    ''' Base class for simple types '''
    
    def match (self, value):
        return type (value) is self._type

    
    
class String (PrimaryType):

    _type = str

class Boolean (PrimaryType):

    _type = bool

class Integer (PrimaryType):

    _type = int
    
    def __init__ (self, min = None, max = None):
        self.min  = min
        self.max  = max
        return

    def match (self, value):
        if not PrimaryType.match (self, value): return False
        
        if self.min and value < self.min: return False
        if self.max and value > self.max: return False

        return True

    def __str__ (self):

        if self.min is None and self.max is None:
            return _("Integer")
        if self.min is None:
            return _("Integer under %d") % self.max
        if self.max is None:
            return _("Integer over %d") % self.min

        return _("Integer between %d and %d") % (self.min, self.max)
    

class Element:
    def __init__ (self, elements):
        self._set = elements
        return

    def _expand (self):
        s = self._set
        if callable (s): s = s ()
        
        return s
    
    def match (self, value):
        return value in self._expand ()

    def __str__ (self):
        return _("Element in `%s'") % str (self._expand ())

    
class Tuple:
    ''' A tuple composed of different subtypes '''
    
    def __init__ (self, subtypes):
        self._sub = subtypes
        return

    def match (self, value):

        for sub, val in zip (self._sub, value):
            if not sub.match (val): return False
        
        return True

    def __str__ (self):
        return _("Tuple (%s)") % \
               string.join (map (str, self._sub), ', ')
    

class List:
    ''' An enumeration of items of the same type '''

    def __init__ (self, subtype):
        self._sub = subtype
        return

    def match (self, value):

        for v in value:
            if not self._sub.match (v):
                return False
        
        return True

    def __str__ (self):
        return _("List (%s)") % str (self._sub)
    

class Dict:
    ''' A dictionnary '''

    def __init__ (self, key, value):
        self._k = key
        self._v = value
        return

    def match (self, value):

        for k, v in value.items ():
            if not self._k.match (k):
                return False
            if not self._v.match (v):
                return False
                
        return True

    def __str__ (self):
        return _("Dictionary (%s, %s)") % (str (self._k),
                                           str (self._v))

_items = None

def reset ():
    global _items
    _items = Storage ()
    return

def define (key, description, vtype = None):
    
    if _items.has_key (key):
        raise KeyError, "key `%s' already defined" % key

    _items [key] = Item (key, description, vtype)
    return


def get (key):
    return _items [key]


def keys ():
    return _items.keys ()


def has_key (key):
    return _items.has_key (key)


def domains ():
    return _items.domains ()


def keys_in_domain (domain):
    return _items.keys_in_domain (domain)


def parse (dir):
    _items.parse (dir)
    return


reset ()



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

