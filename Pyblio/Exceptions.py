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
# 

''' This module defines some common exceptions '''

class ParserError(Exception):
    def __init__(self, msg, line=None):
        Exception.__init__(self, line, msg)

class SchemaError(Exception):
    pass

class ConstraintError(Exception):
    pass

class InvalidQuery(Exception):
    """ Raised if an ill-typed query is attempted """
    pass

class QueryError(Exception):
    """ Raised when an external query failed."""
    pass

class AdaptError(Exception):
    """ Raised when an external query failed."""
    pass

