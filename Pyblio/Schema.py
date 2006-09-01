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

from Pyblio.Attribute import N_to_C, C_to_N, Txo
from Pyblio import I18n

from cElementTree import ElementTree

class SchemaError (Exception): pass

class Schema (dict):

    def __init__ (self, file = None):

        self.id = None
        self.names = {}
        self.txo = {}
        
        if file:
            tree = ElementTree (file = file)
            self.xmlread (tree.getroot ())
        return

    def _name_get (self):
        return I18n.lz.trn (self.names)

    name = property (_name_get)


    def xmlread (self, tree):
        self.id = tree.attrib.get('id', None)
        
        for name in tree.findall ('./name'):
            lang = name.attrib.get ('lang', '')
            self.names [lang] = name.text


        def parseattr (attr):
            aid = attr.attrib ['id']
            
            try:
                atype = N_to_C [attr.attrib ['type']]
            except KeyError:
                raise SchemaError ('attribute %s has an unknown type' % repr (aid))

            if atype is Txo:
                a = TxoAttribute(aid)
            else:
                a = Attribute (aid)

            a.type = atype
            a.indexed = attr.attrib.get ('indexed', '0') == '1'

            try:
                mx = attr.attrib ['max']
                a.range = (1, int (mx))
            except KeyError: pass
            
            for name in attr.findall ('name'):
                lang = name.attrib.get ('lang', '')
                a.names [lang] = name.text

            a.xmlread(self, attr)
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


        # Read the Txo groups predefined in the schema itself
        for attr in tree.findall ('./txo-group'):
            g = TxoGroup()
            g.xmlread(attr)

            self.txo[g.group] = g
        return


    def xmlwrite (self, fd, embedded = False):

        if not embedded:
            fd.write ('<?xml version="1.0" encoding="utf-8"?>\n\n')

        fd.write ('<pyblio-schema')
        if self.id:
            fd.write(' id="%s"' % escape(self.id))
        fd.write('>\n')


        keys = self.names.keys ()
        keys.sort ()

        for k in keys:
            v = self.names [k]
            if k:
                lang = ' lang="%s"' % k
            else:
                lang = ''
            
            fd.write (' <name%s>%s</name>\n' % (
                lang, escape (v.encode ('utf-8'))))

        if keys: fd.write('\n')
        
        keys = self.keys ()
        keys.sort ()

        for k in keys:
            self[k].xmlwrite (fd)
            fd.write('\n')
            
        ks = self.txo.keys()
        ks.sort()

        for k in ks:
            self.txo[k].xmlwrite(fd)
        
        fd.write ('</pyblio-schema>\n')
        return
    
    
class Attribute(object):

    def __init__ (self, id):

        self.id = id

        self.type  = None

        self.range = (1, None)
        
        self.names = {}

        self.q = {}
        return

    def __repr__ (self):

        return 'Attribute (%s, %s, %s)' % (
            repr (self.id), repr (self.type), repr (self.q))


    def _name_get (self):

        return I18n.lz.trn (self.names)

    name = property (_name_get)

    def _xmlopen(self, fd, offset, **extra):
        ws = ' ' * offset

        names = self.names.keys ()
        names.sort ()

        if self.indexed: idx = ' indexed="1"'
        else:            idx = ''

        if self.range [1] is None: card = ""
        else:                      card = ' max="%d"' % self.range [1]

        if extra:
            extra = ' ' + ' '.join(['%s="%s"' % x for x in extra.iteritems()])
        else:
            extra = ''
        
        fd.write ('%s<attribute id="%s" type="%s"%s%s%s>\n' % (
            ws, self.id, C_to_N [self.type], card, idx, extra))

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


    def xmlread(self, schema, attr):
        # We do not need to extract additional data from here
        return
        
    def xmlwrite (self, fd, offset = 1):

        ws = ' ' * offset
        
        self._xmlopen(fd, offset)
        
        fd.write ('%s</attribute>\n' % ws)
        return


