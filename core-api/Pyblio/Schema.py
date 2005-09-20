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

""" Schema definition for a pyblio database. When a database is
created, the schema is instantiated from a template. The user can then
customize it.

At the moment, a schema contains a dictionnary of known document
types. For each document, it is possible to know the mandatory and
optional fields that describe the document. These fields are typed.

"""

from gettext import gettext as _

from xml.sax.saxutils import escape

from Pyblio.Attribute import N_to_C, C_to_N
from Pyblio import I18n, XML

from cElementTree import ElementTree

class SchemaError (Exception): pass

class Schema (dict):

    def __init__ (self, file = None):
        
        if file:
            tree = ElementTree (file = file)

            self.xmlread (tree.getroot ())
        return

    def xmlread (self, tree):

        def parseattr (attr):
            a = Attribute (attr.attrib ['id'])
            a.indexed = attr.attrib.get ('indexed', '0') == '1'
            a.group   = attr.attrib.get ('group', None)

            try:
                mx = attr.attrib ['max']
                a.range = (1, int (mx))
            except KeyError: pass
            
            try:
                a.type = N_to_C [attr.attrib ['type']]
            except KeyError:
                raise SchemaError ('attribute %s has an unknown type' % repr (a.id))

            for name in attr.findall ('name'):
                lang = name.attrib.get ('lang', '')
                a.names [lang] = name.text

            return a
        
        for attr in tree.findall ('./attribute'):
            a = parseattr (attr)

            if self.has_key (a.id):
                raise SchemaError ('duplicate attribute %s' % repr (a.id))

            for q in attr.findall ('./qualifiers/attribute'):
                qa = parseattr (q)
                if a.q.has_key (qa.id):
                    raise SchemaError ('duplicate qualifier %s for attribute %s' % (
                        repr (qa.id), repr (a.id)))

                a.q [qa.id] = qa
                
            self [a.id] = a
        return


    def xmlwrite (self, fd, embedded = False):

        if not embedded:
            fd.write ('<?xml version="1.0" encoding="utf-8"?>\n\n')
        
        fd.write ('<pyblio-schema>\n')

        keys = self.keys ()
        keys.sort ()

        for k in keys:
            self [k].xmlwrite (fd)
            fd.write ('\n')
            
        fd.write ('</pyblio-schema>\n')
        return
    
    
class Attribute:

    def __init__ (self, id):

        self.id = id

        self.type  = None

        # A grouping information (for Enumerated types for instance)
        self.group = None
        self.range = (1, None)
        
        self.names = {}

        self.q = {}
        return

    def _name_get (self):

        return I18n.lz.trn (self.names)

    name = property (_name_get)

    def xmlwrite (self, fd, offset = 1):

        ws = ' ' * offset
        
        if self.group is None: group = ""
        else:                  group = ' group="%s"' % self.group

        if self.indexed: idx = ' indexed="1"'
        else:            idx = ''

        if self.range [1] is None: card = ""
        else:                      card = ' max="%d"' % self.range [1]

        
        fd.write ('%s<attribute id="%s" type="%s"%s%s%s>\n' % (
            ws, self.id, C_to_N [self.type], card, group, idx))

        names = self.names.keys ()
        names.sort ()

        for k in names:
            v = escape (self.names [k].encode ('utf-8'))
            if k: k = ' lang="%s"' % k
            fd.write ('%s <name%s>%s</name>\n' % (ws, k, v))

        if self.q:
            keys = self.q.keys ()
            keys.sort ()

            fd.write ('\n')
            fd.write ('%s <qualifiers>\n' % ws)
            for k in keys: self.q [k].xmlwrite (fd, offset = offset + 2)
            fd.write ('%s </qualifiers>\n' % ws)
            
        fd.write ('%s</attribute>\n' % ws)
        return
