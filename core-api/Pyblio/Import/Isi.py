#This file is part of Pybliographer
# 
# Copyright (C) 2001, 2003 Peter Schulte-Stracke
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

"""Import module for ISI style files.

These files are

"""


import getpass, re, rfc822, string, time, types # XXXX

from Pyblio import Base
from Pyblio.Import import Tagged

    
login_name = getpass.getuser()

# the following list gives all recognised tags for Isi formats.  If the
# tag forms part of the key_map (i.e. is not commented out), this is to
# be understood as giving the bibtex field name and a continuation
# character for this field.  If the continuation character is 0, the
# field is unique  (non-repeatable).

# If the line is commented out, either a field is given in parentheses,
# indicating that the transformation is coded below, or it is handled
# generically.  

key_map = {   
    'AB' : ('abstract', '\n'),
#   'AU' : (author)
#   'BP' (pages)  first page
#   'BS' (title)  subtitle
    'CR' : ('citedref', '\n'),
    'C1' : ('authoraddress', '\n'),
    'DE' : ('keywords', ' ; '),
#   'DT', 'Mytype',		# type = lowercace(DT)
#   'EP' (pages)  last page
#   'ER'   End of record
#   'FN', 0, # File type (should be: 'ISI Export Format')
#   'GA', 0, # ISI document delivery number
#   'ID', 'KeywordsPlus',
    'IS' : ('number', ' ; '),
#   'J9', 0, # 29-character source title abbreviation
#   'JI', 'Journal',
    'LA' : ('language', ' ; '),
#   'NR', 0, # Cited reference count
#   'PA', 'Address',	# publishers address 
    'PD' : ('month', ' ; '),
#   'PG', 'PagesWhole',	# Page count
#   'PI', 0, # Publisher city
#   'PP', 'Pages',		# is "BP -- EP"
#   'PT', 0, # Publication type (e.g., book, journal, book in series)
    'PU' : ('publisher', 0),
    'PY' : ('date', ' ; '),
#   'RP', 0, # Reprint address
    'SE' : ('series', ' '),
    'SN' : ('issn', ' ; '),
#   'SO', 'FullJournalName',
#   'TC', 0, # Times cited
    'TI' : ('title', ' '),
#   'UT', 0, # internal ISI number
    'UT' : ('sourceid', ' ; '),
    'VL' : ('volume', ' ; ')
#   'VR', 0, # File format version number (should be: '1.0')
#   'WP', 'Source',
    }

