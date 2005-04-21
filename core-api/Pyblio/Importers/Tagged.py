# This file is part of pybliographer
# 
# Copyright (C) 1998-2003 Frederic GOBRY
# Email : gobry@pybliographer.org
# 	   
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#   
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.

from gettext import gettext as _

from Pyblio import Callback, Store, Attribute


class Parser (object):

    """ Generic Parser for 'tagged' records, to be derived by actual
    parsers. An actual subclass will need to at least override the
    self.line_handler () method to generate events by calling
    self.push (). The parser is in charge of general state
    bookkeeping, and that sort of things..."""

    
    EV_RECORD_START, EV_RECORD_END, EV_FIELD_START, \
                     EV_FIELD_DATA, EV_FIELD_END, EV_FILE_END = range (6)

    # States
    ST_IN_RECORD, ST_IN_FIELD, ST_OUTSIDE = range (3)

    
    def __init__ (self, fd, charset = 'UTF-8'):

        """ Create a new parser for a file containing 'tagged' records """

        self._fd = fd
        self._ln = 0
        
        self._charset = charset
        self._stack   = []
        self._evstack = []
        self._started = False

        self.state = self.ST_OUTSIDE

        self.file_start ()
        return


    def file_start (self):
        """ Override me to have a function called before the first
        record is to be parsed """
        
        pass

    
    def file_stop (self):

        """ Override me to be called after the last record has been parsed """

        pass

    def line_handler (self, line, number):

        """ Override me to handle each line of input and generate
        self.push () events. Will be called with line == '' when the
        end of file is reached. """

        return
    

    def field_handler (self, tag, value):

        """ Transforms a single field of a record """

        return tag, value.decode (self._charset)


    def push (self, * ev):

        """ Emit a new event. Available events are listed below, with
        their additional parameters listed, when needed:
        
           - self.EV_RECORD_START
           - self.EV_RECORD_END
           - self.EV_FIELD_START, tag, line
           - self.EV_FIELD_DATA,  data
           - self.EV_FIELD_END
           - self.EV_FILE_END

        """
       
        self._evstack.append (ev)
        return

    def record_start (self):
        self.push (self.EV_RECORD_START)
        return
    
    def record_end (self):
        self.push (self.EV_RECORD_END)
        return
    
    def field_start (self, tag, line):
        self.push (self.EV_FIELD_START, tag, line)
        return
    
    def field_end (self):
        self.push (self.EV_FIELD_END)
        return
    
    def field_data (self, data):
        self.push (self.EV_FIELD_DATA, data)
        return
    

    def unread (self, line, count):

        """ Put back a line so that it will be returned by self._pop
        when it is next invoked."""

        self._stack.append ((line, count))
        return


    def next (self):

        """ Call this function to get the next record as a list of tuples

            [ (tag, value), ...]

            or None when there are no more records """
        
        record = []

        while 1:
            ev = self._ev_pop ()

            ev, args = ev [0], ev [1:]

            if ev == self.EV_FILE_END:
                if self.state != self.ST_OUTSIDE:
                    raise SyntaxError (_('line %d: unexpected end of file') % self._ln)
                self.file_stop ()
                return None

            if ev == self.EV_RECORD_END:
                if self.state != self.ST_IN_RECORD:
                    raise SyntaxError (_('line %d: unexpected end of record') % self._ln)
                self.state = self.ST_OUTSIDE
                return record

            if ev == self.EV_RECORD_START:
                if self.state == self.ST_IN_RECORD:
                    raise SyntaxError (_('line %d: nested record') % self._ln)

                self.state = self.ST_IN_RECORD
                
                record = []
                continue

            if ev == self.EV_FIELD_START:
                if self.state == self.ST_IN_FIELD:
                    raise SyntaxError (_('line %d: nested field') % self._ln)

                if self.state == self.ST_OUTSIDE:
                    raise SyntaxError (_('line %d: field is not in a record') % self._ln)

                self.state = self.ST_IN_FIELD
                
                tag, start = args
                data = ''
                continue
            
            if ev == self.EV_FIELD_DATA:
                if self.state != self.ST_IN_FIELD:
                    raise SyntaxError (_('line %d: unexpected field content') % self._ln)
                
                data = data + args [0]
                continue

            if ev == self.EV_FIELD_END:
                record.append ((start,) + self.field_handler (tag, data))

                self.state = self.ST_IN_RECORD
                continue

        return

    def _ev_pop (self):

        """ Parse enough lines to get the next event """

        while 1:
            try:
                return self._evstack.pop (0)

            except IndexError:
                pass

            line, count = self._pop ()

            self.line_handler (line, count)
            
            if line == '': self.push (self.EV_FILE_END)
            
        return

    
    def _pop (self):

        """ Return a line from the file with its line number. """
        
        try:
            line, count = self._stack.pop ()

        except IndexError:
            self._ln = self._ln + 1
            
            line  = self._fd.readline ()
            count = self._ln
            
        return line, count



class Importer (Callback.Publisher):

    Parser = None

    def parse (self, fd, db, charset = 'UTF-8'):

        self.parser = self.Parser (fd, charset)
        self.db = db

        self.emit ('file-start')
        
        while 1:
            record = self.parser.next ()
            
            if record is None: break

            self.record_parse (record)

        self.emit ('file-stop')
        return

    def record_begin (self):

        pass

    def record_end (self):

        pass

    def record_parse (self, record):

        self.record = Store.Record ()
        
        self.record_begin ()
        
        for line, tag, data in record:

            try:
                cmd = getattr (self, 'do_%s' % tag.replace ('-', '_'))

            except AttributeError:

                try:
                    cmd = getattr (self, 'do_default')

                except AttributeError:

                    self.emit ('warning', _('line %d: unhandled tag %s' % (
                        line, `tag`)))
                    continue

            cmd (line, tag, data)

        self.record_end ()

        # The record might have been discarded by self.record_end (),
        # so insert conditionally.
        if self.record is not None:
            
            k = self.db.add (self.record)
            self.emit ('record-added', k)

            self.record = None
            
        return

    def text_add (self, field, value):

        f = self.record.get (field, [])
        f.append (Attribute.Text (value))
        
        self.record [field] = f
        return
    
    def id_add (self, field, value):

        f = self.record.get (field, [])
        f.append (Attribute.ID (value))
        
        self.record [field] = f
        return
    
    def url_add (self, field, value):

        f = self.record.get (field, [])
        f.append (Attribute.URL (value))
        
        self.record [field] = f
        return
    
