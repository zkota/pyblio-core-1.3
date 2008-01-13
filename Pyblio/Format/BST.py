# This file is part of pybliographer
# 
# Copyright (C) 1998-2007 Frederic GOBRY
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

# Intepretation of BST files based on Oren Patashnik's BibTeXing document:
# http://amath.colorado.edu/documentation/LaTeX/reference/faq/bibtex.pdf

"""Format bibliographic record according to a BibTeX BST file.

This module reimplements the bibtex utility on top of pyblio-core. It
reads BST files and generates the formatted bibliography from the
pyblio records.
"""

import re
import logging

from Pyblio import Attribute


_TOKEN_RE = re.compile(
    r'^\s*(%.*|\'?[\w.]+\$?|:?=|[{}*+><-]|"[^"]*"|#\d+)\s*(.*)')

log = logging.getLogger('pyblio.format.bst')

class Error(Exception):
    pass


class Token(object):
    """Syntactic item with location in source file."""
    def __init__(self, text, line):
        self.token = text
        self.line = line

    def __cmp__(self, other):
        if isinstance(other, Token):
            value = other.token
        else:
            value = other
        return cmp(self.token, value)

    def __hash__(self):
        return hash(self.token)

    def __repr__(self):
        return "T:" + self.token


def _Next(fd):
    """Get the next Token from source."""
    line_num = 0
    for line in fd:
        line_num += 1
        if not line.strip():
            continue
        while line:
            m = _TOKEN_RE.match(line)
            if not m:
                raise Error('line %d: cannot parse %r' % (line_num, line))
            yield Token(m.group(1), line_num)
            line = m.group(2)


def _NextBlock(tz):
    """Get the next argument, either a single token or a block."""
    level = 0
    block = []
    while True:
        token = tz.next()
        if token == '{':
            level += 1
        elif token == '}':
            level -= 1
        block.append(token)
        if level < 0:
            raise Error('line %d: mismatched {' % token.line)
        if level == 0:
            if block[0] == '{':
                return block[1:-1]
            return block


class Quoted(object):
    """A quoted block of instructions."""
    def __init__(self, line, block=None):
        self.block = block or []
        self.line = line

    def __repr__(self):
        return "{ %s }"  % ' '.join(str(x) for x in self.block)


