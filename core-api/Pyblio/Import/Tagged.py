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


"""Tagged -- module for data import from tagged records (like Marc,
             Medline, etc.)

      ##################################################
      #                                                #
      #           E X P E R I M E N T A L              #
      #                                                #
      ##################################################

Class Reader -- base class for input modules that read data that
      contain a category code in front of the data. Typical examples
      are classical MARC, Medline, MAB, Refer and many more.

      Usage Notes
      -----------

      Must be subclassed by individual import modules.

      Input is read until one entry is complete; it is then (in
      typical cases) transformed into a sequence of sequences, each
      consisting of a tag as first eleemnt and the input line(s) as
      strings, following. Example:

          [ ['AU', 'Gobry, Frédéric', 'Schulte-Stracke, Peter'], ...]

"""
from Pyblio.Import import Import
import re, string
import traceback

_discard_tag = []
_discard_rx = ''



class Reader(Import.Reader):
    """
    Parameters are (missing):

    """
    def __init__(self, tagcol=0,
                 discard_tag=None, discard_rx=None,
                 *args, **argh):

        self.cache = {'': self.do_leader} 
        self.tagcol = tagcol
        discards = discard_tag or _discard_tag
        discardr = discard_rx or _discard_rx
        if discardr:
            discards.append(discardr)
        if discards:
            self.discardrx = re.compile(string.join(discards,'|'))
        else:
            self.discardrx = None
        #print discards
        Import.Reader.__init__(self, *args, **argh)
        return

    # input to parse is an entry (note that connection to the rest of the
    # system is via self) and the data that comes essentially in two
    # forms: a sequence of text lines (e.g. for Text Reader), and a
    # sequence of sequences, the head of which being the tag (empty
    # string for the leader).

    def parse (self, entry=None, data=None):
        #self.entry = entry or self.next_entry()
        self.begin_record(entry)
        
        # it may be convenient, if the read_next routine already
        # assembles continuation lines. Let's assume this

        for i in data:

            tag = i[0]
            lines = i[1:]
            if self.discardrx and self.discardrx.match(tag):
                continue
                      
            if len(lines) > 1:
                lines = self.prepare_data(lines)

            if self.cache.has_key(tag):
                self.cache[tag] (tag, lines)
            else:
                methname = 'do_'+str(tag)

                if hasattr(self, methname):
                    method = getattr(self, methname)
                else :
                    method = self.do_tag
                    
                method (tag, lines)
                self.cache[tag] = method
        self.finish()
        self.end_record(entry)
        return self.entry


### In need of subclass implementation
    
    def read_next (self):
        """ """
        raise NotImplementedError
    
    def do_leader (self, tag, data):
        
        raise NotImplementedError

    def do_tag(self, tag, data):
        """Process remaining tagged fields."""
##         if self.option_keep == 0:
##             pass
##         elif self.option_keep == 1 and tag in standard_fields:
##             self.add_extra (tag, data)
##         elif self.option_keep == 2 and tag in extra-fields:
##             self.add_extra (tag, data)
##         else : # self.option_keep == 3:
##              self.add_extra (tag, data)
        # could go as well into base class ?
        
        # perhaps place here the old code
        print 'DO TAG %s: %s' %(tag, `data`)
        return
    
