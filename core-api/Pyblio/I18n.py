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


''' Useful tools related to internationalization issues. '''


class Localize (object):

    """ Select a translation among a set of possible values """

    def __init__ (self):
        import locale

        lang, charset = locale.getlocale (locale.LC_MESSAGES)

        self.lang = lang or ''
        self.lang_one = self.lang.split ('_') [0]

        return

    def trn (self, table):

        if table.has_key (self.lang):
            return table [self.lang]
        
        if table.has_key (self.lang_one):
            return table [self.lang_one]

        if table.has_key (''):
            return table ['']

        return table ['C']

lz = Localize ()