class TxoAttribute(Attribute):

    def __repr__ (self):

        return 'TxoAttribute (%s, %s, %s, %s)' % (
            repr (self.id), repr (self.type), repr (self.group),
            repr (self.q))

    def xmlread(self, schema, attr):
        # fetch the possible txo-items
        self.group = attr.attrib ['group']

        g = TxoGroup()
        g.group = self.group
        
        schema.txo.setdefault(self.group, g)
        return
    
    def xmlwrite (self, fd, offset=1):

        ws = ' ' * offset

        self._xmlopen(fd, offset, group=self.group)

        fd.write ('%s</attribute>\n' % ws)
        return


class TxoItem (object):

    """ Definition of a taxonomy item.

    This item can then be reused as the argument for L{Attribute.Txo}
    creation. A taxonomy item can be seen as a value in a enumeration
    of possible values. Compared to a I{simple} enumeration, it has
    the additional property of being hierachical. For instance, you
    could define a taxonomy of document types::

      - publication
         - article
            - peer-reviewed
            - not peer-reviewed
         - conference paper
      - unpublished
         - report

    ...and use this taxonomy to fill an attribute of your records. If
    you use L{Pyblio.Query} to search for the item I{article}, you
    will retrieve all the records which contain one of I{article},
    I{peer-reviewed} or I{not peer-reviewed}.
    """

    def __init__ (self):

        self.id     = None
        self.group  = None
        self.parent = None
        
        self.names = {}
        return

    def _name_get (self):

        return I18n.lz.trn (self.names)

    name = property (_name_get)
    

    def xmlwrite (self, fd, space = ''):

        keys = self.names.keys ()
        keys.sort ()

        for k in keys:
            v = self.names [k]
            if k:
                lang = ' lang="%s"' % k
            else:
                lang = ''
            
            fd.write ('  %s<name%s>%s</name>\n' % (
                space, lang, escape (v.encode ('utf-8'))))
        
        return
    
    def __repr__ (self):

        return 'TxoItem(%s, %s)' % (repr(self.group), repr(self.id))


class TxoGroup(dict):

    def __init__(self):
        dict.__init__(self)

        self.group = None

        # the cache for searching by name
        self._byname = {}
        return
    
    def __repr__ (self):
        return 'TxoGroup (%s)' % (
            repr (self.group))

    def byname (self, name):
        return self._byname[name]
    
    def xmlread(self, attr):
        # fetch the possible txo-items
        self.group = attr.attrib['id']

        def nesting(tree, parent):
            for item in tree.findall ('./txo-item'):
                i = TxoItem ()

                i.id = int(item.attrib['id'])
                i.parent = parent
                i.group = self.group
                
                for name in item.findall ('./name'):
                    lang = name.attrib.get ('lang', '')
                    i.names[lang] = name.text

                if 'C' in i.names:
                    cname = i.names['C']
                    if cname in self._byname:
                        raise SchemaError('name %r appears more than once' % cname)
                    
                    self._byname[cname] = i
                    
                self[i.id] = i

                nesting (item, i.id)

        nesting(attr, None)
        return

    
    def _reverse (self):
        """ Create the reversed taxonomy tree """
        
        children = { None: [] }

        for k in self.keys ():
            children [k] = []

        for v in self.values ():
            children [v.parent].append (v.id)

        return children

    def expand (self, k):
        """ Return a txo and all its children """

        children = self._reverse ()

        full = []
        for c in children [k]:
            full = full + self.expand (c)

        full.append (k)
        
        return full

    
    def xmlwrite (self, fd, offset=1):

        ws = ' ' * offset

        if not self.keys(): return
        
        fd.write ('%s<txo-group id="%s">\n' % (ws, self.group))
            
        children = self._reverse()

        def subwrite (node, depth = 0):
            child = self [node]

            space = ' ' * (offset + depth)
            
            fd.write (' %s<txo-item id="%d">\n' % (
                space, child.id))

            child.xmlwrite (fd, space)

            for n in children [node]:
                subwrite (n, depth + 1)
                
            fd.write (' %s</txo-item>\n' % space)
            return

        for n in children [None]:
            subwrite (n)
        
        fd.write ('%s</txo-group>\n\n' % ws)
        return


