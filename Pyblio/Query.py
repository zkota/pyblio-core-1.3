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


class _Constraint (object):

    def __and__ (self, other):

        return _ANDed (self, other)

    def __or__ (self, other):
        
        return _ORed (self, other)

    def __invert__ (self):

        return _NOTed (self)

    def apply (self, fn, * args, **kargs):

        fn (self, * args, ** kargs)
        return

    def __len__ (self):

        return 1



class _NOTed (_Constraint):

    def __init__ (self, a):

        self.a = a
        return

    def __str__ (self):
        return '~ %s' % str (self.a)

    def apply (self, fn, * args, **kargs):

        self.a.apply (fn, * args, ** kargs)


class _Pairs (_Constraint):

    def apply (self, fn, * args, **kargs):

        self.a.apply (fn, * args, ** kargs)
        self.b.apply (fn, * args, ** kargs)
        return

    def __len__ (self):

        return len (self.a) + len (self.b)

    
class _ORed (_Pairs):

    def __init__ (self, a, b):

        self.a = a
        self.b = b
        return

    def __str__ (self):
        return '(%s | %s)' % (str (self.a),
                              str (self.b))

    
class _ANDed (_Pairs):

    def __init__ (self, a, b):

        self.a = a
        self.b = b
        return

    def __str__ (self):
        return '(%s & %s)' % (str (self.a),
                              str (self.b))


class AnyWord (_Constraint):

    """ Full text searching of a single word """

    def __init__ (self, word):

        self.word = word
        return


    def validate (self, schema):
        return
    

class HasField (_Constraint):

    """ Matches when the record has the specified field."""

    def __init__ (self, field):
        self.field = field
        return

    def validate (self, schema):

        try:
            t = schema [self.field]

        except KeyError:
            raise Exceptions.InvalidQuery ('unknown field: %s' % self.field)

        return
    

class Txo (_Constraint):

    """ Search items that belong to the corresponding txo """

    Attr = Attribute.Txo

    def __init__ (self, field, txo):

        self.field = field
        self.txo   = txo
        return
        
    def validate (self, schema):

        try:
            t = schema [self.field].type

        except KeyError:
            raise Exceptions.InvalidQuery ('unknown field: %s' % self.field)

        if t is not self.Attr:
            raise Exceptions.InvalidQuery ('invalid field type: %s' % self.field)

        return


class Queryable (object):

    """ A mixin that provides an (one day optimized) query engine to a store """

    def query (self, query, permanent = False):

        # Check if the query is well typed
        def check (const, schema):
            const.validate (schema)
            return
        
        query.apply (check, self.schema)

        return self._q_run (query, permanent)


    def _q_run (self, query, permanent):

        # Otherwise, call the corresponding boolean method
        if isinstance (query, _ORed):
            return self._q_or  (query, permanent)

        if isinstance (query, _ANDed):
            return self._q_and (query, permanent)

        if isinstance (query, _NOTed):
            return self._q_not (query, permanent)

        # This must be a single query
        res = self.rs.add (permanent)
        self._q_single (query, res)
        
        return res


    def _q_or (self, query, permanent):

        ra = self._q_run (query.a, permanent)
        rb = self._q_run (query.b, False)

        for k in rb: ra.add (k)

        return ra

        
    def _q_and (self, query, permanent):

        rf = self.rs.add (permanent)

        ra = self._q_run (query.a, False)
        rb = self._q_run (query.b, False)

        for k in ra:
            if rb.has_key (k): rf.add (k)

        return rf


    def _q_not (self, query, permanent):

        rf = self.rs.add (permanent)
        rs = self._q_run (query.a, False)

        for k in self.entries.iterkeys ():
            if k in rs: continue
            rf.add (k)

        return rf
        
    def _q_single (self, q, res):
        
        name = q.__class__.__name__
        
        try:
            fn = getattr (self, '_q_%s' % name.lower ())
            
        except AttributeError:
            raise Exceptions.InvalidQuery ('query on type %s unsupported' % name)

        fn (q, res)

        return


    def _q_hasfield (self, q, res):

        for e in self.entries.itervalues ():

            try: fs = e [q.field]
            except KeyError: continue

            res.add (e.key)

        return
    
    def _q_txo (self, q, res):

        full = self.txo [q.txo.group].expand (q.txo.id)

        for e in self.entries.itervalues ():

            try:             fs = e [q.field]
            except KeyError: continue

            for f in fs:
                if f.id in full:
                    res.add (e.key)
                    break
            
        return

    def _q_anyword (self, q, res):

        word = q.word.lower ()
        
        for entry in self.entries.itervalues ():

            found = False
            
            for attrs in entry.values ():

                for attr in attrs:
                    idx = attr.index ()
                
                    if word in idx:
                        found = True
                        break

                if found: break
                
            if not found: continue

            res.add (entry.key)

        return
    
