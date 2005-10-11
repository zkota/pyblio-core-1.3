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

""" Basic data types that can be used as attributes for a L{Record
<Pyblio.Store.Record>}"""

import string, re, urlparse, os

from xml import sax
from xml.sax.saxutils import escape, quoteattr

from gettext import gettext as _

re_split = re.compile (r'[^\w]+', re.UNICODE)


class Qualified (object):
    """ Mix-in class that provides qualifiers to attributes, making
    them behave like composite data types (but not arbitrarily nested
    data, though)"""
    
    def _xmlsubwrite (self, fd, offset = 1):
        ws = ' ' * offset
        
        for k, vs in self.q.items ():
            fd.write (ws + '<attribute id=%s>\n' % quoteattr (k))
            for v in vs:
                v.xmlwrite (fd, offset + 1)
                fd.write ('\n')
            fd.write (ws + '</attribute>\n')
        return

    def deep_equal (self, other):
        for k in self.q:
            if not k in other.q or not len (self.q [k]) == len (other.q [k]):
                return False
            
            for x, y in zip (self.q [k], other.q [k]):
                if not x.deep_equal (y):
                    return False
                
        for k in other.q:
            if not k in self.q:
                return False
        return True           
                
                  
class UnknownContent (Qualified):
    """
    This is only a temporary Type. It is used, when you add qualifiers before you
    add the main field to a record. Trying to store it will raise an error. 
    """
    def __init__ (self):
        self.q = {}

    def xmlwrite (self, fd, offset = 0):
        #TODO: add this to unit test: no host but qualifiers        
        raise Exceptions.ParserError ("Attribute.UnknownContent has qualifiers, "\
                                      "but is empty: %s" % self.q)

    def deep_equal (self, other):
        if not isinstance (other, UnknownContent): return False
        return Qualified.deep_equal (self, other)
        
class Person (Qualified):
    ''' A person name '''

    def __init__ (self, honorific = None, first = None, last = None, lineage = None,
                  xml = None):

        self.q = {}

        self.honorific = honorific
        self.first     = first
        self.last      = last
        self.lineage   = lineage
        return

    def xmlread (k, xml, inside = False):
        p = k ()
        
        for f in ('honorific', 'first', 'last', 'lineage'):
            setattr (p, f, xml.attrib.get (f, None))

        return p
    
    xmlread = classmethod (xmlread)
    
    def xmlwrite (self, fd, offset = 0):

        ws = ' ' * offset
        
        data = []
        for f in ('honorific', 'first', 'last', 'lineage'):
            v = getattr (self, f)
            if v:
                data.append ('%s=%s' % (f, quoteattr (v.encode ('utf-8'))))

        data = ' '.join (data) 

        if not self.q:
            fd.write (ws + '<person %s/>' % data)
        else:
            fd.write (ws + '<person %s>\n'  % data)
            self._xmlsubwrite (fd, offset + 1)
            fd.write (ws + '</person>')
            
        return
    
    def index (self):
        idx = []
        for x in (self.first, self.last):
            if x: idx = idx + map (string.lower, x.split ())
            
        return filter (None, idx)
    

    def sort (self):
        return (u'%s\0%s' % (self.last or '', self.first or '')).lower ()


    def __eq__ (self, other):

        return self.last == other.last   and \
               self.first == other.first and \
               self.honorific == other.honorific and \
               self.lineage == other.lineage

    def __ne__ (self, other):

        return self.last != other.last   or \
               self.first != other.first or \
               self.honorific != other.honorific or \
               self.lineage != other.lineage

    def deep_equal (self, other):
        if not self == other or not isinstance (other, Person):
            return False        
        return Qualified.deep_equal (self, other)        
    
    def __repr__ (self):
        return "Person (%s, %s)" % (repr(self.last), repr(self.first))

    def __hash__ (self):
        return hash ((self.last, self.first, self.lineage, self.honorific))
        
class Date (Qualified):
    ''' A date '''

    def __init__ (self, year = None, month = None, day = None):
        self.q = {}

        self.year  = year
        self.month = month
        self.day   = day
        return

    def xmlread (k, xml):
        d = k ()
        
        for f in ('year', 'month', 'day'):
            v = xml.attrib.get (f, None)
            if v: setattr (d, f, int (v))
            
        return d
    
    xmlread = classmethod (xmlread)


    def xmlwrite (self, fd, offset = 0):

        ws = ' ' * offset
        
        data = []
        for f in ('year', 'month', 'day'):
            v = getattr (self, f)
            if v:
                data.append ('%s="%d"' % (f, v))
        
        fd.write (ws + '<date %s' % string.join (data, ' '))
        if self.q:
            fd.write ('>\n')
            self._xmlsubwrite (fd, offset + 1)
            fd.write (ws + '</date>')
        else:
            fd.write ('/>')
        return

    def index (self):
        return []

    def sort (self):
        return '%.4d%.2d%.2d' % (self.year or 0,
                                 self.month or 0,
                                 self.day or 0)

    def __cmp__ (self, other):
        if not isinstance (other, Date): return 1
        
        for x, y in ((self.year, other.year),
                     (self.month, other.month),
                     (self.day, other.day)):
            a = cmp (x, y)
            if a: return a

        return 0

    def deep_equal (self, other):
        if not self == other or not isinstance (other, Date):
            return False        
        return Qualified.deep_equal (self, other)        

        
    def __hash__ (self):
        return hash ((self.year, self.month, self.day))


    def __repr__ (self):

        return 'Date (year = %s, month = %s, day = %s)' % (
            repr (self.year), repr (self.month), repr (self.day))


