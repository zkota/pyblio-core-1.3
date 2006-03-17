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
Basic syntactic elements used to format a citation.

This module defines the base syntax elements providing the formatting
domain specific language.

"""


from Pyblio.Format import S2
from Pyblio.Format.S3 import Tag
from Pyblio.Format.Base import Missing

from Pyblio.Attribute import Txo

from gettext import gettext as _

def _deferredText(text):
    """Ensure the parameter is a stage 1 object."""
    if isinstance(text, (str, unicode)):
        return _S1T(text)
    return text

class Glue(object):
    """ A base class that known how to join together multiple
    fragments of DSL code."""
    
    def __add__(self, other):
        return _Sum(self, _deferredText(other))

    def __radd__(self, other):
        return _Sum(_deferredText(other), self)

    def __or__ (self, other):
        return _Or(self, _deferredText(other))
    
    def __ror__(self, other):
        return _Or(_deferredText(other), self)


class _Sum(Glue):

    def __init__ (self, a, b):
        self.a = a
        self.b = b
        return

    def __call__ (self, db):
        a = self.a(db)
        b = self.b(db)
        return S2.Sum(a, b)

    def __repr__ (self):
        return '_Sum(%s, %s)' % (repr(self.a),
                                 repr(self.b))
    
class _Or(Glue):

    def __init__(self, a, b):
        self.a = a
        self.b = b
        return

    def __call__(self, db):
        a = self.a(db)
        b = self.b(db)
        return S2.Or(a, b)

    def __repr__(self):
        return '_Or(%s, %s)' % (repr(self.a),
                                repr(self.b))

class _S1T(Glue):
    """ This is a stage 1 text, ie a text that returns a stage 2 text
    when called."""
    
    def __init__(self, t):
        self.t = t
        return

    def __call__(self, db):
        return S2.Text(self.t)
    
    def __repr__(self):
        return '_S1T(%s)' % repr(self.t)


def join(middle, last=None):
    return _Join(middle, last)

class _Join(Glue):
    """ The join operator is used to join together multiple fragments
    of records::
 
           citation = join(middle, last)[part1, part2, ...]

    part1, part2, ... are joined together by inserting 'middle'
    between them. If a part is missing, it is simply skipped.
    If no part is available at all, the join fails.

    It is possible to specify a different separator between the last
    two parts.
    """
    
    def __init__(self, middle, last):

        self.middle = _deferredText(middle)

        if last: self.last = _deferredText(last)
        else:    self.last = self.middle
            
        self.children = []
        return
    
    def __getitem__(self, children):
        if not isinstance (children, (list, tuple)):
            children = [children]

        self.children.extend([_deferredText(t) for t in children])
        return self

    def __call__(self, db):

        return S2.Join(self.middle(db), self.last(db),
                       [child(db) for child in self.children])
    

class switch(Glue):
    """ The switch operator helps in bringing together multiple
    citation parts, according to the value of a Txo.

       >>> citation = switch('doctype')
       >>> citation.case(ARTICLE=article, BOOK=book)
       >>> citation.default(default)
       
    """

    def __init__(self, switch):

        self._switch = switch
        self._cases = {}
        self._default = None
        return

    def case(self, **kargs):
        for k, v in kargs.items():
            if k in self._cases:
                raise RuntimeError(_('%s: case %s defined more than once') % (
                    repr(self), repr(k)))

            self._cases[k] = _deferredText(v)
        return self

    def default(self, v):
        if self._default is not None:
            raise RuntimeError(_('%s: default case defined more than once') % (
                    repr(self),))
        self._default = _deferredText(v)
        return self
    
    def __repr__(self):
        return 'switch(%s)' % repr(self._switch)

    def __call__(self, db):
        # first of all, get access to the actual Txo being checked.

        parts = self._switch.split('.')

        if len(parts) == 1:
            a = self._switch
            try:
                s = db.schema[a]
            except KeyError:
                raise KeyError(_('%s: unknown attribute') % repr(self))

            def _fetch(record):
                return record[a][0]
            
        elif len(parts) == 2:
            a, q = parts
            try:
                s = db.schema[parts[0]].q[parts[1]]
            except KeyError:
                raise KeyError(_('%s: unknown attribute') % repr(self))

            def _fetch(record):
                return record[a][0].q[q][0]
            
                
        if s.type is not Txo:
            raise TypeError(_('%s: attribute is not a txo') % repr(self))
        
        group = db.txo[s.group]

        sw = {}

        if self._default:
            default = self._default(db)
        else:
            default = None

        
        for name, child in self._cases.items():
            try:
                txo = group.byname(name)
            except KeyError:
                raise KeyError(_('%s: unknown txo %s in group %s') % (
                    repr(self), repr(name), repr(s.group)))

            sw[Txo(txo)] = child(db)


        return S2.Switch(_fetch, sw, default)
    
# ==================================================
# Attribute accessors
# ==================================================

class _Validated(Glue):
    """ Base class for attribute accessors, providing some checks for
    stage 2."""
    
    def __init__(self, field):
        self._f = field
        return


    def __call__(self, db):
        """ Return a compiled version of the attribute accessor."""
        
        parts = self._f.split('.')
        if len(parts) == 1:
            try:
                s = db.schema[self._f]
            except KeyError:
                raise KeyError(_('%s: unknown attribute') % (
                    repr(self),))

            return self._fetch_a(self._f)

        elif len(parts) == 2:
            an, qn = parts
            try:
                s = db.schema[an]
            except KeyError:
                raise KeyError(_('%s: unknown attribute') % (
                    repr(self),))
            try:
                q = s.q[parts[1]]
            except KeyError:
                raise KeyError(_('%s: unknown qualifier') % (
                    repr(self),))

            return self._fetch_q(an, qn)
        

        else:
            raise SyntaxError(_('%s: illegal attribute syntax') % (
                              repr(self),))


class all(_Validated):

    def __repr__(self):
        return 'all(%s)' % repr(self._f)


    def _fetch_a(self, f):
        def _fetch(record):
            try:
                return record[f]
            except (KeyError, IndexError), msg:
                raise Missing (_('%s: no such attribute in record') % repr(self))
            
        return _fetch

    def _fetch_q(self, an, qn):
        def _fetch(record):
            try:
                return record[an][0].q[qn]
            except (KeyError, IndexError), msg:
                raise Missing (_('%s: no such attribute in record') % repr(self))

        return _fetch

class one(_Validated):

    def __repr__(self):
        return 'one(%s)' % repr(self._f)


    def _fetch_a(self, f):
        def _fetch(record):
            try:
                return record[f][0]
            except (KeyError, IndexError), msg:
                raise Missing (_('%s: no such attribute in record') % repr(self))
            
        return _fetch

    def _fetch_q(self, an, qn):
        def _fetch(record):
            try:
                return record[an][0].q[qn][0]
            except (KeyError, IndexError), msg:
                raise Missing (_('%s: no such attribute in record') % repr(self))

        return _fetch

        
# ==================================================
# Tags
# ==================================================

class _SynTag(object):
    """ This is a layout tag before its [] marker. """
    
    def __init__ (self, tag):
        self.tag = tag.lower ()
        self.attributes = {}

    def __call__(self, **kw):
        """Change attributes of this tag. This is implemented using
        __call__ because it then allows the natural syntax::
        
          A (href="http://...")

        """
        if not kw:
            return self

        for k, v in kw.iteritems():
            if k[-1] == '_':
                k = k[:-1]
            elif k[0] == '_':
                k = k[1:]
            self.attributes[k] = _deferredText(v)
        return self

    def __add__(self, other):
        return _Tag('t', [self, _deferredText(other)], {})
        
    def __radd__(self, other):
        return _Tag('t', [_deferredText(other), self], {})
        
    def __getitem__ (self, children):
        if not isinstance(children, (list, tuple)):
            children = [children]

        children = [_deferredText(child) for child in children]

        return _Tag(self.tag, children, self.attributes)

class _Tag(Glue):

    """ This is a layout tag after its [] marker, but before the
    compilation."""

    def __init__ (self, tag, children, attributes):

        self.tag = tag
        self.children = children
        self.attributes = attributes
        
    def __repr__(self):
        rstr = ''
        if self.attributes:
            rstr += ', attributes=%r' % self.attributes
        if self.children:
            rstr += ', children=%s' % repr(self.children)
            
        return "DSL.Tag(%r%s)" % (self.tag, rstr)

    def __call__(self, db):
        children = [child(db) for child in self.children]
        kwargs = {}
        for k, v in self.attributes.items():
            kwargs[k] = v(db)
            
        return Tag(self.tag, children, kwargs)
    
    def __add__(self, other):
        return _Tag('t', [self, _deferredText(other)], {})
        
    def __radd__(self, other):
        return _Tag('t', [_deferredText(other), self], {})
        
        

class _Proto(str):
    """Proto is a string subclass. Instances of Proto, which are constructed
    with a string, will construct Tag instances in response to __call__
    and __getitem__, delegating responsibility to the tag.
    """
    __slots__ = []

    def __call__(self, **kw):
        return _SynTag(self)(**kw)

    def __getitem__(self, children):
        return _SynTag(self)[children]


glob = globals ()

for t in ('A', 'B', 'I', 'Small', 'Span'):
    glob[t] = _Proto(t)

BR = _Proto('BR')[_S1T('')]


# ===================================================
# Helper for building simple additional DSL functions
# ===================================================


def lazy(fn):

    """ Transform a simple function into a lazy function lifted in the
    formatting system.

    This is only sugar : the initial function must be aware that every
    argument must be made strict by calling them before use.
    """

    class _caller(Glue):
        def __init__ (self, * args, ** kargs):
            self.__args  = [_deferredText(arg) for arg in args]

            for k, v in kargs.items():
                kargs[k] = _deferredText(v)
                
            self.__kargs = kargs
            
        def __call__(self, db):
            args = [arg(db) for arg in self.__args]
            kargs = {}
            for k, v in self.__kargs.items():
                kargs[k] = v(db)

            def _late(record):
                return fn (record, *args, **kargs)

            return _late

    return _caller
