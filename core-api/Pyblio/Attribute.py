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

""" Basic data types that can be used as attributes for a Core.Entry """

import string, re

from xml import sax
from xml.sax.saxutils import escape, quoteattr

from gettext import gettext as _


re_split = re.compile (r'[^\w]+', re.UNICODE)


class Person (object):
    ''' Description of a person identity '''

    def __init__ (self, honorific = None, first = None, last = None, lineage = None):

        self.honorific = honorific
        self.first     = first
        self.last      = last
        self.lineage   = lineage
        return

    def xmlwrite (self, fd):
        
        data = []
        for f in ('honorific', 'first', 'last', 'lineage'):
            v = getattr (self, f)
            if v:
                data.append ('%s=%s' % (f, quoteattr (v.encode ('utf-8'))))
        
        fd.write ('<person %s/>' % string.join (data, ' '))
        return
    
    def index (self):
        idx = sum ([x.split () for x in (self.first, self.last) if x], [])
        idx = map (string.lower,idx)
                    
        return filter (None, idx)
    

    def sort (self):
        return (u'%s\0%s' % (self.last or '', self.first or '')).lower ()


class Date:
    ''' Description of a date '''

    def __init__ (self, year = None, month = None, day = None):

        self.year  = year
        self.month = month
        self.day   = day
        return

    def xmlwrite (self, fd):

        data = []
        for f in ('year', 'month', 'day'):
            v = getattr (self, f)
            if v:
                data.append ('%s="%d"' % (f, v))
        
        fd.write ('<date %s/>' % string.join (data, ' '))
        return

    def index (self):
        return []

    def sort (self):
        return '%.4d%.2d%.2d' % (self.year or 0,
                                 self.month or 0,
                                 self.day or 0)

            
class Text (unicode):
    ''' This class holds all the other fields (not an Author or a Date) '''

    def xmlwrite (self, fd):

        fd.write ('<text>%s</text>' % escape (self.encode ('utf-8')))
        return

    def index (self):
        idx = map (string.lower, re_split.split (self))
        return filter (None, idx)

    def sort (self):
        return self.lower ()
    

class URL (str):
    ''' Holder for URL data (for example, the location of a database) '''

    def xmlwrite (self, fd):

        fd.write ('<url href=%s/>' % quoteattr (self.encode ('utf-8')))
        return

    def index (self):
        idx = re_split.split (self)
        return filter (None, idx)

    def sort (self):
        return self


class ID (unicode):

    ''' External Identifier (not meaningful for Pyblio) '''

    def xmlwrite (self, fd):
        fd.write ('<id value=%s/>' % quoteattr (self.encode ('utf-8')))
        return

    def index (self):
        return []
    
    def sort (self):
        return self


class Enumerated:

    def __init__ (self, item):
        self.group = item.group
        self.id    = item.id
        return
    
    def xmlwrite (self, fd):
        fd.write ('<enumerated group="%s" id="%d"/>' % (
            self.group, self.id))
        return

    def index (self):
        return [ '%s/%d' % (self.group, self.id) ]
    
    def sort (self):
        return '%s/%d' % (self.group, self.id)
    

N_to_C = {
    'person'    : Person,
    'date'      : Date,
    'text'      : Text,
    'url'       : URL,
    'id'        : ID,
    'enumerated': Enumerated,
    }

C_to_N = {}

for k, v in N_to_C.items (): C_to_N [v] = k