class State(object):
    """The state holds the internal state of the bst compiler and the
    records to format."""
    def __init__(self, refs, db):
        self.refs = refs
        self.db = db

        self.stack = []
        self.blockstack = []
        self.output = ''
        self.fields = None
        self.local_integers = set()
        self.local_strings = set(['sort.key$'])
        self.integers = set(['global.max$', 'entry.max$'])
        self.strings = set()
        self.functions = {}
        self.macros = {}
        self.values = {'global.max$':2**31,
                       'entry.max$': 2**31}
        self.local_values = {}
        self.warnings = []

        self.FUNCTIONS = {'<': self.Less,
                          '>': self.More,
                          '=': self.Equal,
                          '+': self.Plus,
                          '-': self.Minus,
                          '*': self.Times,
                          ':=': self.Assign,
                          'add.period$': self.AddPeriod,
                          'call.type$': self.CallType,
                          'change.case$': self.ChangeCase,
                          'cite$': self.Cite,
                          'duplicate$': self.Duplicate,
                          'empty$': self.Empty,
                          'format.name$': self.FormatName,
                          'if$': self.IfThenElse,
                          'int.to.str$': self.IntToStr,
                          'missing$': self.Missing,
                          'newline$': self.Newline,
                          'num.names$': self.NumNames,
                          'or': self.Or,
                          'pop$': self.Pop,
                          'preamble$': self.Preamble,
                          'purify$': self.Purify,
                          'skip$': self.Skip,
                          'substring$': self.Substring,
                          'swap$': self.Swap,
                          'type$': self.Type,
                          'warning$': self.Warning,
                          'while$': self.While,
                          'width$': self.Width,
                          'write$': self.Write,
                          }

    def FormatName(self):
        fmt = self.stack.pop()
        idx = self.stack.pop()
        names = self.stack.pop()
        name = names[idx-1]
        # TODO(gobry): use the actual name format
        self.stack.append('%s %s' % (name.first or '', name.last))

    def NumNames(self):
        names = self.stack.pop()
        if not isinstance(names, list):
            raise Error('invalid names: %r' % names)
        self.stack.append(len(names))

    def While(self):
        action = self.stack.pop()
        cond = self.stack.pop()

        while True:
            for op in cond.block:
                self.Push(op)
            if not self.stack.pop():
                break
            for op in action.block:
                self.Push(op)

    def Missing(self):
        self.stack.append((self.stack.pop() is None) and 1 or 0)

    def AddPeriod(self):
        self.stack.append(self.stack.pop() + '.')

    def Width(self):
        # TODO(gobry): this should find a way to use proportional font
        # info... not really easy to hook into that low layer though
        self.stack.append(len(self.stack.pop()))

    def CallType(self):
        tp = self.entry['doctype'][0]
        tpname = self.db.schema.txo[tp.group][tp.id].names['C']
        for body in self.functions[tpname]:
            self.Push(body)
        
    def ChangeCase(self):
        spec = self.stack.pop().lower()
        word = self.stack.pop()
        if isinstance(word, str):
            if spec == 'l':
                word = word.lower()
            elif spec == 'u':
                word = word.upper()
            elif spec == 't':
                self.warnings.append("change.case$ doesn't support 't' yet")
            else:
                raise Error('invalid change.case$ specification %r' % spec)
        self.stack.append(word)

    def Substring(self):
        length = self.stack.pop()
        start = self.stack.pop()
        text = self.stack.pop()
        if text:
            if start > 0:
                start -= 1
                text = text[start:start+length]
            elif start < 1:
                text = text[start-length:start]
        self.stack.append(text)

    def IntToStr(self):
        self.stack.append(str(self.stack.pop()))

    def Skip(self):
        pass

    def Pop(self):
        self.stack.pop()

    def Purify(self):
        pass

    def Duplicate(self):
        self.stack.append(self.stack[-1])

    def Warning(self):
        self.warnings.append(self.stack.pop())

    def Cite(self):
        # This should be the key that was used to cite the
        # object. Here, we use the record id, to detect which record
        # has been cited.
        self.stack.append(str(self.entry.key))

    def Or(self):
        a = self.stack.pop()
        b = self.stack.pop()
        self.stack.append((a or b) and 1 or 0)

    def Type(self):
        tp = self.entry['doctype'][0]
        self.stack.append(self.db.schema.txo[tp.group][tp.id].names['C'])

    def IfThenElse(self):
        else_clause, then_clause, cond = self.stack.pop(), self.stack.pop(), self.stack.pop()
        if cond:
            quoted = then_clause
        else:
            quoted = else_clause
        for token in quoted.block:
            self.Push(token)

    def Empty(self):
        i = self.stack.pop()
        if isinstance(i, str):
            r = i.strip()
        else:
            r = i
        if not r:
            self.stack.append(1)
        else:
            self.stack.append(0)

    def Less(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a < b and 1 or 0)

    def More(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a > b and 1 or 0)

    def Equal(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a == b and 1 or 0)

    def Plus(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a + b)

    def Minus(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a - b)

    def Times(self):
        b, a = self.stack.pop() or '', self.stack.pop() or ''
        self.stack.append(a + b)

    def Swap(self):
        a = self.stack.pop()
        b = self.stack.pop()
        self.stack.append(a)
        self.stack.append(b)

    def Assign(self):
        name, value = self.stack.pop(), self.stack.pop()
        log.debug('%r -> %r' % (value, name))
        if not isinstance(name, Quoted) or len(name.block) != 1:
            raise Error('assignment to a non-variable %r' % name)
        name = name.block[0]
        if name in self.local_strings or name in self.strings:
            if name in self.local_strings:
                self.local_values.setdefault(self.entry.key, {})[name] = value
            else:
                self.values[name] = value
        elif name in self.local_integers or name in self.integers:
            if not isinstance(value, int):
                raise Error('%r expects an int, received %r' % (name, value))
            if name in self.local_integers:
                self.local_values.setdefault(self.entry.key, {})[name] = value
            else:
                self.values[name] = value
        else:
            raise Error('unknown variable %r' % name)

    def Write(self):
        r = self.stack.pop()
        log.debug('WRITE %r' % r)
        self.output += r

    def Newline(self):
        self.output += '\n'

    def Preamble(self):
        self.stack.append('')

    # --------------------------

    def Push(self, token):
        log.debug('%s: %r %r' % (token.line, token, self.stack))
        if isinstance(token, Quoted):
            self.stack.append(token)
            return

        f = token.token[0]

        if f == '{':
            self.blockstack.append(Quoted(token.line))
            return

        if f == '}':
            last = self.blockstack.pop()
            if self.blockstack:
                self.blockstack[-1].block.append(last)
            else:
                self.stack.append(last)
            return

        # we are in an escaped block
        if self.blockstack:
            self.blockstack[-1].block.append(token)
            return

        if f == '#':
            self.stack.append(int(token.token[1:]))
            return

        if f == "'":
            # make this a Quoted object
            raw = token.token[1:]
            self.stack.append(Quoted(token.line,
                                     [Token(raw, token.line)]))
            return
        
        if f == '"':
            self.stack.append(token.token[1:-1])
            return

        # Built-in functions
        if token in self.FUNCTIONS:
            try:
                self.FUNCTIONS[token.token]()
            except Error, msg:
                raise Error('when applying %r, line %d: %s' % (
                    token, token.line, msg))
            return
        # User-defined functions
        if token in self.functions:
            for body in self.functions[token]:
                self.Push(body)
            return
        # bibliographic fields
        if token in self.fields:
            if token == 'year':
                if 'date' in self.entry:
                    entry = str(self.entry['date'][0].year)
                else:
                    entry = None
            else:
                # the bibtex key is in the "id" field in our scheme
                if token == 'key':
                    token = Token('id', token.line)
                entry = self.entry.get(token.token, None)
                if entry and not isinstance(entry[0], Attribute.Person):
                    entry = entry[0]
            self.stack.append(entry)
            return
        # Variables
        if token in self.strings or token in self.integers:
            self.stack.append(self.values[token])
        elif token in self.local_strings or token in self.local_integers:
            self.stack.append(self.local_values[self.entry.key][token])
        else:
            raise Error('undefined token %r' % token)


