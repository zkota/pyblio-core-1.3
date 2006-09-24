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

"""
Definition of the sort language.

Sorting according to fields A (ascending) and B (descending) can be
written::

 OrderBy ('A') & OrderBy ('B', asc = False)

"""


def compare (a, b):

    for (sa, va), (sb, vb) in zip (a, b):
        r = cmp (va, vb)
        if r: return r * sa

    return 0

class _Base (object):

    def __and__ (self, other):
        return _Seq (self, other)


class _Seq (_Base):

    def __init__ (self, a, b):
        self.a = a
        self.b = b
        return

    def cmp_key (self, rec):
        return self.a.cmp_key (rec) + self.b.cmp_key (rec)
    

class OrderBy (_Base):

    def __init__ (self, field, asc = True):

        self.field = field

        if asc: self.asc = +1
        else:   self.asc = -1
        return

    def cmp_key (self, rec):

        try:
            parts = [ x.sort () for x in rec [self.field] ]

        except KeyError:
            parts = []
                                                         
        return (self.asc, parts),
