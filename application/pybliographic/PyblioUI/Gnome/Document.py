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
import gtk

from gettext import gettext as _
from Pyblio.Callback import Publisher

from PyblioUI.Gnome import Glade, Index

from PyblioUI import Document as LogicDoc



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

        # Configure the List View
        col = gtk.TreeViewColumn ('Description', gtk.CellRendererText (), markup = 1)
        self._w_index.append_column (col)

        self._selection = self._w_index.get_selection ()
        self._selection.set_mode (gtk.SELECTION_MULTIPLE)
        self._selection.connect ('changed', self._on_row_select)

        # Configure the text view
        self._text = self._w_view.get_buffer ()

        
        self._w_document.show ()
        return


    def open (self, filename, format):
        """ Open an existing database.

         - format: either the database type, or None if it should be guessed
         """

        self._l = LogicDoc.Document (filename, format)

        # update misc status info
        self._w_document.set_title (_('Pybliographic - %s') % self._l.title ())

        l = len (self._l.db)
        if l > 1:    txt = _('%d entries') % l
        elif l == 1: txt = _('1 entry')
        else:        txt = _('No entry')
        
        self._w_appbar.set_default (txt)

        self._idx = Index.DatabaseModel (self._l.db)
        self._w_index.set_model (self._idx)
        
        return

    def display (self, entry):

        if entry is None:
            self._text.set_text ('')
            return

        self._text.set_text ('%s' % `entry`)
        return


    def close (self):
        """ Close the document """

        self._on_close ()
        self._w_document.destroy ()
        return

    
    def _on_close (self, * args):
        """ Callback on the Close action or window button """
        
        height = self._w_pane.get_position ()

        self.size_save (('pane', height))
        self.emit ('close', self)
        return


    def _on_quit (self, * args):
        
        self.emit ('quit', self)
        return

    
    def _on_row_select (self, sel, * args):

        current = []
        def get (model, path, iter):
            current.append (model.get_value (iter, 0))

        sel.selected_foreach (get)

        if len (current) != 1:
            self.display (None)
            return
        
        self.display (self._l.db [current [0]])
        return
    
