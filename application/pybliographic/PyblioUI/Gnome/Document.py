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

from Pyblio.Callback import Publisher

from PyblioUI.Gnome import Glade
from PyblioUI.Logic import Document as LDoc



class Document (Glade.Window, Publisher):

    """ A visual document (ie, a main window).

    This object is initially not bound to any database document.
    """
    
    
    gladeinfo = { 'file': 'main',
                  'root': '_w_document',
                  'name': 'main'
                  }

    def __init__ (self):
        self._l = None
        
        Publisher.__init__ (self)
        Glade.Window.__init__ (self)

        height = self.size_get ('pane', 50)
        self._w_pane.set_position (height)

        self._w_document.show ()
        return


    def open (self, filename, format):
        """ Open an existing database.

         - format: either the database type, or None if it should be guessed
         """
        
        self._l = LDoc.Document (filename, format)
        return


    def _on_close (self, * args):
        height = self._w_pane.get_position ()

        self.size_save (('pane', height))
        self.emit ('close', self)
        
        return
    
    
