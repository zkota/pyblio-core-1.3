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

import string, os, urlparse

try: _
except NameError:
    def _(s): return s

from gnome import ui

import gtk

from Pyblio import Open, Types, Base, Fields, Config, Autoload

from Pyblio.GnomeUI import Utils



class URLFileSelection (gtk.FileSelection):
    ''' Extended file selection dialog, with an URL field and a type
    selector. '''

    defaultdir = None
    
    def __init__(self, title = _("File"),
                 url = True, modal = True, has_auto = True,
                 directory = None):
        
        gtk.FileSelection.__init__ (self)

        self.set_title (title)
        self.hide_fileop_buttons ()
        
        if directory:
            self.set_filename (directory)
            
        elif self.defaultdir:
            self.set_filename (self.defaultdir)
        
            
        self.ret = None
        self.url = None
        
        vbox = self.main_vbox
        
        # url handler
        if url:
            hbox = gtk.HBox ()
            hbox.set_spacing (5)
            hbox.set_border_width (5)
            hbox.pack_start (gtk.Label ('URL:'), expand = False, fill = False)
            self.url = gtk.Entry ()
            hbox.pack_start (self.url)
            vbox.pack_start (hbox, expand = False, fill = False)

        # type selector
        hbox = gtk.HBox ()
        hbox.set_spacing (5)
        hbox.set_border_width (5)
        hbox.pack_start (gtk.Label (_("Bibliography type:")),
                         expand = False, fill = False)

        self.menu = gtk.OptionMenu ()
        hbox.pack_start (self.menu)
        vbox.pack_start (hbox, expand = False, fill = False)

        # menu content
        menu = gtk.Menu ()
        self.menu.set_menu (menu)
        
        liste = Autoload.available ('format')
        liste.sort ()
        
        if has_auto:
            Utils.popup_add (menu, ' - Auto - ', self.menu_select, None)
            self.ftype = None
        else:
            self.ftype = liste [0]
            
        for avail in liste:
            Utils.popup_add (menu, avail, self.menu_select, avail)

        self.menu.set_history (0)

        vbox.show_all ()
        return


    def menu_select (self, widget, selection):
        self.ftype = selection
        return
        

    def run (self):
        ret = gtk.FileSelection.run (self)

        file = self.get_filename ()
        self.destroy ()

        if ret != gtk.RESPONSE_OK: return (None, None)
        

        # If we select a directory, this means the user did not select
        # a file, so we consider the URL. Otherwise, consider the user
        # input as a plain file.
        
        if not os.path.isdir (file):
            URLFileSelection.defaultdir = os.path.dirname (file) + '/'

            return (file, self.ftype)

        # If it is an URL, we still need to track the last directory selected.
        URLFileSelection.defaultdir = file + '/'
        
        if not self.url: return (None, None)
        
        ret = self.url.get_text ()
        if ret == '': return (None, None)
        
        # construct a nice URL
        if string.lower (ret [0:5]) != 'http:' and \
               string.lower (ret [0:4]) != 'ftp:':
            
            if ret [0:2] != '//':
                ret = '//' + ret
                
            file = 'http:' + ret

        else:
            file = ret
                
        return (file, self.ftype)

            
