# This file is part of pybliographer
# 
# Copyright (C) 2003, Peter Schulte-Stracke
# Email : mail@schulte-stracke.de
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
# $Id:$

"""

      ##################################################
      #                                                #
      #           E X P E R I M E N T A L              #
      #                                                #
      ##################################################


"""

try: _
except NameError:
    def _(s) \
       : return s
import sys
from Pyblio import Base

#
#   Stub for Record / Record
#------------------------------------------------------------

class OldStyleRecord (Base.Record):

    Typ = 'O'
    def __init__ (self, *args, **argh):
        self.dict = {}
        Base.Record.__init__(self, *args, **argh)
    
    def has_key(self, s): return self.dict.has_key(s)
    def __iter__(self): return self.dict.__iter__
    def __getitem__(self, key): return self.dict[key]
    def __setitem__ (self, key, value): self.dict[key] = value
    def __delitem__ (self, key) : del self.dict[key]
    def __len__ (self): return len(self.dict)

    def write_long (self, stream=sys.stdout, *args, **argh):
        self.head_long (stream, *args, **argh)
        for i in self.dict.keys():
            j = self.dict[i].split('//')
            stream.write ('%10s %s\n' %(i,  j[0]))
            for k in j[1:]:
                stream.write('           %s\n' %(k))            
                          
        self.foot_long (stream, *args, **argh) 

Base.register (OldStyleRecord)


#
#   stub for Database
#------------------------------------------------------------

class Database (Base.RecordSet):

    def __init__ (self, base=None,  control=None, 
                 name= 'A Database Stub', temporary = True,
                  *args, **argh):
        """
        base is the database which contains the record
        """
        assert base == None
        self.base = self
        self.name = name 
        #self.control = control or Coco.RecordSet()
        self.order = None ## ??
        self.temporary = temporary
        self._items = {}
        print 'DATA BASE:', `self`
        self.nextid = 0
        return

    def __len__ (self):
        """Number of items in record set.  Subclasses may override."""
        return len(self._items)

    def __del__ (self):
        ### XXX circular references from db._folders XXX
        """Before deleting the recordset, remove all references to it. """
        #self.base.unregister(self)
        self.clear()
        
    def get (self, db_id):
        """Retrieve a record from the database.
        NOTE: Overridden by the db subclass."""
        return# self.base.get(db_id)
    
    def clear(self):
        for i in self._items:
            self.remove(i)

    
    #--------------------------------------------------
    #   Input interface

    def add (self, record, position=-1):
        """Add a record to the base, if necessary.
        This must go through the base add method, because in
        typical situations, both, the data base and the current
        result set are meant to be updated.

        Only items (not ids) are possible inputs.????
        NOTE that in a database implementation, much must be added;
        here it suffices to delegate.
        NOTE that a.t.m. we do not keep the sequence!
        NOTE that we should perhaps accept Ids as well
        """

        if not self.check_in(record):
            return
        
        if record.DB:
            assert record.DB == self, 'ERROR: wrong database'
            if self._items.has_key(record.DB_ID):
                return record
        else:
            assert record.DB_ID == -1, 'ERROR: record not new'
            record.DB = self
            record.DB_ID = self.next_id()
        self._items [record.DB_ID] = record
        return record

    def extend (self, set):
        """Extend a recordset by adding all items from another
        recordset. Does not change the other recordset"""
        for item in set:
            self.copy(item)

    def insert (self, item, position=-1):
        """Only used for Folders: insert a folder hierarchically. """
        raise NotImplementedError
    
    def remove (self, record):
        """Remove a record from this recordset"""
        if self.check_out(record):
            del self._items[record.DB_ID]
        
    def check_in (self,record):
        return True
    
    def check_out (self, record):
        return True

    def move (self, record, set):
        """Move a record *from* one recordset set into this one.
        Note that the order of arguments 
        is uncommon: target.move(item, from) """
        self.copy(record, set)
        set.remove (record)

    def copy (self, record, set=None):
        """Copy a record (from set) into this recordset."""
        if record.DB != self.base:
            record = copy.copy(record)
            record.DB = None
            record.DB_ID = None
        return self.add(record)

    def register_recordset(self, rs):
        """Enter a recordset in to the list of recordsets
        that depend on this database. """
        self.rsets.append(rs)
        
    #--------------------------------------------------
    #   Defaults
   
    def set_filter(self, filter):
        """Set the filter of the Recordset."""
        self.default_filter = filter
        #self.control['filter'] = filter
        return
    
    def set_sorting (self, sorting):
        """set the sorting order for the Recordset."""
        self.default_sorting = sorting
        #self.control['sorting'] = sorting
        return

    def set_style (self, style):
        self.default_style = style
        #self.control['style'] = style
        return

    def set_order (self, kind):
        """Selects the kind of ordering required. Typical values are:
        0  implicit,  
        1  author only,
        2  title only
        3  author/title style.
        """

        if self.order:
            self.order = kind
            #self.redisplay()
        else:
            self.order = kind
        return

    def set_position(self, position):
        """Sets the starting position for the iterator.
        0 means the very  first record, acording to current ordering,
        -1 means the very last one."""
        
        self.default_position = position
        
    def set_limit (self, start, stop=None):
        if stop != None:
            self.low_limit = start
            self.high_limit = stop
        else:
            self.low_limit = None
            self.high_limit = stop
        return

    #--------------------------------------------------
    #   Utilities
    
    def create_bibtex_key(self, item, dict, url):
        from Pyblio import Autoload, Config, Key
        if item.key is None:
            # call a key generator
            keytype   = Config.get ('base/keyformat').data
            return  Autoload.get_by_name (
                'key', keytype).data (item, dict)
        else:
            prefix = item.key.key
            key = Key.Key (self, prefix)
            suffix = ord ('a')
            while dict.has_key (key):
                key = Key.Key (self, prefix + '-' + chr (suffix))
                suffix = suffix + 1
            return key

    def next_id(self):
        self.nextid += 1
        return self.nextid

# Local Variables:
# py-master-file: "ut_stubs.py"
# End:
