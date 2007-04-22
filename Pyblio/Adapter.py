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
Adapt a database schema to another one.

Given a database in, say, PubMed format, it is possible to plug an
adapter on top of it so that it looks as if the database is in, say,
BibTeX format instead.
"""

from gettext import gettext as _

from Pyblio.Store import Database
from Pyblio import Registry


class Adapter(Database):

    """ This class is a db built on top of another db, which behaves
    as if it were of a different schema."""

    header = None
    
    def __init__(self, base):
        self.base = base
        return

    def save(self):
        return self.base.save()

    def xmlread(self):
        raise RuntimeError(_("Adapter databases cannot be read from file"))
    
    
class ResultSetAdapter(object):
    def __init__(self, db, rs):
        self.db = db
        self.rs = rs

    def itervalues(self):
        for k in self.rs.iterkeys():
            yield self.db[k]

    def iteritems(self):
        for k in self.rs.iterkeys():
            yield k, self.db[k]

    def iterkeys(self):
        return self.rs.iterkeys()

    def add(self, k):
        self.rs.add(k)
        
    def __delitem__(self, k):
        del self.rs[k]

class ResultSetStoreAdapter(object):
    def __init__(self, db, adapted):
        self.db = db
        self.adapted = adapted

    def __getitem__ (self, k):
        return ResultSetAdapter(self.adapted, self.db.rs[k])

    def __delitem__ (self, k):
        del self.db.rs[k]

    def __iter__ (self):
        return iter(self.db.rs)

    def new(self, rsid=None):
        return ResultSetAdapter(self.adapted, self.db.rs.new())

    def update(self, result_set):
        return self.db.rs.update(result_set)

class OneToOneAdapter(Adapter):
    """ This adapter assumes a one-to-one mapping between the source
    and the target databases. The keys are not modified. """

    def __init__(self, base):
        Adapter.__init__(self, base)
        self.rs = ResultSetStoreAdapter(base, self)

    def source2target(self, record):
        """ Translates a record from the source db to the target db """
        raise NotImplemented('please override')

    def target2source(self, record):
        """ Translates a record from the target db to the source db """
        raise NotImplemented('please override')

    def add(self, record):
        return self.base.add(self.target2source(record))

    def __setitem__(self, key, record):
        self.base[key] = self.target2source(record)

    def __getitem__(self, key):
        return self.source2target(self.base[key])

    def has_key(self, key):
        return self.base.has_key(key)

    def _entries(self):
        e = self.base.entries
        class Looper:
            def itervalues(s):
                for v in e.itervalues():
                    yield self.source2target(v)
                return
            def iteritems(s):
                for k, v in e.iteritems():
                    yield k, self.source2target(v)
                return
            def iterkeys(s):
                return e.iterkeys()
            def __len__(s):
                return len(e)
            __iter__ = iterkeys
        return Looper()

    entries = property(_entries, None)

def adapt_schema(db, target_schema):
    """ Returns a database using the specified 'target_schema', and
    that maps the content of 'db', thanks to one or more
    L{Adapter}s. If no suitable adapter can be found, will raise an
    AdaptError()"""

    # for the moment, we only resolve direct hits. More clever
    # resolutions will hopefully be implemented.

    # search for target_schema in the adapters for the current schema:
    adapters = Registry.get(db.schema.id, 'adapters')
    
    for adapter in adapters:
        if adapter.target == target_schema:
            return adapter()(db)

    return None
