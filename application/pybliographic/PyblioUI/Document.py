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

import os

from gettext import gettext as _

from Pyblio import Store


def format_guess (filename):

    f, x = os.path.splitext (filename)
    
    if x == '.pbl':    return 'file'
    if x == '.pbl-db': return 'bsddb'
    
    raise RuntimeError (_('unknown file format'))


class Document (object):

    def __init__ (self, filename, format = None):

        self.db = None
        
        assert filename is not None

        if format is None: format = format_guess (filename)
        
        self._filename = filename
        self._format   = format

        da = Store.get (self._format)

        self.db = da.dbopen   (self._filename)
        return

    
    def title (self):

        return os.path.basename (self._filename)
