# This file is part of pybliographer
# 
# Copyright (C) 1998-2008 Frederic GOBRY
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

"""Easy manipulation of BibTeX files.

Usage:

db = BeefTeX('sample.bib')

# do stuff with file

db.Save()

"""

from Pyblio.Parsers.Syntax.BibTeX import Parser

class _Link(object):
    def __init__(self, value, prev, next):
        self.value = value
        self.prev = prev
        self.next = next

    def __repr__(self):
        return 'Linked(%s) -> %s' % (repr(self.value),
                                     repr(self.next))

class _LinkedList(object):
    def __init__(self):
        self.first = None
        self.last = None

    def Append(self, value):
        l = _Link(value, self.last, None)
        if self.last:
            assert self.last.next is None
            self.last.next = l
        else:
            assert self.first is None
            self.first = l
        self.last = l
        return l

    def Delete(self, link):
        if link.prev:
            link.prev.next = link.next
        else:
            assert self.first is link
            self.first = link.next
        if link.next:
            link.next.prev = link.prev
        else:
            assert self.last is link
            self.last = link.prev
        link.prev = None
        link.next = None

    def __iter__(self):
        l = self.first
        while l:
            yield l.value
            l = l.next


class BeefTeX(object):
    """BibTeX file manipulation tool."""

    def __init__(self, filename, charset='UTF-8'):
        self.charset = charset
        self.filename = filename

        self.content = _LinkedList()
        self.records = {}

        if self.filename:
            fh = open(filename)
            for record in Parser.read(fh, self.charset):
                l = self.content.Append(record)
                if isinstance(record, Parser.Record) and record.key:
                    # yay, a real record!
                    self.records[record.key.flat()] = l

    def Save(self, filename=None):
        fh = open(filename or self.filename, 'w')
        for record in self.content:
            fh.write(record.tobib().encode(self.charset))

    def Keys(self):
        return self.records.keys()

    def Get(self, key):
        return self.records[key].value

    def Delete(self, key):
        l = self.records[key]
        del self.records[key]
        self.content.Delete(l)
