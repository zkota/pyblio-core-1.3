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
# 

""" Extension module for BibTeX files """


import re, os, string

from Pyblio.Importers import lex, yacc

from Pyblio import Attribute, Store, Exceptions

from gettext import gettext as _

# ==================================================
# Base Classes
# ==================================================

class Symbol (str):
    """ A literal symbol, predefined or defined by the user """

    def flat (self, charset):
        return self.decode (charset)

    def __repr__ (self):
        return 'Symbol (%s)' % str.__repr__ (self)

    def subst (self):
        return self

    def tobib (self):
        return self

class Command (object):
    """ A LaTeX \-command """
    
    def __init__ (self, cmd):
        self._cmd = cmd
        return
    
    def __repr__ (self):
        return 'Cmd (%s)' % `self._cmd`

    def flat (self, charset):
        return self._cmd.decode (charset)

    def subst (self):
        return self

    def tobib (self):
        return '\\%s' % self._cmd


class Text (str):

    def flat (self, charset):
        return self.decode (charset)
    
    def __repr__ (self):
        return 'Text (%s)' % str.__repr__ (self)

    def subst (self):
        return self

    def tobib (self):
        return self
    

class Block (object):
    """ A textual block, as a sequence of text and commands """

    def __init__ (self, opening, closing, data = None):
        self._o = opening
        self._c = closing
        self._d = data or ()
        return
    
    def flat (self, charset):
        r = ''
        for o in self._d:
            r = r + o.flat (charset)

        return r

    def __repr__ (self):
        return 'Block (%s, %s, %s)' % (`self._o`,
                                       `self._c`,
                                       `self._d`)

    def subst (self):
        return self._d

    def tobib (self):
        return '%s%s%s' % (
            self._o,
            string.join (map (lambda x: x.tobib (), self._d), ''),
            self._c)


class Join (list):
    """ A value, as a concatenation of blocks """
    
    def __repr__ (self):
        return 'Join (%s)' % list.__repr__ (self)

    def subst (self):
        v = ()
        for data in self:
            v = v + data.subst ()
        
        return v

    def flat (self, charset):
        return string.join (map (lambda x: x.flat (charset), self), '')


    def tobib (self):
        return string.join (map (lambda x: x.tobib (), self), ' # ')
    

class Entry (dict):
    """ A bibliographic entry """
    
    def __init__ (self, tp, key):

        self.type = tp
        self.key  = key
        return

    def __repr__ (self):
        return 'Entry (%s, %s, %s)' % (
            self.type, self.key, dict.__repr__ (self))


class Comment (str):
    """ A bibtex file comment """
    
    def __repr__ (self):
        return 'Comment (%s)' % str.__repr__ (self)


# ==================================================
# BibTeX lexer
# ==================================================

tokens = ('AT', 'RBRACE', 'LBRACE', 'SPACE', 'COMMA', 'LITERAL',
          'EQUALS', 'SHARP', 'QUOTE', 'ESCAPE', 'SYMBOL', 'NUMBER',
          'COMMENT', 'NEWLINE', 'LPAREN', 'RPAREN')

def t_AT (t):
    r'@'
    return t

t_RBRACE  = r'\}'
t_LBRACE  = r'\{'

def t_SPACE (t):
    r'[\t ]+'

    t.value = ' '
    return t

def t_NEWLINE (t):
    r'\n+'
    t.value = '\n'
    return t


t_COMMA   = r','

def t_LITERAL (t):
    r'\w[\w\d_-]*'
    
    if t.value.lower () == 'comment':
        t.type = 'COMMENT'
        
    return t

t_LPAREN  = r'\('
t_RPAREN  = r'\)'

t_EQUALS  = r'='
t_SHARP   = r'\#'
t_QUOTE   = r'"'
t_ESCAPE  = r'\\'
t_SYMBOL  = r'[^@{},#"\w\d\s=\\()_-]'
t_NUMBER  = r'\d+'

def t_error (t):
    raise RuntimeError ('lexer error')


lex.lex ()


# ==================================================
# BibTeX parser
# ==================================================


def p_empty_file (t):
    ''' file : opt_space '''
    t [0] = ()
    return

def p_file (t):
    ''' file : opt_space object_list opt_space '''
    t [0] = t [2]
    return


def p_single_object_list (t):
    ''' object_list : object '''
    t [0] = (t [1],)
    return

def p_object_list (t):
    ''' object_list : object_list opt_space object '''
    t [0] = t [1] + (t [3],)
    return 


def p_object (t):
    ''' object : AT opt_space at_object '''
    t [0] = t [3]
    return

def p_at_object_entry (t):
    ''' at_object : entry '''
    t [0] = t [1]
    return

def p_at_object_comment (t):
    ''' at_object : COMMENT comment NEWLINE '''
    t [0] = Comment (t [2])
    return

