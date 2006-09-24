# -*- coding: utf-8 -*-
# This file is part of pybliographer
# 
# Copyright (C) 1998-2006 Frederic GOBRY
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

"""
This module contains bindings for specific Word Processors. Depending
on the capabilities of the wp, some or all of the functions described
in IWordProcessor are implemented.
"""

class CommunicationError(Exception):
    """ Raised when an error occurs on the link between pyblio and the
    word processor. After such an error, the IWordProcessor is
    disconnected."""
    pass

class OperationError(Exception):
    """ Raised when the requested operation on the IWordProcessor
    cannot be completed. The IWordProcessor is _not_ disconnected
    after such an error."""
    pass

class IWordProcessor:
    """ Interface a WordProcessor object should provide """

    def connect(self):
        """ Establish a connection to the word processor.

        This binds this object to a specific document in the word
        processor. No other operation except is_connected can take
        place before connection."""
        pass

    def disconnect(self):
        """ Disconnect from the word processor. """
        pass

    def is_connected(self):
        """ Check if the connection is still up. """
        pass
    
    def cite(self, keys):
        """ Insert a list of references at the current position of the
        document.

        keys is a list of tuples (uid, key) where uid is the
        identifier of the record in the database, and key is the key
        to be shown to the user.
        """
        pass

    def fetch(self):
        """ Retrieve the list of (uid, key) tuples previously inserted
        in the current document with self.cite().

        The tuples are ordered according to the position of the
        references in the text.

        If the WP does not support this operation, returns None (not
        []).
        """
        pass
    
    def update_keys(self, keymap):
        """ Update the keys shown to the user. keymap is a dictionary
        that provides, for each uid having changed, the new key to be
        displayed."""
        pass

    def update_biblio(self):
        """ Return a generate object ready to accept instructions to
        rebuild the current bibliography list. An example of such a
        generator is provided by
        L{Pyblio.Format.OpenOffice.Generator}."""
        pass

    
    
