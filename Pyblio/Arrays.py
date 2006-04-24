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
Result sets and indexes implemented on top of numpy arrays.

"""

import numpy

from numpy import array, resize, zeros, fromstring

from math import ceil, log

from Pyblio.Store import Key

def _to_power(size):
    """ Return the power of two immediately above 'size' """
    try:
        return 2 ** int(ceil(log(size, 2)))
    except OverflowError:
        return 1


class KeyArray(object):
    """ A growing array of Pyblio keys. """
    
    def __init__(self, initial=1, a=None, s=None):
        
        if a is not None:
            self.a = a
        elif s is not None:
            self.a = fromstring(s, bool)
        else:
            self.a = zeros(_to_power(initial), bool)
        return


    def tostring(self):
        return self.a.tostring()

    
    def add(self, k):
        """ Set the key 'k' in the array """
        k -= 1

        try:
            self.a[k] = True
        except IndexError:
            c = len(self.a)
    
            largest = max(c, _to_power(k+1))
            self.a = resize(self.a, (largest,))
            self.a[c:] = False

            self.a[k] = True
        return

    def __delitem__(self, k):
        """ Remove key 'k' from the array """
        self.a[k-1] = False
        return


    def __len__(self):
        return numpy.sum(self.a)


    def __iter__(self):
        for key, status in enumerate(self.a):
            if status:
                yield Key(key + 1)
        return

    
def match_arrays(a,b):
    """ Ensure a and b have the same size, enlarging the smallest of
    the two if needed."""
    
    la = len(a)
    lb = len(b)

    if la == lb:
        return a,b

    if la > lb:
        b = resize(b, la)
        b[lb:] = False

    elif lb > la:
        a = resize(a, lb)
        a[la:] = False

    return a, b