def p_at_object_empty_comment (t):
    ''' at_object : COMMENT NEWLINE '''
    t [0] = Comment ('')
    return

def p_comment (t):
    ''' comment : comment comment_data '''
    t [0] = t [1] + t [2]
    return

def p_single_comment (t):
    ''' comment : comment_data '''
    t [0] = t [1]
    return


def p_comment_data (t):
    ''' comment_data : AT
                     | RBRACE
                     | LBRACE
                     | SPACE
                     | COMMA
                     | LITERAL
                     | EQUALS
                     | SHARP
                     | QUOTE
                     | ESCAPE
                     | SYMBOL
                     | LPAREN
                     | RPAREN
                     | NUMBER
                     | COMMENT '''
    t [0] = t [1]
    return


def p_entry (t):
    ''' entry : LITERAL opt_space LBRACE opt_space LITERAL opt_space COMMA opt_space assignment_list RBRACE
              | LITERAL opt_space LBRACE opt_space LITERAL opt_space COMMA opt_space assignment_list COMMA opt_space RBRACE
              | LITERAL opt_space LPAREN opt_space LITERAL opt_space COMMA opt_space assignment_list RPAREN
              | LITERAL opt_space LPAREN opt_space LITERAL opt_space COMMA opt_space assignment_list COMMA opt_space RPAREN '''

    e = Entry (t [1].lower (), t [5])
    e.update (t [9])
    
    t [0] = e
    return

def p_empty_entry (t):
    ''' entry : LITERAL opt_space LBRACE opt_space LITERAL opt_space RBRACE
              | LITERAL opt_space LPAREN opt_space LITERAL opt_space RPAREN '''
    t [0] = Entry (t [1], t [5])
    return


def p_single_assignment_list (t):
    ''' assignment_list : assignment '''
    t [0] = t [1]
    return

def p_assignment_list (t):
    ''' assignment_list : assignment_list COMMA opt_space assignment '''
    ret = {}
    ret.update (t [1])
    ret.update (t [4])

    t [0] = ret
    return


def p_assignment (t):
    ''' assignment : LITERAL opt_space EQUALS opt_space value opt_space '''

    t [0] = { t [1].lower () : t [5] }
    return 

def p_value (t):
    ''' value : value opt_space SHARP opt_space simple_value '''
    j = Join ()
    j.append (t [1])
    j.append (t [5])
    
    t [0] = j
    return

def p_single_value (t):
    ''' value : simple_value '''
    t [0] = t [1]
    return
    
def p_simple_brace_value (t):
    ''' simple_value : LBRACE  brace_data_list  RBRACE '''
    t [0] = Block ('{', '}', t [2])
    return

def p_simple_brace_value_empty (t):
    ''' simple_value : LBRACE RBRACE '''
    t [0] = Block ('{', '}')
    return

def p_simple_quote_value (t):
    ''' simple_value : QUOTE   quote_data_list  QUOTE '''
    t [0] = Block ('"', '"', t [2])
    return

def p_simple_quote_value_empty (t):
    ''' simple_value : QUOTE QUOTE '''
    t [0] = Block ('"', '"')
    return

def p_simple_atom_value (t):
    ''' simple_value : LITERAL
                     | NUMBER '''
    t [0] = Symbol (t [1])
    return


def p_single_brace_data_list (t):
    ''' brace_data_list : brace_data '''
    t [0] = t [1]
    return

def p_brace_data_list (t):
    ''' brace_data_list : brace_data_list brace_data '''
    t [0] = t [1] + t [2]
    return

def p_sub_brace_data (t):
    ''' brace_data : LBRACE brace_data_list RBRACE '''
    t [0] = (Block ('{', '}', t [2]),)
    return
    
def p_sub_brace_data_empty (t):
    ''' brace_data : LBRACE RBRACE '''
    t [0] = (Block ('{', '}'),)
    return
    
def p_brace_data (t):
    ''' brace_data : misc_data
                   | QUOTE '''
    t [0] = (t [1],)
    return

def p_single_quote_data_list (t):
    ''' quote_data_list : quote_data '''
    t [0] = t [1]
    return

def p_quote_data_list (t):
    ''' quote_data_list : quote_data_list quote_data '''
    
    t [0] = t [1] + t [2]
    return

def p_sub_quote_data (t):
    ''' quote_data : LBRACE quote_data_list RBRACE '''
    t [0] = (Block ('{', '}', t [2]),)
    return

def p_sub_quote_data_empty (t):
    ''' quote_data : LBRACE RBRACE '''
    t [0] = (Block ('{', '}'),)
    return

def p_quote_data (t):
    ''' quote_data : misc_data '''
    t [0] = (t [1],)
    return

def p_misc_data (t):
    ''' misc_data  : LITERAL
                   | NUMBER
                   | SYMBOL
                   | LPAREN
                   | RPAREN
                   | SPACE
                   | NEWLINE
                   | COMMA
                   | COMMENT '''
    t [0] = Text (t [1])
    return

def p_misc_data_cmd (t):
    ''' misc_data  : escaped '''
    t [0] = t [1]
    return

def p_escaped (t):
    ''' escaped : ESCAPE LITERAL
                | ESCAPE QUOTE
                | ESCAPE COMMA
                | ESCAPE RBRACE
                | ESCAPE LBRACE
                | ESCAPE ESCAPE
                | ESCAPE AT
                | ESCAPE COMMENT
                | ESCAPE SHARP
                | ESCAPE SYMBOL
                | ESCAPE LPAREN
                | ESCAPE RPAREN '''
    t [0] = Command (t [2])
    return


def p_opt_space (t):
    ''' opt_space : spaces
                  | empty '''
    t [0] = t [1]
    return


def p_space (t):
    ''' space : SPACE
              | NEWLINE '''
    
    t [0] = t [1]
    return

def p_spaces (t):
    ''' spaces : space
               | spaces space '''
    
    t [0] = t [1]
    return


def p_empty (t):
    'empty :'
    t [0] = ()
    return

def p_error (t):
    line = t.lineno
    raise RuntimeError ('parser error: %d: %s' % (line, t))



# Create the parser, and cache its result in a tab file
_mod = 'BibTeX_Tab'

_pth = os.path.join (os.path.dirname (__file__), _mod + '.py')
_mod = string.join (__name__.split ('.') [:-1] + [_mod], '.')

yacc.yacc (tabmodule = (_pth, _mod))


# ==================================================
# BibTeX conversion routines
# ==================================================

def _textify (stream, encoding):

    return [Attribute.Text (stream.flat (encoding))]


def _persify (stream, encoding):
    ''' Parse a stream of tokens as a series of person names '''

    # Person names are separated by 'and' keywords
    avail  = []
    stream = list (stream.subst ())
    
    while 1:
        try:
            i = stream.index ('and')
        except ValueError:
            break

        avail.append (stream [0:i])
        stream = stream [i+1:]

    if stream:
        avail.append (stream)

    def _person_decode (stream):

        stream = filter (lambda x: x != ' ', stream)
        
        # Check for ',' syntax for names
        comma = stream.count (',')
        
        if comma == 0:
            # Use the number of segments in the name
            stream = map (lambda x: x.flat (encoding), stream)

            if len (stream) == 1:
                return Attribute.Person (last = stream [0])

            if len (stream) == 2:
                return Attribute.Person (first = stream [0],
                                         last  = stream [1])

        elif comma == 1:
            i = stream.index (',')

            return Attribute.Person \
                   (last  = Block ('{','}', stream [:i]).flat (encoding),
                    first = Block ('{','}', stream [i+1:]).flat (encoding))
        
        return Attribute.Person ()
    
    return map (_person_decode, avail)


def _urlify (stream, encoding):

    return [Attribute.URL (stream.flat (encoding))]


def _dateify (stream, encoding):

    return [Attribute.Date ()]


_mapping = {
    Attribute.Text:   _textify,
    Attribute.Person: _persify,
    Attribute.URL:    _urlify,
    Attribute.Date:   _dateify,
    }


def _tostring (tp, key, data):

    ret = '@%s{%s,\n' % (tp, key)

    attrs = []
    keys  = data.keys ()
    keys.sort ()
    
    for k in keys:
        v = data [k]
        attrs.append ('   %s = %s' % (k, v.tobib ()))

    return ret + string.join (attrs, ',\n') + '\n}'

# ==================================================
# BibTeX interface
# ==================================================

def file_import (file, encoding, db, ** kargs):
    
    datalist = yacc.parse (open (file).read (), debug = 0)

    in_head  = True
    header   = []

    doctype = {}
    for v in db.enum ['doctype'].values ():
        doctype [v.names [''].lower ()] = v

    for data in datalist:

        if isinstance (data, Comment):
            # this is a comment. skip.
            if not in_head: continue

            header.append (data.strip ().decode (encoding))
            continue

        if in_head:
            # we are leaving the header.
            in_head = False
            
            if header:
                db.header = string.join (header, '\n')
            
        tp, key, val = data.type, data.key, data
        
        e = Store.Entry ()

        for k, v in val.iteritems ():

            k = k.lower ()
            
            try:
                attp = db.schema [k]

            except KeyError:
                raise Exceptions.SchemaError (
                    _("no attribute '%s' in document '%s'") % (
                    k, tp))

            e [k] = _mapping [attp.type] (v, encoding)

        e.native = ('bibtex', _tostring (tp, key, val).decode (encoding))

        # Add the key and document type
        e ['id'] = [Attribute.ID (key.decode (encoding))]
        e ['doctype'] = [Attribute.Enumerated (doctype [tp])]
        
        db.add (e)
        
    return db
