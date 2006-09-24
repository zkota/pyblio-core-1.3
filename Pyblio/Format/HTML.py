# This file is part of pybliographer
# 
# Copyright (C) 1998-2006 Frederic GOBRY
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

"""
Transformation of the formatted record into an HTML representation.
"""

from xml.sax.saxutils import escape
from StringIO import StringIO

from Pyblio.Format.Generator import Generator as Base

def _mkattrs(attrs):
    # merge the attributes, handling the special case of attributes
    # like _class -> class.
    return ' '.join(['%s="%s"' % (k.lstrip('_'), v)
                     for k, v in attrs.items()])


class Generator(Base):

    def __init__(self, fd):
        self.fd = fd
        return
    
    def do_string(self, t):
        self.fd.write(escape(t))
    
    def do_i(self, t):
        self.fd.write('<i>')
        for s in t.children: self(s)
        self.fd.write('</i>')

    def do_small(self, t):
        self.fd.write('<small>')
        for s in t.children: self(s)
        self.fd.write('</small>')

    def do_span(self, t):
        attrs = _mkattrs(t.attributes)
        self.fd.write('<span %s>' % attrs)
        for s in t.children: self(s)
        self.fd.write('</span>')

    def do_b(self, t):
        self.fd.write('<b>')
        for s in t.children: self(s)
        self.fd.write('</b>')

    def do_a(self, t):
        attrs = _mkattrs(t.attributes)
        self.fd.write('<a %s>' % attrs)
        for s in t.children: self(s)
        self.fd.write('</a>')

    def do_br(self, t):
        self.fd.write('<br>')
    
    def begin_biblio(self):
        self.fd.write('<table>\n')

    def end_biblio(self):
        self.fd.write('</table>')

    def begin_reference(self, key):
        self.fd.write('<tr><td>[%s]</td><td>' % escape(key))

    def end_reference(self, key):
        self.fd.write('</td></tr>\n')


def generate(t):
    """ Convenience function that generates the HTML in a string """
    fd = StringIO()
    g = Generator(fd)
    g(t)

    return fd.getvalue()
    
