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
# 

"""
A simple API to cite references in OpenOffice.org

Based on code from Bibus <http://bibus-biblio.sourceforge.net/>.
"""

import uno
from gettext import gettext as _

from Pyblio.Cite.WP import CommunicationError, OperationError
from Pyblio.Store import Key

DIRECT_VALUE    = uno.getConstantByName("com.sun.star.beans.PropertyState.DIRECT_VALUE")
PARAGRAPH_BREAK = uno.getConstantByName("com.sun.star.text.ControlCharacter.PARAGRAPH_BREAK")

PropertyValue          = uno.getClass("com.sun.star.beans.PropertyValue")
NoSuchElementException = uno.getClass("com.sun.star.container.NoSuchElementException")
NoConnectException     = uno.getClass("com.sun.star.connection.NoConnectException")

ITALIC = (uno.getConstantByName("com.sun.star.awt.FontSlant.ITALIC"),
          uno.getConstantByName("com.sun.star.awt.FontSlant.NONE"))

OO_BIBLIOGRAPHIC_FIELDS = {}
for f in ('Custom1', 'Custom2', 'Identifier'):
    OO_BIBLIOGRAPHIC_FIELDS[f] = \
        uno.getConstantByName("com.sun.star.text.BibliographyDataField." + f.upper())

from Pyblio.Format.OpenOffice import Generator, ITALIC

import re

_x_pyblio_re = re.compile(r'X-PYBLIO<(\d+)>')
_x_pyblio_extra_re = re.compile(r'X-PYBLIO-EXTRA:(.*)')

class OOo(object):
    MASTER = 'com.sun.star.text.FieldMaster.Bibliography'

    FRAME = u'Bibliography (Pybliographer)'
    
    def __init__(self, connection=('pipe', 'OOo_pipe')):
        self.remote = connection
        self.smgr = None
        return

    def is_connected(self):
        return self.smgr is not None

    def disconnect(self):
        self.smgr = None
        self.desktop = None
        self.model = None
        self.controller = None
        self.cursor = None
        self.text = None
        self.tfm = None
        self.frame = None
        
    def connect(self):
        if self.is_connected():
            return
        
        localContext = uno.getComponentContext()
        resolver = localContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", localContext )

        if self.remote[0] == 'pipe':
            cnx_parameter = 'pipe,name=%s' % self.remote[1]
        elif self.remote[0] == 'socket':
            cnx_parameter = 'socket,host=%s,port=%d' % self.remote[1:]
        else:
            cnx_parameter = ''
        try:
            ctx = resolver.resolve("uno:%s;urp;StarOffice.ComponentContext" % (
                cnx_parameter))
        except NoConnectException, msg:
            raise CommunicationError(_("Unable to contact OpenOffice.org: %s" % msg))
        
        self.smgr = ctx.ServiceManager
        self.desktop = self.smgr.createInstanceWithContext("com.sun.star.frame.Desktop",ctx)

        self.model = self.desktop.getCurrentComponent()
        if not (self.model and self.model.getImplementationName() == 'SwXTextDocument'):
            raise OperationError(_("You are not in a text document"))
        
        self.controller = self.model.getCurrentController()
        self.cursor = self.controller.getViewCursor()
        self.text = self.model.Text

        try:
            self.tfm = self.model.getTextFieldMasters().getByName(self.MASTER)
        except NoSuchElementException:
            self.tfm = self.model.createInstance(self.MASTER)

        # Try to get an existing frame of content
        try:
            self.frame = self.model.getTextSections().getByName(self.FRAME)
        except NoSuchElementException:
            self.frame = None
        return

    def cite(self, keys, db):
        """ Insert a list of references in the document, at the
        cursor location. Each reference is a tuple
          (visible_key, internal_id, extra_data)
        """
        for ref, key, extra in keys:
            oref = self._makeRef(ref, key, extra)
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
        return [r for r in [self._parseRef(ref) for ref in refs] if r]

    def update_keys(self, keymap):
        # Update the existing keys according to the new values. This
        # must be done in two passes, as OpenOffice will reject any
        # Identifier that is already used. So let's first rename them all
        # to something unique first, and set the final value in a second
        # phase.
        refmap = {}
        refs = list(self.tfm.getPropertyValue('DependentTextFields'))
        for ref in refs:
            fields = self._parseRef(ref)
            if not fields:
                continue
            uid, readable, extra = fields
            refmap[uid] = (ref, fields)

        for uid, name in keymap.iteritems():
            ref, (_, _, extra) = refmap[uid]
            self._makeRef(uid, name, extra, oref=ref)

        return self.fetch()

    def update_biblio(self):
        if not self.frame:
            self._createFrame()

        f = self.frame
        t = self.text
        c = self.text.createTextCursorByRange(self.frame.Anchor.Start)

        f.Anchor.setString('')
        return Generator(t, c)
    
    def _createFrame(self):
        self.frame = self.model.createInstance("com.sun.star.text.TextSection")
        self.frame.setName(self.FRAME)
        
        self.text.insertString(self.cursor, '\x0a', False)
        c = self.cursor.Text.createTextCursorByRange(self.cursor)
        self.text.insertString(c, '\x0a', False)
        c.goLeft(1, False)
        self.text.insertTextContent(c, self.frame, False)

        c = self.text.createTextCursorByRange(self.frame.Anchor.Start)
        c.CharPosture = ITALIC[0]
        self.text.insertString(c, _('Bibliography will appear here...'), False)
        c.CharPosture = ITALIC[1]
        
        return self.frame

    def _makeRef(self, ref, visible_key, extra, oref=None):
        """ Create a reference ready to be inserted in the document. """

        if extra is not None:
            extra = 'X-PYBLIO-EXTRA:%s' % extra

        if oref is None:
            oref = self.model.createInstance("com.sun.star.text.TextField.Bibliography")

        oref.Fields = (PropertyValue('Identifier', 0, visible_key, DIRECT_VALUE),
                       PropertyValue('Custom1', 0, 'X-PYBLIO<%s>' % ref, DIRECT_VALUE),
                       PropertyValue('Custom2', 0, extra, DIRECT_VALUE),)

        return oref

    def _parseRef(self, r):
        ref, key, extra = (
            r.Fields[OO_BIBLIOGRAPHIC_FIELDS['Custom1']].Value,
            r.Fields[OO_BIBLIOGRAPHIC_FIELDS['Identifier']].Value,
            r.Fields[OO_BIBLIOGRAPHIC_FIELDS['Custom2']].Value)

        if extra:
            m = _x_pyblio_extra_re.match(extra)
            if m:
                extra = m.group(1)
            else:
                extra = None
        m = _x_pyblio_re.match(ref)
        if m:
            return (Key(m.group(1)), key, extra)
        return None
