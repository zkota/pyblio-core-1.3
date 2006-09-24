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
(Data structures for stage 2 of the formatter)
"""


from Pyblio.Format.S3 import Tag
from Pyblio.Format.Base import Missing


def T(*args):
    return Tag('t', args, {})


class Text(object):

    def __init__(self, t):
        self.t = t
        return

    def __call__(self, record):
        return unicode(self.t)

    def __repr__(self):
        return "S2.Text(%r)" % self.t

class Sum(object):

    def __init__(self, a, b):
        self.a = a
        self.b = b
        return

    def __call__(self, record):
        # The sum fails if one of the two members fails
        return T(self.a(record), self.b(record))

    def __repr__(self):
        return "S2.Sum(%r, %r)" % (self.a, self.b)

    
    
class Or(object):

    def __init__(self, a, b):
        self.a = a
        self.b = b
        return

    def __call__(self, record):
        # Return b except if a is defined
        try:
            return self.a(record)
        except Missing:
            return self.b(record)

    def __repr__(self):
        return "S2.Or(%r, %r)" % (self.a, self.b)

    
class Join(object):

    def __init__(self, middle, last, children):
        self.middle = middle
        self.last = last
        self.children = children
        return
    
    def __call__(self, record):

        middle = self.middle(record)
        last = self.last(record)

        ls = []
                    
        for arg in self.children:
            if isinstance (arg, (str, unicode)):
                ls.append (arg)
                continue

            try: v = arg(record)
            except Missing: continue

            if isinstance (v, (list, tuple)):
                ls.extend(v)
            else:
                ls.append (v)

        if len(ls) == 0:
            raise Missing('empty join')

        f = [ls.pop (0)]
        
        while ls:
            l = ls.pop (0)
            if ls: f.append(middle)
            else:  f.append(last)

            f.append(l)

        return T(*f)

    def __repr__(self):
        return "S2.Join(%r, %r, %r)" % (
            self.middle, self.last, self.children)


class Switch(object):

    def __init__(self, fetch, switch, default):
        self.fetch = fetch
        self.switch = switch
        self.default = default
        return

    def __call__(self, record):
        try:
            txo = self.fetch(record)
        except (KeyError, IndexError), msg:
            if self.default:
                c = self.default
            else:
                raise Missing('no such attribute in record: %s' % str(msg))
        else:
            c = self.switch.get(txo, self.default)

        if not c:
            raise Missing('unsupported switch case')

        return c(record)
    


