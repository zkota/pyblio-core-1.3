# -*- coding: utf-8 -*-
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
Generate citation keys.
"""

from sets import Set

def _alphaloop():
    a = ord('a')
    while a <= ord('z'):
        yield chr(a)
        a += 1
    return

class Unambiguous(object):
    """ Base class to handle caching of generated keys. Ensures that
    the same uid will always get the same key."""
    
    def __init__(self, db):
        self.map = {}
        self.db = db
        return
    
    def cache_lookup(self, uid):
        if self.map.has_key(uid):
            return self.map[uid]
        return None

    def cache_update(self, uid, k):
        self.map[uid] = k
        return k

    def make_key(self, uid):
        k = self.cache_lookup(uid)
        if k:
            return k

        k = self._generate(uid)
        return self.cache_update(uid, k)


class Alpha(Unambiguous):
    """ Base class to add a disambiguation letter after generated keys
    that clash with already generated ones."""
    
    def __init__(self, db):
        Unambiguous.__init__(self, db)
        self.seen = Set()
        return
    
    def cache_update(self, uid, k):
        if k in self.seen:
            extra = _alphaloop()
            while 1:
                full = k + ':' + extra.next()
                if full not in self.seen:
                    k = full
                    break

        self.seen.add(k)
        return Unambiguous.cache_update(self, uid, k)


class Numeric(Unambiguous):
    """ Return a numeric key for documents, in the order in which they
    are requested."""
    
    def __init__(self, db):
        Unambiguous.__init__(self, db)
        self.current = 1
        return

    def _generate(self, uid):
        k = str(self.current)
        self.current += 1
        return k

    
def document_order(uids):
    """ Return citations in their order of appearance in the
    document. This is the order in which they are presented in input,
    except that we don't want duplicates. """
    seen = Set()
    for uid, key in uids:
        if uid in seen:
            continue

        seen.add(uid)
        yield (uid, key)
    return
