# -*- coding: utf-8 -*-
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

from Pyblio import Attribute, Store, Exceptions, Tools

from gettext import gettext as _

# ==================================================
# Base Classes
# ==================================================

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


    
class Symbol (str):
    """ A literal symbol, predefined or defined by the user """

    def flat (self):
        return self

    def __repr__ (self):
        return 'Symbol (%s)' % str.__repr__ (self)

    def subst (self):
        return [self]

    def tobib (self):
        return self

    def execute (self, env):
        return env.strings [self]


class Command (object):
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


class Text (unicode):

    def flat (self):
        return self
    
    def __repr__ (self):
        return 'Text (%s)' % unicode.__repr__ (self)

    def subst (self):
        return [self]

    def tobib (self):
        return self
    
    def execute (self, env):
        return self

class Block (object):
    """ A textual block, as a sequence of text and commands """

    def __init__ (self, opening, closing, data = None):
        self._o = opening
        self._c = closing
        self._d = data or ()
        return
    
    def flat (self):
        r = ''
        for o in self._d:
            r = r + o.flat ()

        return r

    def execute (self, env):
        final = []
        stack = [] + list (self._d)
        
        while stack:
            d = stack.pop (0)
            
            if isinstance (d, Command):
                r = env.run (d._cmd, stack)
            else:
                r = d.execute (env)

            final.append (r)

        return Block (self._o, self._c, final)


    def join (self):
        return list (self._d)
    
    def __repr__ (self):
        return 'Block (%s, %s, %s)' % (`self._o`,
                                       `self._c`,
                                       `self._d`)

    def subst (self):
        r = []
        for d in self._d:
            try:
                r = r + d.subst ()
            except AttributeError:
                print repr (d)
        return r

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
        return map (lambda x: x.execute (env), self)


    def flat (self):
        return string.join (map (lambda x: x.flat (), self), '')


    def tobib (self):
        return string.join (map (lambda x: x.tobib (), self), ' # ')
    

class Record (dict):
    """ A bibliographic entry """
    
    def __init__ (self, tp, key):

        self.type = tp
        self.key  = key
        return

    def __repr__ (self):
        return 'Record (%s, %s, %s)' % (
            self.type, self.key, dict.__repr__ (self))


class Comment (str):
    """ A bibtex file comment """
    
    def __repr__ (self):
        return 'Comment (%s)' % str.__repr__ (self)


_basemap = {
    "'": {
    'A': Text (u"Á"),
    'E': Text (u"É"),
    'I': Text (u"Í"),
    'O': Text (u"Ó"),
    'U': Text (u"Ú"),
    'Y': Text (u"Ý"),
    'a': Text (u"á"),
    'e': Text (u"é"),
    'i': Text (u"í"),
    'o': Text (u"ó"),
    'u': Text (u"ú"),
    'y': Text (u"ý"),
    },
    
    "`": {
    'A': Text (u"À"),
    'E': Text (u"È"),
    'I': Text (u"Ì"),
    'O': Text (u"Ò"),
    'U': Text (u"Ù"),
    'a': Text (u"à"),
    'e': Text (u"è"),
    'i': Text (u"ì"),
    'o': Text (u"ò"),
    'u': Text (u"ù"),
    },
    
    "^": {
    'A': Text (u"Â"),
    'E': Text (u"Ê"),
    'I': Text (u"Î"),
    'O': Text (u"Ô"),
    'U': Text (u"Û"),
    'a': Text (u"â"),
    'e': Text (u"ê"),
    'i': Text (u"î"),
    'o': Text (u"ô"),
    'u': Text (u"û"),
    },

    "¨": {
    'A': Text (u"Ä"),
    'E': Text (u"Ë"),
    'I': Text (u"Ï"),
    'O': Text (u"Ö"),
    'U': Text (u"Ü"),
    'a': Text (u"ä"),
    'e': Text (u"ë"),
    'i': Text (u"ï"),
    'o': Text (u"ö"),
    'u': Text (u"ü"),
    'y': Text (u"ÿ"),
    },

    "c": {
    'C': Text (u"Ç"),
    'c': Text (u"ç"),
    },

    
    "~": {
    'A': Text (u"Ã"),
    'O': Text (u"Õ"),
    'a': Text (u"ã"),
    'o': Text (u"õ"),
    'n': Text (u"ñ"),
    'N': Text (u"Ñ"),
    },
    
}

