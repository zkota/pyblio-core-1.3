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

"""
This module is the main interface of a pybliographic database.  It
controls the interactions between the Index of records on the one
hand, and the detailed Entry display on the other hand.

"""

import os
import gtk, gobject
from gtk import gdk

from gettext import gettext as _
from xml.sax.saxutils import escape

from Pyblio.Callback import Publisher
from Pyblio import Sort, Store, Registry

from PyblioUI.Gnome import Glade, Index, Entry
from PyblioUI import Document as Base


uim_content = '''
<ui>
    <menubar name="Menubar">
        <menu action="File">
             <menuitem action="New"/>
             <menuitem action="Open"/>
             <menuitem action="Save"/>
             <menuitem action="Save_As"/>
             <separator/>
             <menuitem action="Import"/>
             <menuitem action="Export"/>
             <separator/>
             <menuitem action="Close"/>
             <menuitem action="Quit"/>
        </menu>
        <menu action="EditMenu">
             <menuitem action="Undo"/>
             <menuitem action="Redo"/>
             <separator/>
             <menuitem action="Cut"/>
             <menuitem action="Copy"/>
             <menuitem action="Paste"/>
             <menuitem action="Clear"/>
             <separator/>
             <placeholder name="Attribute"/>
             <separator/>
             <menuitem action="Add"/>
             <menuitem action="Delete"/>
             <separator/>
             <menuitem action="Find"/>
        </menu>
        <menu action="ViewMenu">
             <menuitem action="Configure"/>
        </menu>
        <menu action="PluginMenu">
             <placeholder name="Plugins"/>
        </menu>
        <menu action="HelpMenu">
             <menuitem action="Contents"/>
             <menuitem action="About"/>
        </menu>
    </menubar>

    <toolbar name="Toolbar">
        <toolitem action="Open"/>
        <toolitem action="Save"/>
        <separator/>
        <toolitem action="Add"/>
        <separator/>
        <toolitem action="Find"/>
    </toolbar>
</ui>
'''

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

        self._uim  = gtk.UIManager()
        self.actiongroup = gtk.ActionGroup ('Main')

        self.actiongroup.add_actions ([
            ('File', None,                _('_File')),
            ('EditMenu', None,            _('_Edit')),
            ('HelpMenu', None,            _('_Help')),
            ('ViewMenu', None,            _('_View')),
            ('PluginMenu', None,            _('_Plugins')),

            ('New',  gtk.STOCK_NEW, None, '', None, lambda *x: True),
            ('Open', gtk.STOCK_OPEN, None, None, None, lambda *x: True),
            ('Save', gtk.STOCK_SAVE, None, None, None, self._on_save),
            ('Save_As', gtk.STOCK_SAVE_AS, None, None, None, lambda *x: True),
            ('Close', gtk.STOCK_CLOSE, None, None, None, self._on_close),
            ('Quit', gtk.STOCK_QUIT, None, None, None, self._on_quit),

            ('Import', gtk.STOCK_UNINDENT, _('Import'), None, None, self._on_import),
            ('Export', gtk.STOCK_INDENT, _('Export'), None, None, self._on_export),

            ('Undo', gtk.STOCK_UNDO, None, '<control>z', None, self._on_undo),
            ('Redo', gtk.STOCK_REDO, None, '<shift><control>z', None, self._on_redo),
            ('Cut', gtk.STOCK_CUT, None, None,   None, lambda *x: True),
            ('Copy', gtk.STOCK_COPY, None, None,   None, lambda *x: True),
            ('Paste', gtk.STOCK_PASTE, None, None,   None, lambda *x: True),
            ('Clear', gtk.STOCK_CLEAR, None, None,   None, lambda *x: True),
            ('Add', gtk.STOCK_ADD, _('Add record'), '<shift><control>n',
             None, self._on_record_add),
            ('Delete', gtk.STOCK_DELETE, _('Delete record'), '<shift><control>d',
             None, self._on_record_delete),
            ('Find', gtk.STOCK_FIND, None, None, None, lambda *x: True),

            ('Configure', gtk.STOCK_PREFERENCES, _('Configure'), None, None, self._on_view_config),

            ('About', gtk.STOCK_ABOUT, None, None, None, lambda *x: True),
            ('Contents', gtk.STOCK_HELP, None, None, None, lambda *x: True),
            ])

        
        # Finish linking up the description of the menu and the
        # actions
        self._uim.insert_action_group (self.actiongroup, 10)
        self._uim.add_ui_from_string (uim_content)
        self._uim.ensure_update ()

        self._w_handle_menu.add(self._uim.get_widget('/Menubar'))
        self._w_handle_tool.add(self._uim.get_widget('/Toolbar'))

        self._w_document.add_accel_group (self._uim.get_accel_group ())


        # We manage UI merging by responding to merge-ui and
        # unmerge-ui request. But we need to keep track of the merged
        # UI fragments.
        self._merged = {}
        
        # We need to process some events manually (like Escape)
        self._w_document.add_events (gdk.KEY_PRESS_MASK)
        

        # Restore the previous visual state
        height = self.size_get ('vpane', 50)
        self._w_vpane.set_position (height)

        height = self.size_get ('hpane', 50)
        self._w_hpane.set_position (height)

        # Theses actions are disabled by default
        self._action_set(False, 'Delete',)
        
        # Configure the List View. We only display the column
        # containing actual data.

        # Build up the Index and Entry views. We possibly work in
        # fixed size mode, to avoid speed issues.
        fixed = True

        self._w_index.set_fixed_height_mode(fixed)
        
        col = gtk.TreeViewColumn (_('Description'), gtk.CellRendererText (),
                                  markup = Index.DatabaseModel.COL_CONTENT)

        if fixed:
            col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        
        self._w_index.append_column (col)

        s = self._w_index.get_selection ()
        s.set_mode (gtk.SELECTION_MULTIPLE)
        s.connect ('changed', self._on_entry_select)

        # Configure the text view controller
        self._text = Entry.Entry (self._w_view)
        self._text.register('changed', self._on_record_edited)
        
        self._text.register('merge-ui', self._merge_ui)
        self._text.register('unmerge-ui', self._unmerge_ui)
        
        # The current record being displayed / edited. This is the
        # state _before_ any editing occured.
        self._current_key = None
        
        # Configure the Result Set List
        self._index_col = gtk.TreeViewColumn ('', gtk.CellRendererText (), markup = 1)
        self._w_sets.append_column (self._index_col)

        s = self._w_sets.get_selection ()
        s.connect ('changed', self._on_rs_select)


        # Configure the status area
        self._statuscontext = self._w_status.get_context_id('default')


        # Some room for the plugins
        self.plugins_action = None
        self.plugins_mid = []
        
        # Showtime !
        self._actions_update()
        self._w_document.show ()
        return


    def open(self, filename, format):
        """ Open an existing database.
        
            - filename: the database filename
            
            - format: either the database type, or None if it should
              be guessed
            
         """

        self._initialize(Base.Document (filename, format))
        

    def close (self):
        """ Close the document """

        self._on_close ()
        return

    def create(self):
        """ Create a fresh database."""
        from PyblioUI.Gnome import Storage

        q = Storage.Create()
        r = q.run()

        if r is None: self.close()

        schema, store, filename = r

        try:
            db = Store.get(store).dbcreate(filename, schema)

        except Store.StoreError, msg:
            q = gtk.MessageDialog(self._w_document,
                                  flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                                  type=gtk.MESSAGE_ERROR,
                                  buttons=gtk.BUTTONS_OK)

            name = os.path.basename(filename)
            msg = str(msg)
            
            q.set_markup(_('<b>Cannot create database <i>%s</i></b>') % name)
            q.format_secondary_markup(_('The following error occured:\n<i>%s</i>') %
                                      escape(msg))

            q.run()
            q.destroy()
            
            return
        
        self._initialize(Base.Document (db=db, filename=filename))
        return
        
    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def _initialize(self, document):
        
        self._l = document

        # update misc status info
        self._w_document.set_title (_('%s - Pybliographic') % self._l.title ())

        self._l.register('record-changed', self._on_record_changed)

        # Handle the visibility of the Undo & Redo buttons
        self._l.register('can-undo', self._on_can_undo)
        self._l.register('can-redo', self._on_can_redo)

        
        # connect the database to the index view
        self._view = self._l.db.entries.view(Sort.OrderBy('publication-date'))
        
        idx = Index.DatabaseModel (self._view, self._l)
        self._w_index.set_model (idx)
        self._w_index.set_cursor((0,))

        idx.connect('row_inserted', self._on_record_added)

        # list the available result sets
        self._rs = gtk.TreeStore (gobject.TYPE_PYOBJECT,
                                  gobject.TYPE_STRING)

        self._rs.append (None, (None, _('<b>Full database</b>')))

        p = self._rs.append (None, (None, _('<i>Permanent Sets</i>')))

        for rs in self._l.db.rs.values ():
            self._rs.append (p, (rs, escape (rs.name) or _('Unnamed')))

        self._w_sets.set_model (self._rs)
        self._w_sets.expand_all ()

        self._actions_update()

        # FIXME: list the available plugins
        plugins = Registry.get(self._l.db.schema.id, 'plugins')

        if self.plugins_action:
            for mid in self.plugins_mid:
                self._uim.remove_ui (mid)
                
            self._uim.remove_action_group (self.plugins_action)

        self.plugins_mid = []
        self.plugins_action = gtk.ActionGroup ('Plugins')

        self._uim.insert_action_group (self.plugins_action, 0)

        for rip in plugins:
            try:
                M = rip()
            except ImportError, msg:
                continue
            
            # Display name in the menu
            name = rip.help()
            
            mid = self._uim.new_merge_id ()

            self.plugins_mid.append (mid)
            
            action = gtk.Action (str (mid), name, None, gtk.STOCK_EXECUTE)
            self.plugins_action.add_action (action)

            def activate(action):
                from PyblioUI.Gnome import Argv

                argv = getattr(M, 'parameters', {})
                
                if argv:
                    info = _('''\
<b>%s</b>

To apply this plugin to <i>%s</i>,
you need to supply the following parameters:''') % (
                        name, self._l.title())
                    
                    popup = Argv.Argv(_('Plugin parameters'),
                                      info, argv)

                    argv = popup.run()
                    if argv is None:
                        return
                    
                plugin = M(self._l)
                plugin.run(**argv)
                
            action.connect ('activate', activate)
        
            self._uim.add_ui (mid, '/Menubar/PluginMenu/Plugins', str (mid),
                              str (mid), gtk.UI_MANAGER_MENUITEM, False)

        return

    def _action_set(self, value, *items):
        """ Set the specified action items as sensitive or not,
        according to 'value'.
        """
        
        for item in items:
            self.actiongroup.get_action (item).set_property ('sensitive', value)
        return


    def _actions_update(self):
        if not self._l:
            self._action_set(False, 'Undo', 'Redo', 'Save', 'Add', 'Delete')
            return

        self._action_set(True, 'Add')

        self._action_set(self._l.canUndo(), 'Undo')
        self._action_set(self._l.canRedo(), 'Redo')
        self._action_set(self._l.isModified(), 'Save')

        l = len (self._l.db.entries)
        if l > 1:    txt = _('%d entries') % l
        elif l == 1: txt = _('1 entry')
        else:        txt = _('No entry')

        self._w_status.pop(self._statuscontext)
        self._w_status.push (self._statuscontext, txt)
        return


    def _can_close(self):
        """ Possibly ask the user if we really can close the window
        with unsaved changes."""

        if self._l is None: return True
        
        if self._l.isModified() or self._text.isModified():
            q = gtk.MessageDialog(self._w_document,
                                  type = gtk.MESSAGE_WARNING,
                                  buttons = gtk.BUTTONS_OK_CANCEL)

            m = u'''\
The database <i>%s</i> contains unsaved modifications.
Are you sure you want to <b>discard these modifications</b>?''' % self._l.title()

            q.set_markup(m)

            r = q.run()
            q.destroy()
            
            if r != gtk.RESPONSE_OK:
                return False

        return True
    
    def _save_settings(self):
        hp = self._w_hpane.get_position ()
        vp = self._w_vpane.get_position ()
        
        self.size_save (('hpane', hp), ('vpane', vp))
        return

    
    # --------------------------------------------------
    # Callbacks
    # --------------------------------------------------

    def _on_view_config(self, *args):
        from PyblioUI.Gnome.ViewConfig import Config

        q = Config()
        q._w_dialog.run()

    
    def _on_import(self, *args):
        if not self._l: return
        
        from PyblioUI.Gnome import Storage

        q = Storage.Import(self._l.db.schema.id)
        r = q.run()

        if r is None: return

        i, filename = r

        fd = open(filename, 'r')
        i.parse(fd, self._l)

        return
    
    def _on_export(self, *args):
        if not self._l: return
        
        from PyblioUI.Gnome import Storage

        q = Storage.Export(self._l.db.schema.id)
        r = q.run()

        if r is None: return

        x, filename = r

        fd = open(filename, 'w')
        x.write(fd, self._view, self._l.db)

        return
    
    def _on_record_add(self, *args):
        """ Called when the user wants to create a new record."""
        self._l.add(Store.Record())

    def _on_record_delete(self, *args):
        """ Called when the user wants to delete records."""
        
        sel = self._w_index.get_selection()
        model, rows = sel.get_selected_rows()

        ks = []
        for row in rows:
            i = model.get_iter(row)
            k = model.get_value(i, 0)
            ks.append(k)
            
        self._l.delete(ks)
        return
    
    def _on_record_added(self, model, path, iter):
        """ Called when a new record has been added to the DB."""
        
        # When the user adds a new record, we immediately stop editing
        # the current one, and jump to the freshly created.
        self._text.commit()

        s = self._w_index.get_selection()

        s.unselect_all()
        s.select_iter(iter)

        self._w_index.set_cursor(path)
        self._w_index.row_activated(path, self._index_col)
        return

    def _merge_ui(self, name, ui, actions):
        uid = self._uim.add_ui_from_string(ui)
        self._uim.insert_action_group(actions, 0)

        self._merged[name] = (uid, actions)
        return

    def _unmerge_ui(self, name):
        uid, actions = self._merged[name]
        del self._merged[name]

        self._uim.remove_action_group(actions)
        self._uim.remove_ui(uid)
        return
    
    def _on_key_pressed(self, app, event):

        # filter out special keys
        if event.keyval == gtk.keysyms.Escape:
            self._text.commit()
            self._w_index.grab_focus()
        return

    def _on_can_undo(self, can):
        self._action_set(can, 'Undo')

    def _on_can_redo(self, can):
        self._action_set(can, 'Redo')
            
    def _on_record_activated(self, *args):

        if self._current_key:
            self._w_view.grab_focus()
        return
    
    def _on_save(self, *args):
        self._l.db.save()
        self._l.savePoint()

        self._actions_update()
        return

    def _on_close (self, * args):
        """ Callback on the Close action or window button """

        # If we cannot close, we return True, as it stops the signal
        # from propagating.
        if not self._can_close(): return True
        
        self._save_settings()
        self._w_document.destroy ()
        
        self.emit ('close', self)
        return

    def _on_undo(self, *args):
        if self._l.canUndo():
            self._l.undoAction()
        self._actions_update()
        return

    def _on_redo(self, *args):
        if self._l.canRedo():
            self._l.redoAction()
        self._actions_update()
        return

    def _on_quit (self, * args):
        
        self.emit ('quit', self)
        return


    def _on_rs_select (self, sel, * args):
        """ Called when a result set is selected. """
        model, iter = sel.get_selected ()
        if iter is None: return

        path = model.get_path (iter)

        if len (path) == 1:
            
            if path [0] == 0:
                vw = self._l.db.entries.view (Sort.OrderBy('publication-date'))
                idx = Index.DatabaseModel (vw, self._l.db)
                
                self._w_index.set_model (idx)

            return
        
        if path [0] == 1:
            # we have selected a result set
            rs = model.get_value (iter, 0)
            vw = rs.view (Sort.OrderBy('publication-date'))
            
            idx = Index.DatabaseModel (vw, self._l.db)
            self._w_index.set_model (idx)

        return


    def _on_record_changed(self, record):
        """ Called when the underlying record is modified in the
        logical document (by anyone)."""
        if record != self._current_key: return
        
        self._text.display (self._l.db[record], self._l.db)
        return

    def _on_record_edited(self, record):
        """ Called when the editor has finished modifications."""

        self._l[record.key] = record
        self._actions_update()
        return

    def _on_entry_select (self, sel, * args):
        """ Called when the Index changed its selection."""

        current = []
        def get (model, path, iter):
            current.append (model.get_value (iter, 0))

        sel.selected_foreach (get)

        # If we did not actually change the selection, just do
        # nothing.
        if current == self._current_key: return

        # Conservatively warn about the change
        self._text.commit()
        self._action_set(len(current) > 0, 'Delete')
        
        if len (current) != 1:
            self._text.display (None, self._l.db)
            self._current_key = None
            return
        
        self._current_key = current[0] 
        self._text.display (self._l.db[current[0]], self._l.db)

        self._actions_update()
        return
    
