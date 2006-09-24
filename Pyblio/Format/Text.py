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
Transformation of the formatted record into a textual representation.
"""

from Pyblio.Format.Generator import Generator as Base
from StringIO import StringIO

class Generator(Base):

    def __init__(self, fd):
        self.fd = fd
        return
    
    def do_string(self, t):
        self.fd.write(t)
    
    def do_a(self, t):
        self.fd.write('%s <%s>' % (''.join (map (generate, t.children)),
                                   t.attributes ['href']))

    def do_br(self, t):
        self.fd.write('\n')
        
    do_i = Base.do_t
    do_b = Base.do_t
    do_small = Base.do_t
    do_span  = Base.do_t

def generate(t):
    """ Convenience function that generates the text in a string """
    fd = StringIO()
    g = Generator(fd)
    g(t)

    return fd.getvalue()
    


