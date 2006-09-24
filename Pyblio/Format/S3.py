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
(Stage 3 objects, ie abstract representation of the actual layout)
"""

class Tag(object):

    def __init__ (self, tag, children, attributes):

        self.tag = tag
        self.children = children
        self.attributes = attributes
        
    def __repr__(self):
        rstr = ''
        if self.attributes:
            rstr += ', attributes=%r' % self.attributes
        if self.children:
            rstr += ', children=%s' % repr(self.children)
            
        return "Tags.Tag(%r%s)" % (self.tag, rstr)

    def __call__(self, arg):
        """ When called, with either a db or a record, return a copy
        of self with mapped children. This makes the markup tags valid
        for stages 2 and 3."""

        children = [child(arg) for child in self.children]
        kwargs = {}
        for k, v in self.attributes.items():
            kwargs[k] = v(arg)
            
        return Tag(self.tag, children, kwargs)
    
        
