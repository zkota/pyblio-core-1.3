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

from Pyblio.Importers.BibTeX import Reader, Coding

from Pyblio import Attribute, Store, Exceptions, Tools

from gettext import gettext as _

# ==================================================
# Base Classes
# ==================================================

class Environ (Coding.Environ):

    def __init__ (self):

        self.strings = {}
        return


# ==================================================
# BibTeX interface
# ==================================================
_lf_re = re.compile ('N+I+')
_fl_re = re.compile ('I+N+')

_split_re = re.compile (r'[,.]|\s+')

class Importer (object):

    def __init__ (self, charset = 'ISO8859-1'):

        self.charset = charset

        self._mapping = {
            Attribute.Text:   self.text_add,
            Attribute.Person: self.person_add,
            Attribute.URL:    self.url_add,
            Attribute.Date:   self.date_add,
            }

        self.env = Environ ()
        
        return

    def url_add (self, field, stream):

        self.record [field] = [Attribute.URL (stream.flat ())]
        return


    def date_add (self, field, stream):

        self.record [field] = [Attribute.Date ()]
        return
    

    def text_add (self, field, stream):
        self.record [field] = [Attribute.Text (stream.execute (self.env).flat ())]
        return

    def person_add (self, field, stream):

        ''' Parse a stream of tokens as a series of person names '''
        
        # The first level of the parsing is of interest, as non-person
        # names can be written for instance:
        # author = "{Name of a Company} and {Another One}"


        # Join joins, ie strings written as {toto} # {tutu}
        stream = stream.join ()

        # ...and expand the low-level text in fragment split on "," "." and space
        stream, os = [], stream
        for v in os:
            if not isinstance (v, Reader.Text):
                stream.append (v)
                continue

            i = 0
            for m in _split_re.finditer (v):
                s, e = m.start (0), m.end (0)
                if i != s: stream.append (Reader.Text (v [i:s]))

                sep = Reader.Text (v [s:e])
                if sep [0] in ' \n\t': sep = Reader.Text (' ')
                stream.append (sep)
                
                i = e

            if i < len (v): stream.append (Reader.Text (v [i:]))
            
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

            stream = stream.execute (self.env)
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

                elif s.lower () in ('van', 'von', 'de'):
                    tags.append ('L')

                else:
                    tags.append ('N')

            return tags
        
        def _person_decode (stream):

            if len (stream) == 1 and isinstance (stream [0], Reader.Block):
                return Attribute.Person (last = stream [0].flat ())

            stream = _wordify (Reader.Block ('', stream))

            # Check for ',' syntax for names
            comma = stream.count (',')

            if comma == 0:
                # Use the number of segments in the name
                ls = len (stream)
                if ls == 1:
                    return Attribute.Person (last = stream [0])

                else:
                    tt = ''.join (_typetag (stream))

                    if _lf_re.match (tt):
                        idx = tt.index ('I')
                        return Attribute.Person (first = ' '.join (stream [idx:]),
                                                 last  = ' '.join (stream [:idx]))
                        

                    if tt == 'NN':
                        return Attribute.Person (first = stream [0],
                                                 last  = stream [1])
                    
                    if _fl_re.match (tt):
                        idx = tt.index ('N')
                        return Attribute.Person (first = ' '.join (stream [:idx]),
                                                 last  = ' '.join (stream [idx:]))

                    try:
                        von = tt.index ('L')

                        return Attribute.Person (first = ' '.join (stream [0:von]),
                                                 last  = ' '.join (stream [von:]))
                        
                    except ValueError:
                        pass

                    # As a fallback, consider that the last name is the last component
                    if tt == 'NNN':
                        return Attribute.Person (first = ' '.join (stream [:-1]),
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

    def string_add (self, stream):
        # by default, we drop strings
        return

    def preamble_add (self, stream):
        # by default, we drop the preamble
        return

    def id_add (self, data):

        self.record ['id'] = [Attribute.ID (data)]
        return

    def type_add (self, data):

        self.record ['doctype'] = [Attribute.Txo (self.doctype [data.lower ()])]
        return

    def record_begin (self):

        pass

    def record_end (self):

        pass

    def record_dispatch (self, k, v):

        try:
            attp = self.db.schema [k]
            
        except KeyError:
            raise Exceptions.SchemaError (
                _("no attribute '%s' in document '%s'") % (
                k, self.tp))
        
        self._mapping [attp.type] (k, v)
        return
    
    def record_parse (self, record):

        tp = record.type.lower ()

        if tp == 'string':
            return self.string_add (record)

        elif tp == 'preamble':
            return self.preamble_add (record)
        
        self.tp, key, val = record.type, record.key, record.fields

        self.record = Store.Record ()
        self.record_begin ()

        self.id_add (key)

        for k, v in val:
            self.record_dispatch (k.lower (), v)
            
        # Add the document type
        self.type_add (self.tp)
        
        self.record_end ()

        if self.record:
            self.db.add (self.record)

        return
    
    
    def parse (self, fd, db):

        self.db = db

        self.doctype = {}

        for v in db.txo ['doctype'].values ():
            self.doctype [v.names ['C'].lower ()] = v

        for data in Reader.read (fd, self.charset):

            if isinstance (data, Reader.Comment):
                self.comment_add (data)
                continue
            
            self.record_parse (data)
            
        return db


# --------------------------------------------------


class Exporter (object):

    _collapse      = re.compile (r'[\s\n]+', re.MULTILINE)
    
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

    def capitalized_text_add (self, field, data):

        # by default, new lines and multiple spaces are not significant in bibtex fields
        data = self._collapse.sub (' ', ' '.join (data))

        # If the text contains capitals that are not at the beginning
        # of a sentence, protect these capitals. Similarly for
        # lowercase letters at the beginning.

        res = Reader.Block ('{', [])

        beginning = True
        in_upper  = False
        block     = []
        braced    = False
        
        def _close_upper ():
            res.append (Reader.Block ('{', (Reader.Text (''.join (block)),)))
            del block[:]

        while data:
            c, data = data [0], data [1:]
            
            if c in '.!?':
                if in_upper:
                    _close_upper ()
                    in_upper = False
                
                beginning = True
                block.append (c)
                continue

            if not c.isalpha ():
                if in_upper:
                    _close_upper ()
                    in_upper = False
                
                block.append (c)

                if c == '"': braced = not braced
                continue

            if not braced:
                if beginning and c.lower () == c:
                    res.append (Reader.Text (''.join (block)))
                    res.append (Reader.Block ('{', (Reader.Text (c),)))

                    block = []
                    beginning = False
                    continue

                if (not beginning and c.lower () != c) \
                   or (beginning and data and data [0].lower () != data [0]):
                    if in_upper:
                        block.append (c)
                    else:
                        in_upper = True
                        res.append (Reader.Text (''.join (block)))

                        block = [c]
                    beginning = False
                    continue

            if in_upper:
                _close_upper ()
                in_upper = False
            
            block.append (c)
            beginning = False

            
        if in_upper: _close_upper ()
        if block: res.append (Reader.Text (''.join (block)))

        self.field [field] = res.tobib ()
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
    
