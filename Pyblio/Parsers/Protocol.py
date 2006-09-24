# This file is part of pybliographer
# 
# Copyright (C) 1998-2006 Frederic GOBRY
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

"""
Protocol definition for importing or exporting data from alien file
formats.

Complying to the specified interfaces ensures that the importers and
exporters can be reused from dynamic components like user interfaces.
"""

from protocols import Interface

class IReader(Interface):

    def parse(self, fd, db):
        """
        Parse a file into a database.
        
        Parse the file specified by fd, and fill in db with the
        corresponding records.
        """

class IWriter(Interface):

    def write(self, fd, rs, db):
        """
        Export records in a file.

        Export the records specified in 'rs' into to file 'fd'.
        """
        
