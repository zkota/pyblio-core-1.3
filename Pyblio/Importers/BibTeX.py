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

tokens = ('AT', 'RBRACE', 'LBRACE', 'SPACE', 'COMMA', 'LITERAL',
          'EQUALS', 'SHARP', 'QUOTE', 'ESCAPE', 'SYMBOL', 'NUMBER')

def t_AT (t):
    r'@'
    return t

t_RBRACE  = r'\}'
t_LBRACE  = r'\{'

def t_SPACE (t):
    r'[\t\n ]+'

    t.value = ' '
    return t

t_COMMA   = r','
t_LITERAL = r'\w[\w\d]*'
t_EQUALS  = r'='
t_SHARP   = r'\#'
t_QUOTE   = r'"'
t_ESCAPE  = r'\\'
t_SYMBOL  = r'[^@{},#"\w\d\s=\\]'
t_NUMBER  = r'\d+'

def t_error (t):
    raise RuntimeError ('lexer error')


lex.lex ()


class Command (object):

    def __init__ (self, esc):

        self.esc = esc
        return
    
    def __repr__ (self):
        return 'Cmd (%s)' % `self.esc`

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

def p_at_object (t):
    ''' at_object : entry '''
    t [0] = t [1]
    return


def p_entry (t):
    ''' entry : entry_head assignment_list RBRACE
              | entry_head assignment_list COMMA opt_space RBRACE '''
    t [0] = t [1] + (t [2],)
    return

def p_empty_entry (t):
    ''' entry : entry_head RBRACE '''
    t [0] = t [1] + ({},)
    return

    
    
def p_entry_head (t):
    ''' entry_head : LITERAL opt_space LBRACE opt_space LITERAL opt_space COMMA opt_space '''
    t [0] = (t [1], t [5])
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

    t [0] = { t [1] : t [5] }
    return 

def p_value (t):
    ''' value : value opt_space SHARP opt_space simple_value '''
    t [0] = t [1] + t [5]
    return

def p_single_value (t):
    ''' value : simple_value '''
    t [0] = t [1]
    return
    
def p_simple_value (t):
    ''' simple_value : LBRACE  brace_data_list  RBRACE
                     | QUOTE   quote_data_list  QUOTE '''
    t [0] = t [2]
    return

def p_simple_atom_value (t):
    ''' simple_value : LITERAL
                     | NUMBER '''
    t [0] = (t [1],)
    return


def p_single_brace_data_list (t):
    ''' brace_data_list : brace_data '''
    t [0] = t [1]
    return

def p_brace_data_list (t):
    ''' brace_data_list : brace_data_list brace_data '''
    t [0] = t [1] + t [2]
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

def p_quote_data (t):
    ''' quote_data : misc_data
                   | RBRACE
                   | LBRACE '''
    t [0] = (t [1],)
    return

def p_misc_data (t):
    ''' misc_data  : LITERAL
                   | NUMBER
                   | SYMBOL
                   | SPACE
                   | COMMA
                   | escaped '''
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
                | ESCAPE SHARP
                | ESCAPE SYMBOL '''
    t [0] = Command (t [2])
    return


def p_opt_space (t):
    ''' opt_space : SPACE
                  | empty '''
    t [0] = t [1]
    return

def p_empty (t):
    'empty :'
    t [0] = ()
    return

def p_error (t):
    raise RuntimeError ('parser error: %s' % t)



# Create the parser, and cache its result in a tab file
_mod = 'BibTeX_Tab'

_pth = os.path.join (os.path.dirname (__file__), _mod + '.py')
_mod = string.join (__name__.split ('.') [:-1] + [_mod], '.')

yacc.yacc (tabmodule = (_pth, _mod))


def _flat (stream, encoding):
    
    ret = ''

    while stream:
        v, stream = stream [0], stream [1:]
        
        if isinstance (v, Command):
            ret = ret + v.esc
        else:
            ret = ret + v.decode (encoding)

    return ret


def _textify (stream, encoding):

    return [Attribute.Text (_flat (stream, encoding))]


def _persify (stream, encoding):

    # Person names are separated by 'and' keywords
    avail  = []
    stream = list (stream)
    
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
            stream = map (lambda x: _flat (x, encoding), stream)

            if len (stream) == 1:
                return Attribute.Person (last = stream [0])

            if len (stream) == 2:
                return Attribute.Person (first = stream [0],
                                         last  = stream [1])

        elif comma == 1:
            i = stream.index (',')

            return Attribute.Person (last  = _flat (stream [:i], encoding),
                                     first = _flat (stream [i+1:], encoding))
        
        return Attribute.Person ()
    
    return map (_person_decode, avail)


def _urlify (stream, encoding):

    return [Attribute.URL ('')]

def _dateify (stream, encoding):

    return [Attribute.Date ()]

def _refify (stream, encoding):

    return [Attribute.Reference ('')]


_mapping = {
    Attribute.Text:   _textify,
    Attribute.Person: _persify,
    Attribute.URL:    _urlify,
    Attribute.Date:   _dateify,
    Attribute.Reference: _refify,
    }

def file_import (file, encoding, db, ** kargs):
    
    data = yacc.parse (open (file).read ())

    for tp, key, val in data:

        tp = tp.lower ()

        try:
            schema = db.schema.documents [tp]
        except KeyError:
            raise Exceptions.SchemaError (_("document '%s' is unknown") % tp)
        
        e = Store.Entry (Store.Key (key), schema)

        for k, v in val.iteritems ():

            k = k.lower ()
            
            try:
                attp = schema.typeof (k)
            except KeyError:
                raise Exceptions.SchemaError (_("no attribute '%s' in document '%s'") % (
                    k, schema.name))

            e [k] = _mapping [attp.type] (v, encoding)

        db [e.key] = e
        
    return db
