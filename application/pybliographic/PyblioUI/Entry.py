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
import string

from gettext import gettext as _

from xml.sax.saxutils import escape

def summary (entry):

    """ Summarize an entry for displaying in an index """

    try: t = entry ['name']
    except KeyError: t = [_('Untitled')]

    t = string.join (map (escape, t), '; ')

    if entry.has_key ('url'):
        u = string.join (map (escape, entry ['url']), '; ')
        t = t + ' <i>%s</i>' % u
    
    return t

