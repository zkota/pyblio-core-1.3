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
# 
"""
A simple API to cite references in OpenOffice.org

Based on code from Bibus <http://bibus-biblio.sourceforge.net/>.
"""

import uno

DIRECT_VALUE    = uno.getConstantByName("com.sun.star.beans.PropertyState.DIRECT_VALUE")
PARAGRAPH_BREAK = uno.getConstantByName("com.sun.star.text.ControlCharacter.PARAGRAPH_BREAK")

PropertyValue          = uno.getClass("com.sun.star.beans.PropertyValue")
NoSuchElementException = uno.getClass("com.sun.star.container.NoSuchElementException")

_OO_BIB_FIELDS = ('Identifier', 'BibiliographicType', 'Address', 'Annote', 'Author',
                  'Booktitle', 'Chapter', 'Edition', 'Editor', 'Howpublished', 'Institution',
                  'Journal', 'Month', 'Note', 'Number', 'Organizations', 'Pages', 'Publisher',
                  'School', 'Series', 'Title', 'Report_Type', 'Volume', 'Year', 'URL', 'Custom1',
                  'Custom2', 'Custom3', 'Custom4', 'Custom5', 'ISBN')

OO_BIBLIOGRAPHIC_FIELDS = {}
for k, v in enumerate(_OO_BIB_FIELDS):
    OO_BIBLIOGRAPHIC_FIELDS[v] = k
        
class OOo(object):
    MASTER = 'com.sun.star.text.FieldMaster.Bibliography'
    
    def __init__(self):
        localContext = uno.getComponentContext()
        resolver = localContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", localContext )

        ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
        
        self.smgr = ctx.ServiceManager
        self.desktop = self.smgr.createInstanceWithContext("com.sun.star.frame.Desktop",ctx)

        self.model = self.desktop.getCurrentComponent()
        if not (self.model and self.model.getImplementationName() == 'SwXTextDocument'):
            raise RuntimeError("not in a text document")
        
        self.controller = self.model.getCurrentController()
        self.cursor = self.controller.getViewCursor()
        self.text = self.model.Text

        try:
            self.tfm = self.model.getTextFieldMasters().getByName(self.MASTER)
        except NoSuchElementException:
            self.tfm = self.model.createInstance(self.MASTER)

        return

    
    def _makeRef(self, visible_ref, key):
        """ Create a reference ready to be inserted in the document. """
        
        oref = self.model.createInstance("com.sun.star.text.TextField.Bibliography")
        oref.Fields = (PropertyValue('Identifier', 0, visible_ref, DIRECT_VALUE),
                       PropertyValue('Custom1', 0, 'X-PYBLIO<%s>' % key, DIRECT_VALUE),)

        return oref

    def insert(self, ref, key):
        """ Insert a reference in the document, at the cursor. """
        
        oref = self._makeRef(ref, key)
        c = self.cursor.Text.createTextCursorByRange(self.cursor)
        c.Text.insertTextContent(c, oref, True)
        self.cursor.setPropertyToDefault('CharStyleName')
        return
    
    def fetch(self):
        """ Fetch all the references in the document, in order of appearance """

        refs = list(self.tfm.getPropertyValue('DependentTextFields'))

        # We need to reorder the fields by checking their relative
        # position.
        def cmp(a, b):
            return self.text.compareRegionStarts(b.Anchor.Start,
                                                 a.Anchor.Start)
        refs.sort(cmp)

        return [[x.Value for x in r.Fields] for r in refs]
