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

""" Exhaustive display of a bibliographic record """

import gtk, gobject, pango, gnome

from Pyblio import Attribute


class Entry (object):


    def __init__ (self, view):

        """ Create an object that can Control a View """

        self._view = view

        # Configure the text view
        self._text = self._view.get_buffer ()

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

        self._map = {
            Attribute.Txo: self._show_txo,
            Attribute.URL: self._show_url
            }
        
        return


    def _default (self, iter, attr, db):

        self._text.insert (iter, str (attr) + '\n')
        return


    def _show_txo (self, iter, attr, db):

        e = db.txo [attr.group] [attr.id]
        
        self._text.insert (iter, e.name + '\n')
        return


    def _show_url (self, iter, attr, db):
        
        anchor = self._text.create_child_anchor (iter)

        button = gtk.Button (label = str (attr))
        button.set_relief (gtk.RELIEF_NONE)
        
        button.show ()

        def url_open (w, url):
            gnome.url_show (url)
            return
                
        button.connect ('clicked', url_open, str (attr))
            
        self._view.add_child_at_anchor (button, anchor)
        self._text.insert (iter, '\n')
        return

    
    def display (self, entry, db):

        """ Display a record taken from a database. If the record is
        None, display nothing."""

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

            desc = db.schema [k]

            si = iter.get_offset ()
            
            self._text.insert (iter, desc.name + '\n')

            mi = iter.get_offset ()

            for f in entry [k]:
                try:
                    cmd = self._map [f.__class__]

                except KeyError:
                    cmd = self._default

                cmd (iter, f, db)
            
            si = self._text.get_iter_at_offset (si)
            mi = self._text.get_iter_at_offset (mi)
                
            self._text.apply_tag (self._tag ['body'],  si, iter)
            self._text.apply_tag (self._tag ['field'], si, mi)

            self._text.insert (iter, '\n')

        return

    
