# This file is part of pybliographer
# 
# Copyright (C) 2002, 2003 Peter Schulte-Stracke
# Email : mail@schulte-stracke.de
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

"""Import functions for Pybliographer
 
      ##################################################
      #                                                #
      #           E X P E R I M E N T A L              #
      #                                                #
      ##################################################

Class Reader -- Base class for various Import modules.

importer -- convenience function to import from a file or in-core
data. ???

   See also GnomeUI/Import.py for related dialogues.

   Update discussion in Todo. 
"""

import os, stat, string, types
from  Pyblio import Base, Dedup

_default_options = {'preserve_input':1}

class Reader (Base.RecordSet):

    """Base class for all import reader classes.

    Support for input methods, encodings, database and GUI connections.
    A general discussion of the import framework is in the DG, chap. 7.

    This class is an instance of the Strategy pattern; it provides a
    number of slots which more specialised subclasses are expected to
    fill in or to override.  In addition it provides service routines
    that are used to help the subclass programmeer and to standardise
    behaviour.

    The external (service) interface is a (new style) Iterator
    interface, with __iter__ and next routines, in addition to a
    number of other ones.
    
    
    External interface:

    >  __init__       
    +  __iter__
    -  __del__
    *  next
    +  open
    +  close
     . . .
     
    Subclass Interface: * means: must implement

    >  start_file     read file prologue
    >  end_file
    *  read_next      return next input record
    *  parse          parse input record, return entry
    >  begin_record   called for each record upon start of parse
    >  end_record     called after parse (use for clean up)

    #  add_simple     add a standard (BibTeX) field
    #  add_simple_nr  add a nonrepeatable standard field
    #  add_person     add a person (author/editor) record and reference
    #  add_data       add raw data 

    """

    def __init__ (self, control=None, options=None,
                  interactive=0, 
                  file=None, data=None, iter=None,
                  *argv, **argh):
        
        """Input sources:
        -- file   a file name (url) or an open file *or*
        -- data   a sequence of lines *or*
        -- iter   an iterator

        Interactive means:
        
        
        """

        self.interactive = interactive
        self.entry = None
        self.jentry = None
        #self.control = control or Coco.Importer(
        #    title='Unspecified Import', options=options)
        self.options = options or _default_options
        self.source = None
        if file or data or iter:
            self.open(file=file, data=data, iter=iter)
        return

    def __del__ (self):
        self.close()
        
    def __iter__ (self):
        return self

    def close (self):
        if self.source:
            try:
                self.source.close()
            except AttributeError:
                pass

    def open (self, file=None, data=None, iter=None,
              *args, **argh):
        self.start_file (file=file, data=data, iter=iter, *args, **argh
                         ) or self.open_file(
            file=file, data=data, iter=iter, *args, **argh)

    def open_file(self, file=None, data=None, iter=None,
                  *argv, **argh):
        assert ((file != None) + (data != None) + (iter != None)
                ) <= 1, "More than one input source"

        if iter:
            #self.control.set_progress(0, -1)
            #self.read_first = iter.first
            self.read_next = iter.next
        else:
            if file:
                if type(file) == types.FileType:
                    self.source = file
                else:
                    #self.control.set_title('Unspecified Import from %s' % file)
                    self.source = open(file)
                #self.control.set_progress(0, os.fstat(self.source.fileno()
                #                                      )[stat.ST_SIZE])
            elif data:
                import cStringIO
                self.source = cStringIO.StringIO(data)
            self.read_first (self.source)
            #self.control.set_progress(0, len(data))
        #self.control.start()

        # file_position
        self.start_pos, self.end_pos = 0, 0

    def start_file(self, *args, **argh):
        """Called by open and before opening the file.  If this routine
        opens the input it returns True."""
        return False
    
    def end_file (self):
        """Called after processing the file """
        self.close()

    def begin_record (self, *args, **argh):
        """Subclass overridable routine."""
        pass

    def end_record (self, *args, **argh):
        """Subclass overridable routine."""
        pass

    def finish (self,  *args, **argh):
        """ *** Subclass overridable routine. ***

        Finish processing of one input record.  Use this routine to
        add attributes that are combined from several imput fields
        etc.
        """
        pass

    def next (self, entry=None, data=None):
        """Process the next entry from the input source. Both
        entry and data argument are provided for easy testing.
        For interactive use, self.parse is the right interface
        to use.

        """
        entry = entry or self.next_entry()
        data = data or self.read_next(self.source)

        if data :
            if self.options.has_key('preserve_input'):
                entry.lines = data
            self.entry = entry
            result =  self.parse(entry, data)
            #Dedup.dedup(result)
            return result ### not really good, i.e. if result is ignored
        else:
            raise StopIteration
       
        
    def parse (self, entry, data):
        """Major routine. Must always be subclass implemented.  This
        routine calls start_record and end_record for every record it
        produces, and finish after the processing of the input is
        completed.
        """
        raise NotImplementedError

    def next_entry (self):
        """ *** DEPRECATED ***
        Create a new empty entry for use by import routine."""
        entry = Base.create('O')
        return entry
    
