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
Provides an UNSAVED in-memory store.

This store is useful when processing a temporary database whose size
does not exceed the memory of the computer.
"""

from gettext import gettext as _

from Pyblio import Store
from Pyblio.Stores.filestore import Database


def dbdestroy(path, nobackup=False):
    return

    
def dbcreate(path, schema, args={}):
    db = Database (schema=schema, file=None, create=True)
    
    return db


def dbopen(path, args={}):
    raise Store.StoreError(_("there is no way to open an in-memory database"))


def dbimport(target, source, args={}):

    db = Database (file=source)
    db.file = None

    return db


description = _("In-memory storage (NOT SAVED)")
