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

def id_make(last, proposed=None):

    """ Return an identifier, possibly taking into account a proposed
    id. """

    if proposed:
        if proposed >= last: last = proposed + 1

    else:
       proposed = last
       last     = last + 1

    return last, proposed

       
def format(string, width, first, next):

    ''' Format a string on a given width '''

    out = []
    current = first

    # if the entry does not fit the current width
    while len (string) > width - current:
	    
        pos = width - next - 1

	# search a previous space
	while pos > 0 and string [pos] <> ' ':
	    pos = pos - 1

	# if there is no space before...
	if pos == 0:
	    pos = width - current
	    taille = len (string)
	    while pos < taille and string [pos] <> ' ':
	        pos = pos + 1

	out.append (' ' * current + string [0:pos])
	string = string [pos+1:]
	current = next

    out.append (' ' * current + string)

    return '\n'.join (out).rstrip ()