class Environ (object):

    def __init__ (self):

        self.strings = {}
        return

    def run (self, cmd, stack):

        try:
            m = _basemap [cmd]
        except KeyError:
            return Text ('?')

        # If we have a map, we need the single next character
        while 1:
            if isinstance (stack [0], Text):
                tt = stack.pop (0)

                if len (tt) > 1:
                    t = tt [0]
                    stack.insert (0, Text (tt [1:]))
                else:
                    t = tt

                return m [t]

            elif isinstance (stack [0], Block):
                # Move this block back one step
                d = list (stack.pop (0)._d)

                while d:
                    stack.insert (0, d.pop ())

            else:
                raise Exceptions.ParserError ('cannot evaluate expression %s' % repr ((cmd, stack)))

        


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
    r'[\r\t ]+'

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
t_SYMBOL  = r'[^@{},#"\w\d\s=\\()_]'
t_NUMBER  = r'\d+'

def t_error (t):
    c = t.value [0]
    raise RuntimeError ('unknown symbol: %s [%d]' % (`c`, ord (c)))


lex.lex ()


# ==================================================
# BibTeX parser
# ==================================================

precedence = (
    ('left', 'SYMBOL', 'LITERAL'),
    )

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


def p_key (t):
    ''' key : keypart key '''
    t [0] = t [1] + t [2]
    return

def p_key_simple (t):
    ''' key : keypart '''
    t [0] = t [1]
    return
    
def p_keypart (t):
    ''' keypart : LITERAL
                | SYMBOL
                | NUMBER
                | LPAREN
                | RPAREN '''
    t [0] = t [1]
    return

def p_entry (t):
    ''' entry : LITERAL opt_space LBRACE opt_space key opt_space COMMA opt_space assignment_list RBRACE
              | LITERAL opt_space LBRACE opt_space key opt_space COMMA opt_space assignment_list COMMA opt_space RBRACE
              | LITERAL opt_space LPAREN opt_space key opt_space COMMA opt_space assignment_list RPAREN
              | LITERAL opt_space LPAREN opt_space key opt_space COMMA opt_space assignment_list COMMA opt_space RPAREN '''

    e = Record (t [1].lower (), t [5])
    e.update (t [9])
    
    t [0] = e
    return

def p_empty_entry (t):
    ''' entry : LITERAL opt_space LBRACE opt_space LITERAL opt_space RBRACE
              | LITERAL opt_space LPAREN opt_space LITERAL opt_space RPAREN '''
    t [0] = Record (t [1], t [5])
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

def p_assignment_bad_list (t):
    ''' assignment_list : assignment_list opt_space assignment '''
    ret = {}
    ret.update (t [1])
    ret.update (t [3])

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
    ''' brace_data : misc_data '''
    t [0] = (t [1],)
    return

def p_brace_data_quote (t):
    ''' brace_data :  QUOTE '''
    t [0] = (Text (t [1]),)
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
# BibTeX interface
# ==================================================


