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

from gettext import gettext as _

import os

from Pyblio import Store


class Database (Store.Database):

    def __init__ (self, schema = None, file = None, create = False):

        self.file = file
        
        if create:

            # WARNING: this code contains a race condition. This
            # exception is only here to trap blatant errors, not to
            # avoid concurrent accesses. How does one open a file with
            # O_CREAT, BTW ? Mabe this would not be portable at all.
            
            if os.path.exists (file):
                raise Store.StoreError (_("database '%s' already exists") % file)
            
            Store.Database.__init__ (self, schema = schema)
            self.save ()

        else:
            Store.Database.__init__ (self, file = file)
        return


    def query (self, word, sort, name = None):

        res = []
        for entry in self.itervalues ():

            found = False
            
            for attrs in entry.values ():
                idx = sum (map (lambda x: x.index (), attrs), [])
                
                if word in idx:
                    found = True
                    break
                
            if not found: continue

            res.append ((entry [sort] [0].sort (), entry.key))

        def zipsort (a, b):
            return cmp (a [0], b [0])

        res.sort (zipsort)

        if not res: return res
        
        return apply (zip, res) [1]
        
    
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


def dbdestroy (path, nobackup = False):

    os.unlink (path)

    if nobackup:
        try:
            os.unlink (path + '.bak')
            
        except OSError:
            pass
    return

    
def dbcreate (path, schema):

    return Database (schema = schema, file = path,
                     create = True)


def dbopen (path):

    return Database (file = path)

