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


''' This Module contains the interfaces one might want to implement in
order to provide a specific database _storage_.

Please note: this is an interface definition, but it can also be used
as a base class.
'''

from gettext import gettext as _

from Pyblio.Schema import Schema


class Key (object):

    ''' A key uniquely identifies an entry in a database '''

    def __init__ (self, key):
        self._key = key
	return

    def __repr__ (self):
	return 'Key (%s)' % `self._key`

    def __cmp__ (self, other):
	return cmp (self._key, other._key)

    def __hash__ (self):
	return hash (self._key)

    def xmlwrite (self, fd):
        pass


class Entry (dict):

    """
    A database entry. It behaves like a dictionnary, which returns a
    attribute for each key, depending on the database schema.

    The entry.key is an instance of Core.Key, and has to be unique
    over the database.

    The entry.type is an instance of Schema.Document. It links the
    field names with their type.

    For each attribute, it is possible that the returned value is
    lossy compared with the native data, if some information was not
    properly translated. This is known by calling self.has_loss (key)
    """

    def __init__ (self, key, type):
	self.type   = type
	self.key    = key
        self.native = None

        self._loss = {}
        return

    def has_loss (self, key):
	''' Returns wether the entry attribute is converted with loss '''
	return self._loss.get (key, False)

    def loss_set (self, key, flag = True):
        self._loss [key] = flag
        return

    def xmlwrite (self, fd):
        pass


class Database (dict):

    ''' This class represents a full bibliographic database.  It also
    looks like a dictionnary, linking a Core.Key with a Core.Entry.'''


    def __init__ (self, schema):
	''' Create a new empty database with the specified schema '''
        self.schema = schema
	return

    def xmlwrite (self, fd):
        fd.write ('<?xml version="1.0" encoding="utf-8"?>\n\n')
        fd.write ('<pyblio-db>\n')

        self.schema.xmlwrite (fd, embedded = True)
        
        for v in self.itervalues ():
            v.xmlwrite (fd)
        
        fd.write ('</pyblio-db>\n')
        return
    
