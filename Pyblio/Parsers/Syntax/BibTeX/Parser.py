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

""" Stream oriented reading of a BibTeX file, with no actual semantic
operation on the content. Tries to return _everything_ from the file,
including comments, strings,..."""

import re

from Pyblio.Exceptions import ParserError
from Pyblio.Parsers.Syntax.BibTeX import Coding

class IBibTeX:
    def flat (self):
        """ Return a textual version of the field, with no visible BibTeX / LaTeX markup """
        pass

    def subst (self):
        """ Return a flattened list of the balanced expressions composing the field """
        pass

    def execute (self, environ):
        """ Execute the known LaTeX commands forming the field,
        substitute the known symbols, and return the resulting string"""
        pass

    def tobib (self):
        """ Return the BibTeX version of the field """
        pass


class Comment (unicode):
    """ A bibtex file comment """
    
    def __repr__ (self):
        return 'Comment (%s)' % unicode.__repr__ (self)


class ATComment (Comment):
    def __repr__ (self):
        return '@Comment (%s)' % unicode.__repr__ (self)

class Record (object):

    def __init__ (self, type, key, fields):

        self.type   = type
        self.key    = key
        self.fields = fields
        
        return

    def __cmp__ (self, other):

        if self.type != other.type: return 1
        if self.key  != other.key : return 1

        return cmp (self.fields, other.fields)
        
    def __repr__ (self):

        return 'Record (%s, %s, %s)' % (
            repr (self.type),
            repr (self.key),
            repr (self.fields))
    
class Join (list):
    """ A value, as a concatenation of blocks """
    
    def __repr__ (self):
        return 'Join (%s)' % list.__repr__ (self)

    def subst (self):
        v = []
        for data in self:
            v = v + data.subst ()
        
        return v

    def join (self):
        r = []
        for v in self:
            r += v.join ()
        return r

    def execute (self, env):
        # Joining of bare Text fragments leads to a lookup in the @string environment
        def subjoin (fragment):
            if isinstance (fragment, Text):
                try:
                    return env.strings [fragment]
                except KeyError:
                    pass
            return fragment.execute (env)
                
        return Join ([ subjoin (x) for x in self ])


    def flat (self):
        try:
            return ''.join (map (lambda x: x.flat (), self))
        except AttributeError:
            print repr (self)
            raise


    def tobib (self):
        return ' # '.join (map (lambda x: x.tobib (), self))
    
class Text(unicode):

    def flat(self):
        return self.replace ('~', u'\xa0')
    
    def __repr__ (self):
        return 'Text(%s)' % unicode.__repr__(self)

    def subst (self):
        return [self]

    def tobib(self):
        return Coding.encode(self)
    
    def execute (self, env):
        return self

class Cmd (object):
    """ A LaTeX \-command """
    
    def __init__ (self, cmd):
        self._cmd = cmd
        return
    
    def __repr__ (self):
        return 'Cmd (%s)' % `self._cmd`

    def flat (self):
        return self._cmd

    def subst (self):
        return [self]

    def tobib (self):
        return '\\%s' % self._cmd

    def __cmp__ (self, other):
        if not isinstance (other, Cmd): return 1
        
        return cmp (self._cmd, other._cmd)
        
class Block (object):
    """ A textual block, as a sequence of text and commands """

    closer = {
        '"': '"',
        '{': '}',
        '(': ')',
        }

    def __init__ (self, opening, data = None):
        self._o = opening

        if data is None: self._d = ()
        else:            self._d = data
        return
    
    def flat (self):
        r = ''
        for o in self._d:
            r = r + o.flat ()

        return r

    def append (self, v):
        return self._d.append (v)
        
    def execute (self, env):
        final = []
        stack = [] + list (self._d)
        
        while stack:
            d = stack.pop (0)
            
            if isinstance (d, Cmd):
                r = env.run (d._cmd, stack)
            else:
                r = d.execute (env)

            final.append (r)

        return Block (self._o, final)


    def join (self):
        return list (self._d)
    
    def __repr__ (self):
        return 'Block (%s, %s)' % (`self._o`,
                                  `self._d`)

    def subst (self):
        r = []
        for d in self._d:
            try:
                r = r + d.subst ()
            except AttributeError:
                print repr (d)
        return r

    def __cmp__ (self, other):
        if not isinstance (other, Block): return 1

        if self._o != other._o: return 1
        return cmp (self._d, other._d)

    def tobib (self):
        return '%s%s%s' % (
            self._o,
            ''.join([x.tobib() for x in self._d]),
            self.closer[self._o])


class EndOfFile (Exception): pass

class Cache (object):

    def __init__ (self, fd, charset):

        self.fd = fd
        self.ln = 0
        self.cs = charset
        
        self._buf = []
        return

    def readline (self):

        self.ln += 1

        if self._buf:
            return self._buf.pop ()

        l = self.fd.readline ()
        if not l: raise EndOfFile ()
        
        return l.decode (self.cs)

    def unreadline (self, line):

        self.ln -= 1
        self._buf.append (line)
        
        return


class Context (object):

    def __init__ (self):

        self.rectype = None
        return

ST_OUT, ST_OPEN, ST_DONE = range (3)

_record_start = re.compile ('\s*@\s*(\w+)(.*)')

