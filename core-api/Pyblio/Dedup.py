# This file is part of pybliographer
# 
# Copyright (C) 2003, Peter Schulte-Stracke
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
# $Id:$

"""

      ##################################################
      #                                                #
      #           E X P E R I M E N T A L              #
      #                                                #
      ##################################################


"""

try: _
except NameError:
    def _(s) \
        : return s

#   Dispositions
#------------------------------------------------------------

IGNORE_DISP   =  1 << 0
# new record (subject) is already in the database, ignore it

AUGMENT_DISP  =  1 << 1
COALESCE_DISP =  1 << 2
UPGRADE_DISP  =  1 << 3


#   Main Routines
#------------------------------------------------------------

def gather (subject):
    """ """
    if False: yield None
    raise StopIteration

def check (subject, item):
    return

def dedup (subject):
    """ """
    candidates_list = []
    for i in gather(subject):
        candidates_list.append(check (subject, i))
    #print 'Candidates:', candidates_list
    return 






# Local Variables:
# py-master-file: "../tests/ut_Dedup.py"
# End:
