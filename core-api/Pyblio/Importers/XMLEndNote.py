# This file is part of pybliographer
# 
# Copyright (C) 1998-2004 Frederic GOBRY
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

import string

from xml import sax
from xml.sax.saxutils import escape, quoteattr

from Pyblio import Attribute, Store, Exceptions, Tools, XML

from gettext import gettext as _


class Importer (XML.Parser):

    def parse (self, fd, db):

        self.db = db
        
        parser  = sax.make_parser ()
        parser.setFeature (sax.handler.feature_validation, False)
        parser.setContentHandler (self)
        
        parser.parse (fd)
        return


    def startDocument (self):

        self._tdata = None
        return


    def startElement (self, name, attrs):
        self._error ('unknown tag: %s' % `name`)
            
        return

    def endElement (self, name):
        
        return
        
    def characters (self, data):

        if self._tdata is not None:
            self._tdata = self._tdata + data
            
        return


class Exporter (object):

    def _encode (self, txt):

        return escape (txt).encode ('ascii', 'xmlcharrefreplace')
        
    def author_add (self, person):

        self.fd.write ('<AUTHOR>')

        if person.first:
            txt = '%s, %s' % (person.last, person.first)
        else:
            txt = self.last
        
        self.fd.write (self._encode (txt))
        
        self.fd.write ('</AUTHOR>')
        return
    
    def write (self, fd, rs, db):

        self.fd = fd
        
        fd.write ('<XML><RECORDS>\n')

        for k, r in rs.iteritems ():

            fd.write ('<RECORD>')
            fd.write ('<REFNUM>%d</REFNUM>\n' % k)

            if r.has_key ('author'):
                fd.write ('<AUTHORS>')
                for auth in r ['author']:
                    self.author_add (auth)
                fd.write ('</AUTHORS>')
                
            fd.write ('</RECORD>\n')

        fd.write ('</RECORDS></XML>')
        return
    
    