def _on_out (fd, ctx):
    """ Called when the parser is not in a record """

    assert ctx.rectype is None
    
    comment = ''
    
    while 1:
        try:
            l = fd.readline ()

        except EndOfFile, _:
            if comment: return ST_DONE, Comment (comment)
            else:       return ST_DONE, None
            
        m = _record_start.match (l) 
        if m:
            # Handle the case of a @comment comment.
            if m.group (1).lower () == 'comment':
                r = []
                if comment:
                    r.append (Comment (comment))

                r.append (ATComment (m.group (2)))
                return ST_OUT, r
            
            ctx.rectype = m.group (1)
            fd.unreadline (m.group (2).lstrip ())
            
            if comment: return ST_OPEN, Comment (comment)
            else:       return ST_OPEN, None

        comment += l

    assert False

_brace_re  = re.compile (r'[()"{}\\]')
_cmd_re    = re.compile (r'(\w+|\S| )(.*)')
_inline_re = re.compile (r'([,#=])')

def _on_open (fd, ctx):
    """ Called at the opening of a record """

    assert ctx.rectype is not None

    # We eat up input as long as we don't have a balanced expression
    stack = []
    curr  = []
    
    container = None
    data = ''
    
    l     = fd.readline ()
    start = fd.ln
    
    while 1:
        m = _brace_re.search (l)
        if not m:
            data += l
            l = fd.readline ()
            continue

        idx = m.start (0)
        before, brace, l = l [:idx], l [idx], l [idx+1:]

        data += before

        if brace == '\\':
            m = _cmd_re.match (l)
            
            if not m:
                raise ParserError ('backslash at the end of a line', fd.ln)

            if data: curr.append (Text (data))
            curr.append (Cmd (m.group (1)))
            
            l = m.group (2)
            data = ''
            continue
        
        if not container:
            if data:
                raise ParserError (
                    'unexpected data before '
                    'the opening of the record: %s' % repr (data),
                    fd.ln)

            if brace in ')}':
                raise ParserError ('unexpected closing symbol %s' % repr (brace),
                                   fd.ln)

            container = brace

        else:
            if brace in '})':
                # Discard bad matching of braces
                if (brace == '}' and container != '{'):
                    raise ParserError ('mismatched "%s"' % brace, fd.ln)

                if brace == ')' and container != '(':
                    data += ')'
                    continue
                    
                if data: curr.append (Text (data))
                data = ''

                if not stack: break

                v = Block (container, curr)

                curr, container = stack.pop ()
                curr.append (v)
                continue
            
            elif brace == '(':
                # Except during the opening, the parenthesis is a normal token
                data += '('
                continue

            elif brace == '"':

                if container == '"':
                    # closing the brace
                    if data: curr.append (Text (data))
                    data = ''
                    
                    if not stack: break
                    
                    v = Block ('"', curr)
                    curr, container = stack.pop ()
                    curr.append (v)
                    continue
                
                else:
                    # opening the brace only occurs on the second level
                    
                    if len (stack) == 0:
                        #create a new context
                        if data: curr.append (Text (data))
                        stack.append ((curr, container))
                        
                        curr = []
                        data = ''
                        container = '"'

                    else:
                        data += '"'
                    
            elif brace == '{':
                if data: curr.append (Text (data))
                stack.append ((curr, container))
                
                curr = []
                data = ''
                container = '{'

    # We are only interested in first level items now
    stream = []
    
    while curr:
        l = curr.pop (0)

        if not isinstance (l, Text):
            stream.append (l)
            continue

        i = 0
        for m in _inline_re.finditer (l):
            s, e = m.start (1), m.end (1)
            
            stream += [ Text (x) for x in l [i:s].split () ]
            stream.append (Text (l [s]))
            i = e

        if i < len (l): stream += [ Text (x) for x in l [i:].split () ]
        
    final = []
    key   = None
    field = []

    while stream:

        k = stream.pop (0)

        if not stream or stream [0] == ',':
            if key: raise ParserError (
                "key is defined twice", start)

            if field: raise ParserError (
                "key is defined in the middle of the record", start)

            key = k
            if stream: stream.pop (0)
            continue

        v = stream.pop (0)
        if v != '=':
            raise ParserError (
                "invalid syntax after field %s" % repr (k), start)

        vs = Join ()
        
        while stream:
            v = stream.pop (0)
            if v == ',': break

            if vs:
                if v == '#':
                    if not stream:
                        raise ParserError (
                            "field %s: unexpected #" % k, start)
                    vs.append (stream.pop (0))

                else:
                    if isinstance (v, Text):
                        # Give a chance, in case a comma was missing
                        stream.insert (0, v)
                        break
                    
                    raise ParserError (
                        "field %s: missing #" % k, start)
            else:
                vs.append (v)
                    
        field.append ((k, vs))

    rec = Record (ctx.rectype, key, field)
    
    ctx.rectype = None
    
    return ST_OUT, rec

_fstm = {
    ST_OUT:  _on_out,
    ST_OPEN: _on_open,
    }

def read (fd, charset = 'utf-8'):

    ctx = Context ()
    
    fd = Cache (fd, charset)
    st = ST_OUT
    
    while st != ST_DONE:
        st, data = _fstm [st] (fd, ctx)
        if data is None: continue

        if type (data) is type ([]):
            for d in data: yield d
        else:
            yield data
        
    return