class Text (unicode, Qualified):
    ''' A textual data '''

    def __init__ (self, text = u''):
        unicode.__init__ (self, text)
        self.q = {}
        return
    
    def xmlread (k, xml):
        content = xml.find ('./content')
        if content is not None:
            return k (content.text)
        else:
            return k (xml.text)
    
    xmlread = classmethod (xmlread)

    def xmlwrite (self, fd, offset = 0):
        ws = ' ' * offset

        if self.q:
            fd.write (ws + '<text>\n')
            fd.write (ws + ' <content>%s</content>\n' % escape (self.encode ('utf-8')))
            self._xmlsubwrite (fd, offset + 1)
            fd.write (ws + '</text>')
        else:
            fd.write (ws + '<text>%s</text>' % escape (self.encode ('utf-8')))
        return

    def index (self):
        idx = map (string.lower, re_split.split (self))
        return filter (None, idx)

    def sort (self):
        return self.lower ()
    
    def deep_equal (self, other):
        if not self == other or not isinstance (other, Text):
            return False        
        return Qualified.deep_equal (self, other)        


class URL (str, Qualified):
    ''' An URL '''

    def __init__ (self, text = ''):
        self.q = {}
        str.__init__ (self, text)
        return
        
    def xmlread (k, xml):
        return k (xml.attrib ['href'])
    
    xmlread = classmethod (xmlread)
    
    def xmlwrite (self, fd, offset = 0):
        ws = ' ' * offset

        fd.write (ws + '<url href=%s' % quoteattr (self.encode ('utf-8')))
        if self.q:
            fd.write ('>\n')
            self._xmlsubwrite (fd, offset + 1)
            fd.write (ws + '</url>')
        else:
            fd.write ('/>')
        return

    def index (self):
        # do not index the document suffix, only the server name and document page
        url = urlparse.urlparse (self)
        
        idx = re_split.split (url [1]) + \
              re_split.split (os.path.splitext (url [2]) [0])
        
        return filter (None, idx)

    def sort (self):
        return self

    def deep_equal (self, other):
        if not self == other or not isinstance (other, URL):
            return False        
        return Qualified.deep_equal (self, other)        


class ID (unicode, Qualified):

    ''' An external identifier '''

    def __init__ (self, text = u''):
        self.q = {}
        unicode.__init__ (self, text)
        return

    def xmlread (k, xml):
        return k (xml.attrib ['value'])
    
    xmlread = classmethod (xmlread)
    
    def xmlwrite (self, fd, offset = 0):
        ws = ' ' * offset
        fd.write (ws + '<id value=%s' % quoteattr (self.encode ('utf-8')))
        if self.q:
            fd.write ('>\n')
            self._xmlsubwrite (fd, offset + 1)
            fd.write (ws + '</id>')
        else:
            fd.write ('/>')
        return

    def index (self):
        return []
    
    def sort (self):
        return self

    def deep_equal (self, other):
        if not self == other or not isinstance (other, ID):
            return False        
        return Qualified.deep_equal (self, other)        


class Txo (Qualified):

    """ Relationship to a Taxonomy """

    def __init__ (self, item = None):
        self.q = {}
        if item:
            self.group = item.group
            self.id    = item.id
        else:
            self.group = None
            self.id    = None
        return

    def xmlread (k, xml):
        txo = k ()
        txo.group = xml.attrib ['group']
        txo.id    = int (xml.attrib ['id'])

        return txo
    
    xmlread = classmethod (xmlread)
    
    def xmlwrite (self, fd, offset = 0):
        ws = ' ' * offset
        fd.write (ws + '<txo group="%s" id="%d"' % (self.group, self.id))

        if self.q:
            fd.write ('>\n')
            self._xmlsubwrite (fd, offset + 1)
            fd.write (ws + '</txo>')
        else:
            fd.write ('/>')
        return

    def index (self):
        return [ '%s/%d' % (self.group, self.id) ]
    
    def sort (self):
        return '%s/%d' % (self.group, self.id)

    def __repr__ (self):

        return 'Txo (%s, %s)' % (`self.group`, `self.id`)

    def __cmp__ (self, other):

        return cmp (self.group, other.group) or cmp (self.id, other.id)

    def deep_equal (self, other):
        if not self == other or not isinstance (other, Txo):
            return False        
        return Qualified.deep_equal (self, other)        

    def __hash__ (self):
        return hash ((self.group, self.id))
    
N_to_C = {
    'person'    : Person,
    'date'      : Date,
    'text'      : Text,
    'url'       : URL,
    'id'        : ID,
    'txo'       : Txo,
    }

C_to_N = {}

for k, v in N_to_C.items (): C_to_N [v] = k

