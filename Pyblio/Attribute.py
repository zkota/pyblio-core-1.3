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

import string

from xml import sax
from xml.sax.saxutils import escape, quoteattr

from gettext import gettext as _


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


class Text (unicode):
    ''' This class holds all the other fields (not an Author or a Date) '''

    def xmlwrite (self, fd):

        fd.write ('<text>%s</text>' % escape (self.encode ('utf-8')))
        return


class URL (str):
    ''' Holder for URL data (for example, the location of a database) '''

    def xmlwrite (self, fd):

        fd.write ('<url href=%s/>' % quoteattr (self.encode ('utf-8')))
        return


class Reference (str):
    ''' Holder for a reference to a bibliographic entry (which can be
    a crossref, a link to related entries, ... '''

    def __init__ (self, key):

        self.key = key
        return

    def xmlwrite (self, fd):
        fd.write ('<reference ref=%s/>' % quoteattr (str (self.key).encode ('utf-8')))
        return


N_to_C = {
    'person'   : Person,
    'date'     : Date,
    'text'     : Text,
    'url'      : URL,
    'reference': Reference,
    }

C_to_N = {}

for k, v in N_to_C.items (): C_to_N [v] = k

