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

from Pyblio import Store


class Database (Store.Database):

    def __init__ (self, schema = None, file = None):

        Store.Database.__init__ (self, schema, file)

        self.file = file
        return
    
    def save (self):

        try:
            os.unlink (self.file + '.bak')
        except OSError:
            pass

        if os.path.exists (self.file):
            os.rename (self.file, self.file + '.bak')

        fd = open (self.file, 'w')
        self.xmlwrite (fd)
        fd.close ()

        return


def dbdestroy (path):

    os.unlink (path)
    return

    
def dbcreate (path, schema):

    db = Database (schema = schema)
    db.file = path

    return db


def dbopen (path):

    return Database (file = path)