class BST(object):
    """This object represents a parsed BST file."""

    COMMANDS = {'ENTRY': 3,
                'INTEGERS': 1,
                'FUNCTION': 2,
                'STRINGS': 1,
                'MACRO': 2,
                'READ': 0,
                'ITERATE': 1,
                'REVERSE': 1,
                'SORT': 0,
                'EXECUTE': 1}

    def __init__(self, fd):
        self.program = []
        tz = _Next(fd)
        while True:
            try:
                token = tz.next()
            except StopIteration:
                break
            if token.token[0] == '%':
                continue
            if token.token not in self.COMMANDS:
                raise Error('line %d: unexpected token %r' % (
                    token.line, token))
            count = self.COMMANDS[token.token]
            args = []
            while count:
                args.append(_NextBlock(tz))
                count -= 1
            self.program.append((token, getattr(self, token.token), args))

    def Run(self, state):
        for token, fn, args in self.program:
            try:
                fn(state, args)
            except Error, msg:
                raise Error("in %s, line %d: %s" % (
                    token, token.line, msg))

    def ENTRY(self, state, args):
        if state.fields is not None:
            raise Error('ENTRY has been already called')
        state.fields = set(args[0])
        state.fields.add('crossref')
        state.local_integers.update(set(args[1]))
        state.local_strings.update(set(args[2]))

    def INTEGERS(self, state, args):
        state.integers.update(set(args[0]))

    def FUNCTION(self, state, args):
        name, body = args
        if len(name) != 1:
            raise Error('invalid function name %r' % name)
        state.functions[name[0]] = body

    def STRINGS(self, state, args):
        state.strings.update(set(args[0]))

    def MACRO(self, state, args):
        name, body = args
        if len(name) != 1:
            raise Error('invalid macro name %r' % name)
        state.macros[name[0]] = body

    def READ(self, state, args):
        pass

    def ITERATE(self, state, args):
        for entry in state.refs.itervalues():
            state.entry = entry
            self.EXECUTE(state, args)

    def REVERSE(self, state, args):
        pass

    def SORT(self, state, args):
        pass

    def EXECUTE(self, state, args):
        name = args[0]
        if len(name) != 1:
            raise Error('invalid function name %r' % name)
        state.Push(name[0])
