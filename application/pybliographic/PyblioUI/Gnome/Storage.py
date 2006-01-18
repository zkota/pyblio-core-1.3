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

import os
import gtk, gobject
from gettext import gettext as _

from Pyblio import Store, Registry

from PyblioUI.Gnome import Glade, Argv


class _Base(Glade.Window):
    gladeinfo = { 'file': 'create',
                  'root': '_w_create',
                  'name': 'create'
                  }

    _list_values = None
    _combo_values = None
    
    def __init__ (self):
        Glade.Window.__init__ (self)
    
        # Initialize the ListView
        if self._list_values:
            self._list_store = gtk.ListStore(gobject.TYPE_PYOBJECT, str)
            self._w_list.set_model(self._list_store)
            self._w_list.set_size_request(-1, 100)

            col = gtk.TreeViewColumn(self._list_title,
                                     gtk.CellRendererText(), text=1)
            self._w_list.append_column(col)


            for v in self._list_values():
                self._list_store.append(v)

            sel = self._w_list.get_selection()
            sel.select_path((0,))

        else:
            self._w_list.hide()

        # Initialize the combo's list
        if self._combo_values:
            self._combo_store = gtk.ListStore(str, str)
            self._w_combo.set_model(self._combo_store)

            cell = gtk.CellRendererText()

            self._w_combo.pack_start(cell, True)
            self._w_combo.add_attribute(cell, 'text', 1)

            for v in self._combo_values():
                self._combo_store.append(v)

            self._w_combo.set_active(0)

        else:
            self._w_combo_row.hide()
        return

    def run(self):

        while 1:
            r = self._w_create.run()

            if r != gtk.RESPONSE_OK:
                self._w_create.destroy()
                return None

            listv = None
            combov = None

            if self._list_values:
                # Fetch the selected schema
                sel = self._w_list.get_selection()

                buffer, i = sel.get_selected()
                if i is None: continue

                listv = buffer.get(i, 0)[0]

            if self._combo_values:
                # Fetch the selected store
                i = self._w_combo.get_active_iter()
                if i is None: continue

                combov = self._combo_store.get(i, 0)[0]

            filename = self._w_chooser.get_filename()
            if filename is None: continue

            break
        
        self._w_create.destroy()
        
        return (listv, combov, filename)


class Import(_Base):
    gladeinfo = { 'file': 'create',
                  'root': '_w_create',
                  'name': 'create'
                  }

    _list_title = _('Available Importers')

    def __init__(self, schema):
        self.schema = schema

        _Base.__init__(self)
        self._w_chooser.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        return
    
    def _list_values(self):
        # Initialize the list of known importers
        r = []
        for rip in Registry.get(self.schema, 'importers'):
            try:
                m = rip()
            except ImportError, msg:
                continue

            r.append((rip, rip.help()))
        return r

        
    def run(self):

        r = _Base.run(self)
        if r is None: return r

        rip, __, f = r

        m = rip()
        
        if not hasattr(m, 'parameters') or not m.parameters:
            return m(), f

        info = _('''\
<b>%s</b>

You need to provide the following parameters
to import the data in your current database:''') % rip.help()

        popup = Argv.Argv(_('Importer parameters'),
                          info, m.parameters)

        argv = popup.run()
        if argv is None:
            return None

        return m(**argv), f
    

class Export(_Base):
    _list_title = _('Available Exporters')

    def __init__(self, schema):
        self.schema = schema

        _Base.__init__(self)
        return
    
    def _list_values(self):
        # Initialize the list of known exporters
        r = []
        for rip in Registry.get(self.schema, 'exporters'):
            try:
                m = rip()
            except ImportError, msg:
                continue

            doc = help(m, rip.name)
                
            r.append((m, doc))
        return r
    

    
    def run(self):

        r = _Base.run(self)
        if r is None: return r

        rip, __, f = r

        m = rip()

        if not hasattr(m, 'parameters') or not m.parameters:
            return m(), f

        info = _('''\
<b>%s</b>

You need to provide the following parameters
to export the data from your current database:''') % rip.help()
        
        popup = Argv.Argv(_('Exporter parameters'),
                          info, m.parameters)

        argv = popup.run()
        if argv is None:
            return None

        return m(**argv), f
    

class Create(_Base):

    _list_title = _('Available Schemas')
    
    def _list_values(self):
        # Initialize the list of known schemas
        r = []
        for key in Registry.schemas():
            schema = Registry.getSchema(key)
            
            r.append((schema, schema.name))
        return r
    
    def _combo_values(self):
        r = []
        
        for name in Store.modules():
            try:
                m = Store.get(name)
            except ImportError:
                continue

            r.append((name, m.description))
        return r
    
    def run(self):

        r = _Base.run(self)
        if r is None: return r

        # We need to possibly add a file extension to the filename.
        l, c, f = r
        
        base, ext = os.path.splitext(f)
        if ext != '.bip': f += '.bip'
            
        return (l, c, f)

        
        