class Importer (object):

    def __init__ (self, charset = 'ISO8859-1'):

        self.charset = charset

        self._mapping = {
            Attribute.Text:   self.text_add,
            Attribute.Person: self.person_add,
            Attribute.URL:    self.url_add,
            Attribute.Date:   self.date_add,
            }
        return

    def url_add (self, field, stream):

        self.record [field] = [Attribute.URL (stream.flat ())]
        return


    def date_add (self, field, stream):

        self.record [field] = [Attribute.Date ()]
        return
    

    def text_add (self, field, stream):
        
        self.record [field] = [Attribute.Text (stream.flat ())]
        return

    def person_add (self, field, stream):

        ''' Parse a stream of tokens as a series of person names '''

        # The first level of the parsing is of interest, as non-person
        # names can be written for instance:
        # author = "{Name of a Company} and {Another One}"

        # Join joins, ie strings written as {toto} # {tutu}
        stream = stream.join ()

        # These high-level groups are separated by 'and' keywords
        avail  = []
        
        while 1:
            try:
                i = stream.index ('and')
            except ValueError:
                break

            avail.append (stream [0:i])
            stream = stream [i+1:]

        if stream:
            avail.append (stream)

        def _wordify (stream):

            stream = stream.execute (Environ ())
            stream = stream.subst ()

            # Ensure the stream is a sequence of complete words (ie,
            # concatenate successive text parts and space parts).  The
            # comma must remain on its own, as it serves as a separator.
            # The dot is always appended to the previous word.

            in_space = True
            os, stream = stream, []

            while os:
                s = os.pop (0)

                if s == '.':
                    stream [-1] += '.'
                    continue

                is_space = s in (' ', '\n')

                if in_space:
                    if not is_space:
                        stream.append (s)
                        in_space = False
                    continue

                else:
                    if is_space:
                        in_space = True
                    else:
                        if s == ',':
                            stream.append (s)
                            in_space = True
                        else:
                            stream [-1] += s
                    
            return stream
    
        def _typetag (stream):
            """ For each element of the string, return a list that
            indicates if the corresponding element is :
               - I : an initial
               - L : a lower case word
               - N : a name
            """
            
            tags = []
            
            for s in stream:
                if '.' in s:
                    tags.append ('I')

                elif s.lower () == s:
                    tags.append ('L')

                else:
                    tags.append ('N')

            return tags
        
        def _person_decode (stream):

            if len (stream) == 1 and isinstance (stream [0], Block):
                return Attribute.Person (last = stream [0].flat ())

            stream = _wordify (Block ('', '', stream))

            # Check for ',' syntax for names
            comma = stream.count (',')

            if comma == 0:
                # Use the number of segments in the name
                ls = len (stream)
                if ls == 1:
                    return Attribute.Person (last = stream [0])

                else:
                    tt = _typetag (stream)

                    if tt in (['N', 'I'],
                              ['N', 'I', 'I'],
                              ['N', 'I', 'I', 'I']):
                        return Attribute.Person (first = ' '.join (stream [1:]),
                                                 last  = stream [0])

                    if tt in (['N', 'N'],
                              ['I', 'N'],
                              ['I', 'I', 'N'],
                              ['I', 'I', 'I', 'N']):
                        return Attribute.Person (first = ' '.join (stream [0:-1]),
                                                 last  = stream [-1])
                    
                    raise Exceptions.ParserError ("unable to parse name properly: %s (typed as %s)" % (
                        repr (stream), repr (tt)))
                    
            elif comma == 1:
                i = stream.index (',')

                return Attribute.Person \
                       (last  = ' '.join (stream [:i]),
                        first = ' '.join (stream [i+1:]))

            return Attribute.Person ()

        self.record [field] = map (_person_decode, avail)
        return 

    
    def comment_add (self, stream):

        # by default, we drop comments
        return


    def id_add (self, data):

        self.record ['id'] = [Attribute.ID (data)]
        return

    def type_add (self, data):

        self.record ['doctype'] = [Attribute.Txo (self.doctype [data])]
        return

    def record_begin (self):

        pass

    def record_end (self):

        pass

    def record_dispatch (self, tp, k, v):

        try:
            attp = self.db.schema [k]
            
        except KeyError:
            raise Exceptions.SchemaError (
                _("no attribute '%s' in document '%s'") % (
                k, tp))
        
        self._mapping [attp.type] (k, v)
        return
    
    def record_parse (self, data):

        self.record = Store.Record ()
        self.record_begin ()

        tp, key, val = data.type, data.key, data

        self.id_add (key)
        
        for k, v in val.iteritems ():
            self.record_dispatch (tp, k.lower (), v)
            
        # Add the document type
        self.type_add (tp)
        
        self.record_end ()

        if self.record:
            self.db.add (self.record)

        return
    
    
    def parse (self, fd, db):

        self.db = db
        
        datalist = yacc.parse (fd.read ().decode (self.charset), debug = 0)

        self.doctype = {}

        for v in db.txo ['doctype'].values ():
            self.doctype [v.names ['C'].lower ()] = v

        for data in datalist:

            if isinstance (data, Comment):
                self.comment_add (data)
                continue

            self.record_parse (data)
            
        return db


# --------------------------------------------------


class Exporter (object):

    _collapse = re.compile (r'[\s\n]+', re.MULTILINE)
    
    def __init__ (self):

        import Recode

        self._mapping = {
            Attribute.Text:   self.text_add,
            Attribute.Person: self.person_add,
            Attribute.URL:    self.url_add,
            Attribute.Date:   self.date_add,
            Attribute.ID:     self.id_add,
            Attribute.Txo:    self.txo_add,
            }
        return

    def _escape (self, text):

        return text.encode ('latex', 'replace')

    def txo_add (self, field, data):

        r = []
        for d in data:
            v = self.db.txo [d.group][d.id]

            try: n = v.name
            except KeyError: n = v.names.get ('C', None)
                
            if n: r.append (n)

        data = self._escape ('; '.join (r))
        
        self.field [field] = '{%s}' % data
        return
        
    def text_add (self, field, data):

        data = self._escape (' '.join (data))
        
        # by default, new lines and multiple spaces are not significant in bibtex fields
        data = self._collapse.sub (' ', data)
        
        self.field [field] = '{%s}' % data
        return

    def id_add (self, field, data):

        data = self._escape ('; '.join (data))
        
        self.field [field] = '{%s}' % data
        return

    def _single_person (self, person):

        return '%s, %s' % (person.last, person.first)
    
    def person_add (self, field, data):

        v = self._escape (' and '.join (map (self._single_person, data)))

        self.field [field] = '{%s}' % v
        return

    def url_add (self, field, data):

        v = ', '.join (data)
        
        self.field [field] = '{%s}' % v
        return

    def date_add (self, field, data):

        v = str (data [0].year)
        
        self.field [field] = v
        return

    def record_begin (self):

        self.key = str (self.record ['id'] [0])

        tp = self.record ['doctype'] [0]
        self.type = self.db.txo [tp.group][tp.id].names ['C']

        return

    def record_end (self):

        return

    def record_parse (self, key, value):

        if key in ('id', 'doctype'): return

        key = key.encode ('ascii', 'replace')
        
        self._mapping [self.db.schema [key].type] (key, self.record [key])
        return
    
    def write (self, fd, rs, db):

        """ Write a result set to a given file descriptor """

        self.db = db
        self.rs = rs
        
        self.doctype = {}

        for v in db.txo ['doctype'].values ():
            self.doctype [v.names ['C'].lower ()] = v

        for e in rs.itervalues ():

            self.record = e

            self.field = {}
            self.type  = None
            self.key   = None
        
            self.record_begin ()

            for k, v in e.items ():
                self.record_parse (k, v)

            self.record_end ()
            
            ret = '@%s{%s,\n' % (self.type, self.key)

            attrs = []
            keys  = self.field.keys ()
            keys.sort ()

            maxlen = 0
            for k in keys:
                l = len (k)
                if l > maxlen: maxlen = l
            
            for k in keys:
                v = self.field [k]
                
                left = '   %s%s = ' % (k, ' ' * (maxlen - len (k)))

                attrs.append (left + Tools.format (v, 75, 0, len (left)))

            fd.write (ret + ',\n'.join (attrs) + '\n}\n')

        return
    
