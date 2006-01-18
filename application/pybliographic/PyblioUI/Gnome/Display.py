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

import dispatch
import gtk
import datetime

from Pyblio import Attribute

from gettext import gettext as _


class Invalid(Exception):
    """Raised when a buffer content cannot be converted into a record
    properly."""

# A few helper functions

def _fillWithText(text, buffer, i):
    """ Insert the specified text, and put marks at its both ends so
    that it can be retrieved afterward"""
    
    l = buffer.create_mark(None, i, True)

    buffer.insert(i, text)
    buffer.remove_all_tags(buffer.get_iter_at_mark(l), i)
    
    buffer.insert_with_tags_by_name(i, '\n', 'static')

    # We cannot create the mark between the two \n immediately, as
    # otherwise the mark would move along when we continue building up
    # the content of the TextBuffer. So we simply add the two \n, move
    # back, set the mark and continue.
    i.backward_char()
    r = buffer.create_mark(None, i, False)
    i.forward_char()

    return (l, r)

def _getTextInMarks(buffer, l, r):
    """ Retrieve text inserted between the two specified marks."""
    
    l = buffer.get_iter_at_mark(l)
    r = buffer.get_iter_at_mark(r)
    
    text = buffer.get_text(l, r)
    
    return text.strip()



# ==================================================

@dispatch.generic()
def newValue(attr, db):
    """ A generic method that creates a new value of a given
    attribute, so that the user can start to type ahead."""

# --------------------------------------------------

@newValue.when("attr.type is Attribute.Text")
def newValue(attr, db):
    return Attribute.Text(u'New Text')

@newValue.when("attr.type is Attribute.Person")
def newValue(attr, db):
    return Attribute.Person(last = _('Last Name'),
                            first = _('First Name'))

@newValue.when("attr.type is Attribute.Txo")
def newValue(attr, db):
    first = db.txo[attr.group].values()[0]
    return Attribute.Txo(first)

@newValue.when("attr.type is Attribute.Date")
def newValue(attr, db):
    today = datetime.date.today()
    return Attribute.Date(year = today.year)

@newValue.when("attr.type is Attribute.URL")
def newValue(attr, db):
    return Attribute.URL('http://...')

@newValue.when("attr.type is Attribute.ID")
def newValue(attr, db):
    return Attribute.ID(u'New Identifier')

# ==================================================

class Range(object):

    def __init__(self, fn, l, r):
        self.l = l
        self.r = r
        self._fn = fn
        return

    def __call__(self):
        return self._fn()


@dispatch.generic()
def fillTextBuffer(editable, attr, db, buffer, i, view):
    """ A generic method that knows how to display a field, and
    returns a method on how the record should be updated once the
    editing is done. """

# --------------------------------------------------


@fillTextBuffer.when("isinstance(attr, Attribute.Text)")
def fillTextBuffer(editable, attr, db, buffer, i, view):
    """ Display a 'simple' text attribute """

    l, r = _fillWithText(attr, buffer, i)

    def update():
        txt = _getTextInMarks(buffer, l, r)
        return Attribute.Text(txt)

    return Range(update, l, r)


@fillTextBuffer.when("isinstance(attr, Attribute.Person)")
def fillTextBuffer(editable, attr, db, buffer, i, view):

    person = ', '.join (filter (None, (attr.last, attr.first)))
    l, r = _fillWithText(person, buffer, i)

    def update():
        text = _getTextInMarks(buffer, l, r)
        segs = [x.strip() for x in text.split(',')]

        count = len(segs)
            
        if count == 1 or count > 2:
            p = Attribute.Person(last=text.strip())
        else:
            p = Attribute.Person(last=segs[0], first=segs[1])
        return p

    return Range(update, l, r)

    
@fillTextBuffer.when("isinstance(attr, Attribute.ID)")
def fillTextBuffer(editable, attr, db, buffer, i, view):
    l, r = _fillWithText(attr, buffer, i)

    def update():
        text = _getTextInMarks(buffer, l, r).strip()
        return Attribute.ID(text)

    return Range(update, l, r)


@fillTextBuffer.when("isinstance(attr, Attribute.Date)")
def fillTextBuffer(editable, attr, db, buffer, i, view):
    
    r = []
    for p in (attr.year, attr.month, attr.day):
        if p is None: break
        r.append (str (p))

    date = '/'.join (r)

    l, r = _fillWithText(date, buffer, i)

    def update():
        text = _getTextInMarks(buffer, l, r).strip()
        parts = [int(x.strip()) for x in text.split('/')]

        return Attribute.Date(*parts)
    
    return Range(update, l, r)


@fillTextBuffer.when("isinstance(attr, Attribute.Txo)")
def fillTextBuffer(editable, attr, db, buffer, i, view):

    txo = db.txo [attr.group] [attr.id]
    
    if editable:
        txt = txo.names['C']
    else:
        txt = txo.name
        
    l, r = _fillWithText(txt, buffer, i)

    def update():
        text = _getTextInMarks(buffer, l, r).strip()
        try:
            txo = db.txo[attr.group].byname(text)
        except KeyError:
            raise Invalid()
        
        return Attribute.Txo(txo)
    
    return Range(update, l, r)

    
@fillTextBuffer.when("isinstance(attr, Attribute.URL)")
def fillTextBuffer(editable, attr, db, buffer, i, view):
    if editable:
        l, r = _fillWithText(attr, buffer, i)

        def update():
            text = _getTextInMarks(buffer, l, r).strip()
            return Attribute.URL(text)

        return Range(update, l, r)
    
    else:
        url = str(attr)
        anchor = buffer.create_child_anchor (i)

        button = gtk.Button (label = attr)

        button.show ()

        def url_open (w, url):
            gnome.url_show (url)
            return

        button.connect ('clicked', url_open, url)
        view.add_child_at_anchor(button, anchor)

        buffer.insert(i, '\n')

        return Range(lambda: None, None, None)