### The following must be provided (if needed) by the derived class:

# Main routine:

    def unpack (self, data): # needed if unpacked data is used
        """Unsure about this routine ***
        It could unpack the data object, setup a memory file
        and return this, but alternatively could return the data,
        and setup read_next in a suitable way.

        XXXX
        
        """
        raise NotImplementedError

    def read_first (self):
        """Skip over the beginnign of the input file until an input
        record commences."""
        pass

    def read_next (self, source):

        """Read input data for one record. Subclass implemented.
        Return the data as either a sequence of lines or (e.g., for
        tagged input) a sequence of sequences, starting with the tag
        (or the empty string for the leader).

        Note: some formats within the scope of TaggedReader delimit
        information with newlines (e.g., ISI), others do not break
        lines at all (e.g., MARC), but are often given in a
        convenience format with line breaks. To accomodate them all,
        use the following rules: If the input field comes in several
        lines, respect the line breaks but remove the newline
        characters. If a reader uses both, broken and unbroken
        input, it is to implement prepare_data to join the lines.
        
        For interactive use, we need an indication of the text
        reletive to the input as a whole, if the limits are in any way
        subject to manual intervention.  For that purpose, we have
        start_pos, end_pos with both set to zero in the trivial case.

        So the interactive applicaton has to check end_pos to determine
        if it is posssible to change the boundries of the input data.

        The parsing routines are shielded from the input, they must
        never access the input directly.
        

        """

        raise NotImplementedError

    def read_next_indent(self, source):

        """Read data with indented continuation lines."""

        if not line :
            line = source.readline()
            self.line_counter += 1
        lines = [line]
        self.line_number = self.line_counter        
        line = source.readline()
        self.line_counter += 1
        while line and line[0] in string.whitespace:
            lines.append(line)
            line = source.readline()
            self.line_counter += 1
            
        
        return lines

    def prepare_data(self, data):
        """Subclass overridable. Joins lines that were input broken."""
        return data

    #   Interface routines
    #--------------------------------------------------

    def add_simple (self, field, value, join='', referent=None):
        """add the value to the field, if necessary joining with join."""

        assert self.entry.Typ == 'O'
        try:
            self.add_simple_nr (field, value, referent=referent)
        except KeyError:
            self.entry.dict[field] = '%s%s%s' %(
                self.entry.dict[field], join, value)
        #print 'ADD SIMPLE:', field, value, self.entry[field]

    def add_simple_nr (self, field, value, join='', referent=None):
        """Add the value to the field, raise KeyError if duplicate."""
        assert self.entry.Typ == 'O'
        if self.entry.has_key(field):
            #print 'ADD SIMPLE NR KEY ERROR:', field, self.entry[field]
            raise TypeError
        else:
            self.entry.dict [field] = value
        #print 'ADD SIMPLE NR:', field, value

    def add_number (self, kind, name, value=None, timestamp=0):
        pass

    def add_person (self, name='', initials='', role=Base.AUTHOR_ROLE,
                    referent=None):
        assert name != '', "short name"
        #assert  self.entry is Base.Record
        if name.isupper():
            import re
            parts = re.split("([- /.,]+)", name)
            name = "".join([x.capitalize() for x in parts])
        if initials:
            #print "»%s«" %(initials)
            initials = initials.strip()
            if initials.isalpha():
                initials = '. '.join(initials.strip())

            real_name = "%s, %s." %(name, initials)
        else:
            real_name = name    
        #print 'ADD PERSON:', real_name
        if role == Base.AUTHOR_ROLE:
            if self.entry.dict.has_key('author'):
                self.entry['author'] = "%s and %s" %(self.entry['author'], real_name)
            else:
                self.entry['author'] = real_name
                
        elif role == Base.EDITOR_ROLE:
            self.entry['editor'] = real_name
        else:
            self.add_simple('note', "Other person: %s(%d)" %(real_name, role))

    def add_title (self, title, *args, **argh):
        self.add_simple_nr('title', title)

def importer (name=None, control=None):
    """ Import from a file or an internal result set. Both
    are modelled as an iterator. ???

    from:       Iterator (or Scan) to be imported.
    control:    Coco object associated

    Returns:    a coco object An inport object) ?"""

    pass
    

# Local Variables:
# py-master-file: "ut_Import.py"
# End:
