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
import gtk, gobject, pango

from gettext import gettext as _
from xml.sax.saxutils import escape

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

        height = self.size_get ('vpane', 50)
        self._w_vpane.set_position (height)

        height = self.size_get ('hpane', 50)
        self._w_hpane.set_position (height)

        # Configure the List View
        col = gtk.TreeViewColumn (_('Description'), gtk.CellRendererText (), markup = 1)
        self._w_index.append_column (col)

        s = self._w_index.get_selection ()
        s.set_mode (gtk.SELECTION_MULTIPLE)
        s.connect ('changed', self._on_entry_select)

        # Configure the text view
        self._text = self._w_view.get_buffer ()

        self._tag = {}
        
        self._tag ['title'] = \
                  self._text.create_tag ('title',
                                         weight = pango.WEIGHT_BOLD)
        self._tag ['field'] = \
                  self._text.create_tag ('field',
                                         indent = -20,
                                         style = pango.STYLE_OBLIQUE)
        self._tag ['body'] = \
                  self._text.create_tag ('body',
                                         left_margin = 20)


        # Configure the Result Set List
        col = gtk.TreeViewColumn ('', gtk.CellRendererText (), markup = 1)
        self._w_sets.append_column (col)

        s = self._w_sets.get_selection ()
        s.connect ('changed', self._on_rs_select)

        # Let's go !
        self._w_document.show ()
        return


    def open (self, filename, format):
        """ Open an existing database.
        
            - filename: the database filename
            
            - format: either the database type, or None if it should
              be guessed
            
         """

        self._l = LogicDoc.Document (filename, format)

        # update misc status info
        self._w_document.set_title (_('Pybliographic - %s') % self._l.title ())

        l = len (self._l.db.entries)
        if l > 1:    txt = _('%d entries') % l
        elif l == 1: txt = _('1 entry')
        else:        txt = _('No entry')
        
        self._w_appbar.set_default (txt)

        # connect the database to the index view
        v = self._l.db.entries.view ('name')
        
        idx = Index.DatabaseModel (v, self._l.db)
        self._w_index.set_model (idx)


        # list the available result sets
        self._rs = gtk.TreeStore (gobject.TYPE_PYOBJECT,
                                  gobject.TYPE_STRING)

        self._rs.append (None, (None, _('<b>Full database</b>')))

        p = self._rs.append (None, (None, _('<i>Permanent Sets</i>')))

        for rs in self._l.db.rs.values ():
            self._rs.append (p, (rs, escape (rs.name) or _('Unnamed')))

        self._w_sets.set_model (self._rs)
        self._w_sets.expand_all ()
        return


    def display (self, entry):
        """ Full text display of an entry """
        
        if entry is None:
            self._text.set_text ('')
            return

        # Display this entry
        self._text.delete (self._text.get_start_iter (),
                           self._text.get_end_iter ())
        
        iter = self._text.get_start_iter ()
        
        fields = entry.keys ()
        fields.sort ()
        
        
        for k in fields:

            desc = self._l.db.schema [k]

            si = iter.get_offset ()
            
            self._text.insert (iter, desc.name + '\n')

            mi = iter.get_offset ()

            for f in entry [k]:
                self._text.insert (iter, str (f) + '\n')
            
            si = self._text.get_iter_at_offset (si)
            mi = self._text.get_iter_at_offset (mi)
                
            self._text.apply_tag (self._tag ['body'],  si, iter)
            self._text.apply_tag (self._tag ['field'], si, mi)

            self._text.insert (iter, '\n')
        return


    def close (self):
        """ Close the document """

        self._on_close ()
        self._w_document.destroy ()
        return

    
    def _on_close (self, * args):
        """ Callback on the Close action or window button """
        
        hp = self._w_hpane.get_position ()
        vp = self._w_vpane.get_position ()
        
        self.size_save (('hpane', hp), ('vpane', vp))
        self.emit ('close', self)
        return


    def _on_quit (self, * args):
        
        self.emit ('quit', self)
        return


    def _on_rs_select (self, sel, * args):

        model, iter = sel.get_selected ()
        if iter is None: return

        path = model.get_path (iter)

        if len (path) == 1:
            
            if path [0] == 0:
                vw = self._l.db.entries.view ('name')
                idx = Index.DatabaseModel (vw, self._l.db)
                
                self._w_index.set_model (idx)

            return
        
        if path [0] == 1:
            # we have selected a result set
            rs = model.get_value (iter, 0)
            vw = rs.view ('name')
            
            idx = Index.DatabaseModel (vw, self._l.db)
            self._w_index.set_model (idx)

        return
    
    
    def _on_entry_select (self, sel, * args):

        current = []
        def get (model, path, iter):
            current.append (model.get_value (iter, 0))

        sel.selected_foreach (get)

        if len (current) != 1:
            self.display (None)
            return
        
        self.display (self._l.db [current [0]])
        return
    
