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
from PyblioUI.Undo import Undoable


def format_guess (filename):

    f, x = os.path.splitext (filename)
    
    if x == '.bip':
        if os.path.isdir(x):
            return 'bsddb'
        
        return 'file'
    
    raise RuntimeError (_('unknown file format'))


class Document (Undoable):

    def __init__(self, filename=None, format=None, db=None):
        Undoable.__init__(self)

        assert filename is not None

        self._filename = filename
        
        if db is not None:
            self.db = db
            return
        
        self.db = None
        
        if format is None:
            format = format_guess(filename)
        
        self._format   = format

        da = Store.get(self._format)

        self.db = da.dbopen(self._filename)
        return

    def _txo(self):
        return self.db.txo

    txo = property(_txo, None)

    def _schema(self):
        return self.db.schema

    schema = property(_schema, None)


    def title(self):
        return os.path.basename (self._filename)

    def __setitem__(self, k, v):
        old = self.db[k]

        def do():
            self.db[k] = v
            self.emit('record-changed', k)

        def undo():
            self.db[k] = old
            self.emit('record-changed', k)

        self.doAction(do, undo)
        return

    def delete(self, ks):

        olds = [self.db[k] for k in ks]
        
        def do():
            for k in ks:
                self.emit('record-deleting', k)
                del self.db[k]
                self.emit('record-deleted', k)

        def undo():
            for old in olds:
                k = self.db.add(old, key=old.key)
                self.emit('record-added', k)

        self.doAction(do, undo)
        return

    def add(self, v):
        def do():
            k = self.db.add(v)
            self.emit('record-added', k)

            def undo():
                del self.db[k]
                self.emit('record-deleted', k)

            return undo

        self.doAction(do, None)
        return

    
