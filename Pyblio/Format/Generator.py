# -*- coding: utf-8 -*-
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

"""
A base generator, specialized for every output style.
"""

class Generator(object):

    def __call__(self, t):
        if isinstance(t, (str, unicode)):
            self.do_string(t)
        else:
            getattr(self, 'do_' + t.tag)(t)
        return

    def do_t(self, t):
        for s in t.children:
            self(s)
        return

    def begin_biblio(self):
        pass
    def end_biblio(self):
        pass

    def begin_reference(self, key):
        pass
    def end_reference(self, key):
        pass
