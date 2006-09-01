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

""" Definition of the query language.

A query is composed of elementary search operations, which are
combined by boolean operations:

   >>> query = (AnyWord(u'findme') | Txo('type', item)) & ~ HasField('title')

"""

from Pyblio import Attribute, Exceptions
from Pyblio.Arrays import KeyArray, match_arrays


class _Constraint(object):

    def __and__(self, other):

        return _ANDed(self, other)

    def __or__(self, other):
        
        return _ORed(self, other)

    def __invert__(self):

        return _NOTed(self)

    def apply (self, fn, *args, **kargs):

        fn(self, *args, ** kargs)
        return

    def __len__(self):

        return 1



class _NOTed(_Constraint):

    def __init__(self, a):

        self.a = a
        return

    def __str__(self):
        return '~ %s' % str(self.a)

    def apply (self, fn, *args, **kargs):

        self.a.apply(fn, *args, **kargs)

    def run(self, db):

        ra = self.a.run(db)
        rb = db._q_all()

        a, b = match_arrays(ra.a, rb.a)

        return KeyArray(a=~a & b)


class _Pairs(_Constraint):

    def apply(self, fn, *args, **kargs):

        self.a.apply(fn, *args, **kargs)
        self.b.apply(fn, *args, **kargs)
        return

    def __len__(self):

        return len(self.a) + len(self.b)

    
class _ORed(_Pairs):

    def __init__(self, a, b):

        self.a = a
        self.b = b
        return

    def __str__(self):
        return '(%s | %s)' % (str(self.a),
                              str(self.b))

    def run(self, db):

        ra = self.a.run(db)
        rb = self.b.run(db)

        a, b = match_arrays(ra.a, rb.a)

        return KeyArray(a=a | b)
    
class _ANDed(_Pairs):

    def __init__(self, a, b):

        self.a = a
        self.b = b
        return

    def __str__(self):
        return '(%s & %s)' % (str(self.a),
                              str(self.b))

    def run(self, db):

        ra = self.a.run(db)
        rb = self.b.run(db)

        a, b = match_arrays(ra.a, rb.a)

        return KeyArray(a=a & b)


class Null(_Constraint):
    """ Does not search anything, but is useful when programatically
    constructing a query:

       >>> q = Null()
       >>> q = q & AnyWord(...)

    """
    
    def __and__(self, other):
        return other

    def __or__(self, other):
        return other

    def run(self, db):
        return db._q_all()


class AnyWord(_Constraint):

    """ Full text searching of a single word """

    def __init__(self, word):

        self.word = word
        return


    def validate(self, schema):
        return
    
    def run(self, db):
        return db._q_anyword(self)

    def __str__(self):
        return 'AnyWord(%s)' % repr(self.word)
    
class HasField(_Constraint):

    """ Matches when the record has the specified field."""

    def __init__(self, field):
        self.field = field
        return

    def validate(self, schema):

        try:
            t = schema[self.field]

        except KeyError:
            raise Exceptions.InvalidQuery('unknown field: %s' % self.field)

        return
    
    def run(self, db):
        return db._q_hasfield(self)


class Txo(_Constraint):

    """ Search items that belong to the corresponding txo """

    Attr = Attribute.Txo

    def __init__(self, field, txo):

        self.field = field
        self.txo   = txo
        return
        
    def validate(self, schema):

        try:
            t = schema[self.field].type

        except KeyError:
            raise Exceptions.InvalidQuery ('unknown field: %s' % self.field)

        if t is not self.Attr:
            raise Exceptions.InvalidQuery ('invalid field type: %s' % self.field)

        return

    def run(self, db):
        return db._q_txo(self)


class Queryable(object):

    """ A mixin that provides an (one day optimized) query engine to a store """

    def query(self, query, permanent=False):
        """ Perform a query and return a result set of the matching records. """
        self._q_check(query)

        r = query.run(self)
        return self._q_to_rs(r, permanent)


    def count(self, query):
        """ Perform a query and return the count of matching records. """

        self._q_check(query)
        
        return len(query.run(self))


    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _q_check(self, query):

        # Check if the query is well typed
        def check(const, schema):
            const.validate(schema)
            return
        
        query.apply(check, self.schema)
        return
    

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _q_hasfield(self, q):

        res = KeyArray()
        
        for e in self.entries.itervalues():

            try:
                fs = e[q.field]

            except KeyError:
                continue

            res.add(e.key)

        return res
    
    def _q_txo(self, q):

        res = KeyArray()
        
        full = self.schema.txo[q.txo.group].expand(q.txo.id)

        for e in self.entries.itervalues():

            try:
                fs = e[q.field]
                
            except KeyError:
                continue

            for f in fs:
                if f.id in full:
                    res.add(e.key)
                    break
            
        return res

    def _q_anyword(self, q):

        res = KeyArray()
        
        word = q.word.lower()
        
        for entry in self.entries.itervalues():

            found = False
            
            for attrs in entry.values ():

                for attr in attrs:
                    idx = attr.index ()
                
                    if word in idx:
                        found = True
                        break

                if found: break
                
            if not found: continue

            res.add(entry.key)

        return res
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _q_to_rs(self, res, permanent):

        rs = self.rs.add(permanent)

        for key in res:
            rs.add(key)
        
        return rs
    
    def _q_all(self):

        r = KeyArray()
        
        for k in self.entries:
            r.add(k)

        return r
    
            
