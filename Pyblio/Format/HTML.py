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

def _mkattrs(attrs):
    # merge the attributes, handling the special case of attributes
    # like _class -> class.
    return ' '.join(['%s="%s"' % (k.lstrip('_'), v)
                     for k, v in attrs.items()])

def generate (t):
    """
    Actual HTML generator.

    @param t: the formatted representation
    @type  t: an S3 abstract tree, as returned when calling a formatted on a record

    @return: the HTML code representing the cited record
    """
    
    if isinstance (t, (str, unicode)): return escape(t)
    return _map [t.tag](t)
    
def _do_t (t):
    return ''.join (map (generate, t.children))

def _do_i (t):
    return '<i>' + ''.join (map (generate, t.children)) + '</i>'
    
def _do_small (t):
    return '<small>' + ''.join (map (generate, t.children)) + '</small>'

def _do_span (t):
    attrs = _mkattrs(t.attributes)
    return '<span %s>' % attrs + ''.join (map (generate, t.children)) + '</span>'

def _do_b (t):
    return '<b>' + ''.join (map (generate, t.children)) + '</b>'
    
def _do_a (t):
    attrs = _mkattrs(t.attributes)
    return '<a %s>' % attrs + ''.join (map (generate, t.children)) + '</a>'

def _do_br (t):
    return '<br>'
    

_map = {
    't' : _do_t,
    'i' : _do_i,
    'b' : _do_b,
    'a' : _do_a,
    'br': _do_br,
    'small': _do_small,
    'span': _do_span,
    }


