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

# Perform the first initialisation of Gnome, so that the options
# passed to the script are not passed to Gnome.

import PyblioUI
import sys

_prev = sys.argv

sys.argv = sys.argv [:1] + ['--'] + sys.argv [1:]

# import the required modules so that they get initialized
import pygtk
pygtk.require ('2.0')

import gnome
import gnome.ui

# correctly identify the program
gnome.init ('Pybliographic', PyblioUI.version)

# clean up our garbage
sys.argv = _prev

del sys

import gtk.glade

gtk.glade.bindtextdomain ("pybliographer", PyblioUI.localedir)


# Provide a simple "run" function
import gtk

def run ():
    gtk.main ()
    return

def exit ():
    gtk.main_quit ()
    return

