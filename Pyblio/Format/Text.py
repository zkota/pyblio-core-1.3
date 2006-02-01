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

"""
Transformation of the formatted record into a textual representation.
"""

def generate (t):
    """
    Actual text generator.

    @param t: the formatted representation
    @type  t: an S3 abstract tree, as returned when calling a formatted on a record

    @return: the text representing the cited record
    """
    if isinstance (t, (str, unicode)): return t
    return _map [t.tag] (t)
    
def _do_t (t):
    return ''.join (map (generate, t.children))

def _do_a (t):
    return '%s <%s>' % (''.join (map (generate, t.children)),
                        t.attributes ['href'])

def _do_br (t):
    return '\n'
    

_map = {
    't' : _do_t,
    'i' : _do_t,
    'b' : _do_t,
    'small' : _do_t,
    'a' : _do_a,
    'br': _do_br,
    }


