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

""" Definition of the query language """

from Pyblio import Attribute, Exceptions


class Constraint (object):

    def __and__ (self, other):

        return ANDed (self, other)

    def __or__ (self, other):
        
        return ORed (self, other)

    def apply (self, fn, * args, **kargs):

        fn (self, * args, ** kargs)
        return

    def __len__ (self):

        return 1


class Pairs (Constraint):

    def apply (self, fn, * args, **kargs):

        fn (self.a, * args, ** kargs)
        fn (self.b, * args, ** kargs)
        return

    def __len__ (self):

        return len (self.a) + len (self.b)

    
class ORed (Pairs):

    def __init__ (self, a, b):

        self.a = a
        self.b = b
        return

    def __str__ (self):
        return '(%s | %s)' % (str (self.a),
                              str (self.b))

    
class ANDed (Pairs):

    def __init__ (self, a, b):

        self.a = a
        self.b = b
        return

    def __str__ (self):
        return '(%s & %s)' % (str (self.a),
                              str (self.b))


class AnyWord (Constraint):

    """ Full text searching of a single word """

    def __init__ (self, word):

        self.word = word
        return


    def validate (self, schema):
        return
    

class Txo (Constraint):

    """ Search items that belong to the corresponding txo """

    Attr = Attribute.Txo

    def __init__ (self, field, id):

        self.field = field
        self.id = id
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

        # Check for a single query
        if len (query) > 1:
            raise Exceptions.InvalidQuery ('only support single queries')


        name = query.__class__.__name__
        
        try:
            fn = getattr (self, '_q_%s' % name.lower ())
            
        except AttributeError:
            raise Exceptions.InvalidQuery ('query on type %s unsupported' % name)
        
        res = self.rs.add (permanent)

        fn (query, res)

        return res


    def _q_anyword (self, q, res):

        word = q.word
        
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
    
