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
# 

''' Utility functions for Gnome Interface management. '''

import os

import gtk
import gtk.glade

from PyblioUI.Gnome import Config


class Window (object):

    ''' A Helper class that builds a graphical interface provided by a
    Glade XML file. This class binds the methods with
    signal_autoconnect, and imports wigets whose name starts with _w_
    as instance attributes. Therefore, after init, the instance can refer to:

        self._w_main

    if the glade file defined a _w_main widget.

    This class must be derived and the gladeinfo class variable must
    be given some sensible value:

        file: name of the glade file (with no directory info)
        root: name of the root widget
        name: name under which GUI data will be stored for this window
        
    '''


    # This is a class variable that contains configuration parameters

    gladeinfo = { 'file': None,
                  'root': None,
                  'name': None
                  }

    def __init__ (self, parent = None):
        
        gp = os.path.join (os.path.dirname (__file__), 'Glade',
                           self.gladeinfo ['file'] + '.glade')
        
        self.xml = gtk.glade.XML (gp, domain = "pybliographer")
        self.xml.signal_autoconnect (self)

        for w in self.xml.get_widget_prefix ('_w_'):
            setattr (self, w.name, w)

        # Set the parent window. The root widget is not necessarily
        # exported as an instance attribute.
        root = self.xml.get_widget (self.gladeinfo ['root'])
        cfg  = self.gladeinfo ['name']
        
        w = Config.int_get (cfg + '/width')  or -1
        h = Config.int_get (cfg + '/height') or -1

        if w != -1 and h != -1:
            root.set_default_size (w, h)
            root.resize (w, h)
        
        if parent:
            root.set_transient_for (parent)
            
        return

    def size_save (self, * args):

        """ Save the window size, and optional additional
        parameters. This parameters must be passed as extra 2-uples
        like:

           widget.size_save (('name', size), ('other', size))
           
        """
        
        root = self.xml.get_widget (self.gladeinfo ['root'])
        cfg  = self.gladeinfo ['name']

        w, h = root.get_size ()

        Config.int_set (cfg + '/width',  w)
        Config.int_set (cfg + '/height', h)

        for k, v in args:
            Config.int_set (cfg + '/%s' % k, v)
            
        return

    def size_get (self, arg, default = -1):

        """ Return the value of an extra parameter, or the supplied
        default value if the parameter has not been saved yet. """
        
        
        cfg = self.gladeinfo ['name']

        return Config.int_get (cfg + '/' + arg) or default
    
