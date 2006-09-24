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

from Pyblio.Format.Generator import Generator as Base

import uno

_gc = uno.getConstantByName

ITALIC = (_gc("com.sun.star.awt.FontSlant.ITALIC"),
          _gc("com.sun.star.awt.FontSlant.NONE"))

BOLD = (_gc("com.sun.star.awt.FontWeight.BOLD"),
        _gc("com.sun.star.awt.FontWeight.NORMAL"))


class Generator(Base):
    """ Returns an object capable of transforming an abstract
    representation of text into actual text in OpenOffice."""
    
    def __init__(self, text, cursor):
        self.t = text
        self.c = cursor
        self.first = False
        return

    def do_string(self, t):
        self.t.insertString(self.c, t, False)
    
    def do_i(self, t):
        self.c.CharPosture = ITALIC[0]
        for s in t.children: self(s)
        self.c.CharPosture = ITALIC[1]
        
    def do_b(self, t):
        self.c.CharWeight = BOLD[0]
        for s in t.children: self(s)
        self.c.CharWeight = BOLD[1]

    def do_br(self, t):
        self.t.insertString(self.c, u'\x0a', False)

    def begin_biblio(self):
        self.first = True

    def begin_reference(self, key):
        if self.first:
            self.first = False
        else:
            self.t.insertString(self.c, u'\x0d', False)
        self.t.insertString(self.c, u'[%s]\xa0' % key, False)
