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
# 

""" Store GUI configuration information """

import gconf

# Information is automatically stored under a given subpath
_root = '/apps/pybliographic/'

_engine = gconf.client_get_default ()

def _path (sub):

    if sub [0] == '/': sub = sub [1:]
    return _root + sub


def int_set (key, val):
    _engine.set_int (_path (key), val)

def int_get (key):
    return _engine.get_int (_path (key))