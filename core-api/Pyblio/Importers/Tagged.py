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


class Tagged (object):

    """ Generic Parser for 'tagged' records, to be derived by actual
    parsers."""

    # A regex with 2 groups, the tag and the data
    start_re = None

    # A regex with 1 group, the continued data
    contd_re = None

    # A line that matches this regex marks the end of a record
    split_re = None


    def __init__ (self, fd, charset = 'UTF-8'):

        """ Create a new parser for a file containing 'tagged' records """

        self._fd = fd
        self._ln = 0
        
        self._charset = charset
        self._stack = []
        self._started = False
        return


    def file_start (self):
        """ Override me to have a function called before the first
        record is to be parsed """
        
        pass

    
    def file_stop (self):

        """ Override me to be called after the last record has been parsed """

        pass

    def line_handler (self, line):

        """ Transforms a single line of input, possibly returning None to skip the line """

        return line
    

    def field_handler (self, tag, value):

        """ Transforms a single field of a record """

        return tag, value.decode (self._charset)


    def next (self):

        if not self._started:
            self.file_start ()
            self._started = True

        record  = []

        while 1:
            line = self._pop ()

            if line is None:
                if record: return record

                self.file_stop ()
                return None

            match = self.start_re.match (line)
            if match is None:
                raise SyntaxError (_('line %d: syntax error') % self._ln)

            tag, data = match.groups ((1, 2))
            start     = self._ln
            
            while 1:
                line = self._pop ()
                if line is None: break
            
                match = self.contd_re.match (line)
                if match is None:
                    self._unpop (line)
                    break

                data = data + match.group (1)

            record.append ((start,) + self.field_handler (tag, data))
            
            # check for record boundary
            done = False
            
            while 1:
                line = self._pop ()
                
                if line is None:
                    done = True
                    break
                
                if self.split_re.match (line):
                    done = True
                else:
                    self._unpop (line)
                    break

            if done: break

        return record
            
    def _pop (self):

        """ Return a line from the file that should not be skipped, or
        None if the end of file has been reached. """
        
        while 1:
            
            try:
                line = self._stack.pop ()

            except IndexError:
                self._ln = self._ln + 1
            
                line = self._fd.readline ()
                if line == '': return None

            line = self.line_handler (line)
            if line is not None: break

        return line


    def _unpop (self, line):

        """ Put back a line so that it will be returned by self._pop
        when it is next invoked."""

        self._stack.append (line)
        return

            

        

        
