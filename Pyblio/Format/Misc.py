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
Miscellanous formatting helpers.
"""

from Pyblio.Format.DSL import lazy

def plural(record, sequence, zero=None, one=None, two=None, more=''):
    """
    Generate different outputs depending on the number of items in a sequence.

       >>> editor = initialsLast(all('editor')) + plural('editor',
                                                         one=', editor',
                                                         more=', editors')

    @param sequence:
        The sequence whose item count will be used to generate the output.
    @type  sequence:
        list

    @param zero:
        value returned when the sequence is empty
    @param one:
        value returned when the sequence has one item
    @param two:
        value returned when the sequence has two items
    @param more:
        value returned when the sequence has more than two items

    @note when a given parameter is not provided but should be returned,
      then the default is to use the value of the L{more} parameter.
    """

    l = len (sequence(record))
    
    if l == 0 and zero is not None:
        return zero(record)
    elif l == 1 and one is not None:
        return one(record)
    elif l == 2 and two is not None:
        return two(record)
    else:
        return more(record)

plural = lazy (plural)