monthnames = {'jan': 1, 'feb': 2, 'mar': 3, 'apr':  4, 'may':  5, 'jun':  6,
              'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
              'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr':  4, 'May':  5, 'Jun':  6,
              'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
              'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR':  4, 'MAY':  5, 'JUN':  6,
              'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}

xheader  = re.compile('^(\w\w|\w\w+:)( (.*))$')
header   = re.compile('^(\w\w)( (.*))$')
contin   = re.compile('^   (.*)$') 
sporadic = re.compile('^isifile-(..)$')

field_map = None

def reverse_mapping(map):
    remap = {}
    for key in map.keys():
        remap[map[key][0]] = key
    return remap


output = None                  # set by 

try: _
except NameError:
    def _(s): return s



def output_write(key, text):
    # A text is either a string or a list:
    if type(text) == types.ListType:
        output.write ('%2s %s\n' %(key, text[0]))
        for t in text[1:]:
            output.write ('   %s\n' %(t))
    elif str(text):    
        output.write ('%2s %s\n' % (key, Utils.format(
            str (text), 70, 0, 3)))
pagenum  = re.compile('(\d) p\.')
keywds   = re.compile('(.*)\[ISI:\] *(.*);;(.*)')



class Reader(Tagged.Reader):
    ''' This class exports two functions: next and ,
    each of which returns an bibliographic entry from the input file.
    In addition is saves extraneous text (pre- and postamble).'''

    def __init__(self, 
                 *args, **argh):
        self.extraneous = []
        self.isifileformat = None
        self.isifileinfo = None
        #self.current_line = '' ### Warning: changed by Import.Reader.__init__
        Tagged.Reader.__init__ (self,
            tagcol=5, *args, **argh)

        
## the following could go into __init__ as well
        
    def read_first(self, *args, **argh):
        #self.source.seek(0)
        self.current_line = self.source.readline()
        file_notes, file_time, file_version, file_format = ('','','','')
        while self.current_line:

            assert self.current_line != ''
            head = xheader.match(self.current_line)
            if not head :
                pass
            elif head.group(1) == 'Date:':
                file_time = time.strftime(
                    "%Y-%m-%d %H:%M", rfc822.parsedate(head.group(2)))
            elif head.group(1) == 'Notes:':
                file_notes = string.strip(head.group(2))
            elif head.group(1) == 'FN':
                file_format = head.group(2)
            elif head.group(1) == 'VR':
                file_version = head.group(2)
            elif len(head.group(1)) == 2 :
                break
            else :
                pass
            self.extraneous.append(self.current_line)
            self.current_line = self.source.readline()

        self.isifileformat = self.isifileformat or "Isifile format %s(%s)" % (
            file_format, file_version)
        self.isifileinfo = self.isifileinfo or "ISI %s (%s) %s" %(
            file_time, file_notes, login_name)
        return 

    def read_next (self, source):
        self.firstpg, self.lastpg, self.numberpg = [''], [''], ['']
        self.journaln = ''
        self.journald = ''
        self.pubmonth = ''
        self.pubyear  = ''
        
        lines = []
        line = []

        while self.current_line == '\n':
            self.current_line = source.readline()
        if not self.current_line : return None

        while self.current_line not in ['',  '\n']:
            head = xheader.match(self.current_line)

            if head :
                tag = head.group(1)
                if line: lines.append(line)
                line  = [tag, head.group(3)]
            else:
                cont = contin.match(self.current_line)
                if cont : 
                    val = cont.group(1)
                    line.append(val)

            self.current_line = source.readline()
        while self.current_line == '\n':
            self.current_line = source.readline()
        lines.append (line)
        #print 'ISI INPUT DATA\n   <<', lines, '>>'
        return lines


#   'AB' : ('abstract', '\n'),

    def do_AU (self, tag, data):
        """AU : author"""
        for item in data:
            if string.strip(item) =='[Anon]' : pass
            else:        
                name, firstn = string.split (item, ',')
                #print 'ISI AU:', name, firstn
                self.add_person(name, initials=firstn,
                                role=Base.AUTHOR_ROLE)
        return

    def do_BP (self, tag, data):
        """BP : First page """
        self.firstpg = data[0]
        return
    

#   'BS' (title)  subtitle
#   'CR' : ('citedref', '\n'),
#   'C1' : ('authoraddress', '\n'),
#   'DE' : ('keywords', ' ; '),
#   'DT', 'Mytype',		# type = lowercace(DT)

    def do_EP (self, tag, data):
        """EP  Last page"""
        self.lastpg = data[0]
        return
    
#   'ER'  # End of record (never seen)
#   'FN', # File type (should be: 'ISI Export Format')
#   'GA', # ISI document delivery number
#   'ID', 'KeywordsPlus',

    def do_IS (self, tag, data):
        """IS : Issue number of journal"""
        self.add_simple_nr('number', data[0])
        return
    
#   'J9', 0, # 29-character source title abbreviation

    def do_JI (self, tag, data):
        self.journald = data[0]
        return

#   'LA' : ('language', ' ; '),
#   'NR', 0, # Cited reference count
#   'PA', 'Address',	# publishers address 

    def do_PD (self, tag, data):
        month = data[0]
        self.pubmonth = monthnames.get(month, 0)
#    'PD' : ('month', ' ; '),

    def do_PG (self, tag, data):
        self.add_simple ('size', '%s pp.' %(data[0]))
        return

#   'PI', 0, # Publisher city
#   'PP', 'Pages',		# is "BP -- EP"

    def do_PT (self, tag, data):
        #print 'PT:', data
        if string.strip(data[0]) != 'J':
            print 'Warning: Unknown type of entry (%s) -- may need editing.' %(
                data)
        return
#   'PT', 0, # Publication type (e.g., book, journal, book in series)
#   'PU', 'Publisher',

    def do_PY (self, tag, data):

        try:
            self.pubyear = int(data[0])
        except:
            import traceback
            traceback.print_exc()
            self.pubyear = 0
        #self.jentry.add_simple_nr ('date', data[0])
        #self.add_simple_nr ('date', data[0])
        return
#    'PY' : ('date', ' ; '),
#   'RP', 0, # Reprint address
#    'SE' : ('series', ' '),

    def do_SN (self, tag, data):

        self.add_simple('issn', data[0])
        return
#    'SN' : ('issn', ' ; '),
    
    def do_SO (self, tag, data):
        self.journaln = data[0]
        return
#   'SO', 'FullJournalName',
#   'SO' : ('journal', ' ; '),

    def do_SU (self, tag, data):
        #self.add_journal(issn=data[0])
        self.journali = data[0]
        return
#   'TC', 0, # Times cited

    def do_TI (self, tag, data):
        """TI title"""
        self.add_title(string.join(data, ' '))
        return

    def do_UT (self, tag, data):
        self.add_number ('C', 'ISI',
                         value=data[0],
                         )

#    'UT', 0, # internal ISI number
#    'UT' : ('sourceid', ' ; '),
    
    def do_VL (self, tag, data):
        self.add_simple_nr('volume', data[0])
        return
#    'VL' : ('volume', ' ; ')}
#    'VR', 0, # File format version number (should be: '1.0')
#    'WP', 'Source',


    def do_tag (self, tag, data):

        #print 'DO_TAG:', tag, data, "//".join(data)

        if key_map.has_key(tag):
            self.add_simple (key_map[tag][0], "//".join(data), key_map[tag][1])
        else :
            #print "Unknown tag %s for %s" %(tag, data)
            self.add_simple ("isi-%s" %(tag), "//".join(data))
        return

    def finish (self, *args, **argh):

        """Finish processing of input entry.  Combine several input
        fields.
        """

        #print `self.entry.dict`
        if self.lastpg:
            pages= '%s-%s' % (self.firstpg, self.lastpg)
        else:
            pages = '%s' % (self.firstpg)
        self.add_simple_nr ('pages', pages)

        i , Title = 0, []
        uc_title = re.split(r"([- .,/]+)", self.journaln) # title words in UPPERCASE
        ca_title = re.split(r"[- .,/]+",self.journald) # Capitalised words, abbrev.

        if ca_title == ['']:  # c'est drôle
            Title = self.journaln.title()
        else:
            for word in uc_title:
                Word = string.capitalize(word)
                if word == ca_title [i]:
                    Title.append (word)
                    i += 1
                elif Word.startswith(ca_title[i]):
                    Title.append(Word)
                    i += 1
                else:
                    Title.append(string.lower(word))
            self.add_simple('journal', "".join(Title))


        #date = Fields.Date((self.pubyear, self.pubmonth, 0))
        date = "%s-%s" %(self.pubyear, self.pubmonth)
        self.add_simple_nr('date',  date)
        return    

## Autoload.register ('format', 'Isifile', {'open': opener,
##                                          'write': writer,
##                                          'iter': iterator})


### Local Variables:
### Mode: python
### py-master-file: "../../tests/ut_Isi.py"
### End:
