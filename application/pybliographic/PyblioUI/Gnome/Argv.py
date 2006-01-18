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
This module provides a tool to build up a popup for filling missing
parameters dynamically.
"""

import os
import gtk, gobject

from gettext import gettext as _

from PyblioUI.Gnome import Glade

class Argv(Glade.Window):

    """ A popup window which asks for a dynamically defined set of
    values."""
    
    gladeinfo = { 'file': 'argv',
                  'root': '_w_popup',
                  'name': 'argv'
                  }


    def __init__(self, title, info, args):
        Glade.Window.__init__(self)

        self._w_popup.set_title(title)
        self._w_label.set_markup(info)

        self._w_table.resize(len(args), 2)

        ks = args.keys()
        ks.sort()

        self.args = {}
        
        for row, k in enumerate(ks):
            self.args[k] = None
            
            tp, help = args[k]

            info = gtk.Label(help)
            self._w_table.attach(info, 0, 1, row, row+1)

            if tp is str:
                w = gtk.Entry()
                w.set_property('activates-default', True)
                
                
                def update(w):
                    self.args[k] = w.get_text()

                w.connect('changed', update)

            elif tp is bool:
                w = gtk.CheckButton()

                self.args[k] = False
                
                def update(w):
                    self.args[k] = w.get_active()

                w.connect('toggled', update)
                
            else:
                raise RuntimeError('unable to connect parameter type %s' % repr(tp))
            
            self._w_table.attach(w, 1, 2, row, row+1)
                
        self._w_popup.show_all()
        return

    def run(self):
        r = self._w_popup.run()
        self._w_popup.destroy()

        if r != gtk.RESPONSE_OK:
            return None

        return self.args
    

