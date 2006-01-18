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

from Pyblio import Attribute, Store
from Pyblio.Callback import Publisher

from PyblioUI.Undo import Undoable
from PyblioUI.Gnome import Marks
from PyblioUI.Gnome.Display import Invalid

from gettext import gettext as _

import copy
import os


    
class Entry (Publisher):

    """ The Entry class can control a TextView in order to display and
    edit Records."""


    # Specific UI fragment merged when the user is in the editor window.
    uim_content = '''
<ui>
    <menubar name="Menubar">
        <menu action="EditMenu">
             <placeholder name="Attribute">
               <menuitem action="Add_Attribute"/>
               <menuitem action="Insert_Value"/>
               <menuitem action="Delete_Attribute"/>
             </placeholder>  
        </menu>
    </menubar>
</ui>
'''

    UPDATE    = 0
    NO_UNDO   = 1 << 0
    NO_RECORD = 1 << 1
    
    def __init__ (self, view):
        Publisher.__init__(self)
        
        self._view = view
        self._text = self._view.get_buffer ()

        # --------------------------------------------------
        # Specific menu overrides
        # --------------------------------------------------

        # Gtk makes it possible to merge menu fragments
        # dynamically. So, when we are in editing mode, we provide
        # extra menu features, and override some operations (like copy
        # / paste).
        
        self._actions = gtk.ActionGroup ('Entry')
        
        # We provide "local" cut/copy/paste shortcuts for the
        # TextBuffer operations
        clipboard = gtk.Clipboard()

        def cut(*args):
            self._text.cut_clipboard(clipboard, self._view.get_editable())

        def copy(*args):
            self._text.copy_clipboard(clipboard)

        def paste(*args):
            self._text.paste_clipboard(clipboard, None, self._view.get_editable())
        

        self._actions.add_actions ([
            # These are new operations available when the user is in the editor widget.
            ('Add_Attribute', gtk.STOCK_ADD, _('_Add attribute'), '<control>n',
             _('Add a new attribute'), self._on_add_attribute),
            
            ('Insert_Value', None, _('_Insert value'), '<control>i',
             _('Add a value to an attribute'), self._on_insert_value),
            
            ('Delete_Attribute', gtk.STOCK_DELETE, _('_Delete attribute'), '<control>d',
             _('Delete an attribute or value'), self._on_delete_attribute),

            # We take over these operations too...
            ('Undo', gtk.STOCK_UNDO, None, '<control>z', None, self._on_undo),
            ('Redo', gtk.STOCK_REDO, None, '<shift><control>z', None, self._on_redo),
            ('Cut', gtk.STOCK_CUT, None, None,   None, cut),
            ('Copy', gtk.STOCK_COPY, None, None,   None, copy),
            ('Paste', gtk.STOCK_PASTE, None, None,   None, paste),
            ])


        # For the moment, we have no undo / redo operation inside the editor
        for a in ('Undo', 'Redo'):
            self._actions.get_action (a).set_property ('sensitive', False)

        
        # --------------------------------------------------

        # We react on focus changes, and we intercept some special keys for shortcuts
        self._editable = self._view.is_focus()
        self._view.connect('focus-in-event', self._on_focus, True)
        self._view.connect('focus-out-event', self._on_focus, False)
        self._view.connect('key-press-event', self._on_keypress)

        self._text.connect("insert-text", self._on_insert_text)
        self._text.connect("delete-range", self._on_delete_range)

        self._text.connect_after("insert-text", self._on_text_inserted)
        self._text.connect_after("delete-range", self._on_range_deleted)

        # --------------------------------------------------
        # Configure the text view display styles
        # --------------------------------------------------

        self._text.create_tag ('static',  editable=False)
        self._text.create_tag ('colored', foreground="#888888")
        
        self._text.create_tag ('title',
                               weight=pango.WEIGHT_BOLD)

        # Display style for main attributes
        self._text.create_tag ('field',
                               pixels_above_lines=5,
                               style=pango.STYLE_OBLIQUE)

        # Display style for attribute qualifiers
        self._text.create_tag ('attribute', left_margin=10)

        self._text.create_tag ('qualified field', left_margin=20)
        self._text.create_tag ('qualified', left_margin=35)

        # --------------------------------------------------

        # The item being edited
        self._record = None
        self._db = None
        self._current = None
        
        # A flag telling if we are currently updating the content (via
        # the display() method), or letting the user edit it.
        self._flag = self.UPDATE

        # A stack of flags, for temporary state changes
        self._flagstack = []
        return

    def isModified(self):
        if not self._editable or self._record is None:
            return False

        new = self._current.record
        return not self._record.deep_equal(new)

        
    def commit(self):
        """ Check if the record has been modified, and if it has been,
        emit a notification with its new content."""

        if not self._editable or self._record is None:
            return

        # after a commit, we switch back from editable to display
        # mode.
        self._editable = False
        self.emit('unmerge-ui', 'Entry')

        new = self._current.record
        
        if not self._record.deep_equal(new):
            self.emit('changed', new)

        self.display(new, self._db)
        return

    def display(self, entry, db):
        """ Display a record taken from a database. If the record is
        None, display an empty page. If the widget has the focus, the
        record is displayed in editable form, otherwise in a more
        'static' form."""

        # While we update the display, we don't want to send
        # modification notifications to the undo stack.
        self._flag_push(self.NO_UNDO, self.NO_RECORD)

        # We need to keep track of the current record and db, as they
        # are used to display the content.
        self._record = entry
        self._db = db

        has_content = entry is not None

        # When we have no content, we don't want the user to start
        # playing in the editing area
        self._view.set_editable(has_content)
        self._view.set_cursor_visible(has_content)
        
        # We possibly need to clean up the previous text
        if self._current:
            self._current.deleteMarks(self._text)

        if not has_content:
            self._text.set_text ('')
            self._flag_pop()
            
            self._current = None
            return
            
        # This is the working copy on which we perform on-the-fly
        # modifications
        self._current = Marks.Record()
        
        # When we display a new item, we start a fresh undo stack for
        # it.
        self._undo = Undoable()

        # Handle the visibility of the Undo & Redo buttons
        self._undo.register('can-undo', self._on_can_undo)
        self._undo.register('can-redo', self._on_can_redo)

        # Display this entry in a clean textview
        self._text.delete (self._text.get_start_iter (),
                           self._text.get_end_iter ())

        # Actually insert the content of the buffer
        self._current.insert(self._text.get_start_iter(),
                             copy.deepcopy(entry), db,
                             self._text, self._view,
                             self._editable)
        self._current.markup(self._text)

        # jump to the first record
        if self._editable:
            self._move_at_iter(self._current.next().editPoint(self._text))
        
        self._flag_pop()
        return

    # --------------------------------------------------

    def _move_at_iter(self, i):
        self._text.place_cursor(i)
        self._view.scroll_mark_onscreen(self._text.get_insert())
        return

    def _get_attribute_at_cursor(self):
        """ Find out in which attribute the cursor is located. Returns
        the mark index, or None if not in range."""

        cm = self._text.get_insert()
        cm = self._text.get_iter_at_mark(cm)

        return self._get_attribute(cm)

    def _get_attribute(self, i):
        return self._current.find(i.get_offset(), self._text)


    def _action_set(self, value, *items):
        """ Set the specified action items as sensitive or not,
        according to 'value'.
        """
        
        for item in items:
            self._actions.get_action (item).set_property ('sensitive', value)
        return

    def _flag_push(self, *mask):
        """ Temporarily set the specified list of flags, memorizing
        its previous state."""
        f = self._flag
        self._flagstack.append(f)
        
        for m in mask:
            self._flag |= m
        return

    def _flag_pop(self):
        """ Restore the flag to the state it had before calling
        _flag_push()."""
        self._flag = self._flagstack.pop()
        return

    def _has_flag(self, flag):
        return self._flag & flag
    
    # --------------------------------------------------

    def _on_undo(self, *arg):
        if self._undo and self._undo.canUndo():
            self._flag_push(self.NO_UNDO)
            self._undo.undoAction()
            self._flag_pop()
        return

    def _on_redo(self, *arg):
        if self._undo and self._undo.canRedo():
            self._flag_push(self.NO_UNDO)
            self._undo.redoAction()
            self._flag_pop()
        return


    def _on_insert_text(self, buffer, i, text, length):
        """ Called when text is about to be inserted. """
        if self._has_flag(self.NO_UNDO): return

        offset = i.get_offset()
        
        def do():

            # we will re-perform an insert at the same offset as
            # previously, without triggering a call to this same
            # handler.
            place = buffer.get_iter_at_offset(offset)
            buffer.insert(place, text)
            return

        def undo():
            # We need to remove length characters starting at offset.
            to_iter = buffer.get_iter_at_offset
            buffer.delete(to_iter(offset), to_iter(offset + length))
            return
        
        self._undo.doAction(do, undo, done=True)
        return

    
    def _on_delete_range(self, buffer, start, end):
        """ Called when text is about to be deleted. """
        if self._has_flag(self.NO_UNDO): return

        text = buffer.get_text(start, end)

        start = start.get_offset()
        end = end.get_offset()
        
        def do():
            # re-suppress what was between the two offsets
            to_iter = buffer.get_iter_at_offset
            buffer.delete(to_iter(start), to_iter(end))
            return

        def undo():
            place = buffer.get_iter_at_offset(start)
            buffer.insert(place, text)
            return

        self._undo.doAction(do, undo, done=True)
        return


    def _on_text_inserted(self, buffer, i, text, length):
        if self._has_flag(self.NO_RECORD): return

        m = self._get_attribute(i)
        if m is None or m.update is None:
            return

        try:
            m.recordSet(m.update())
        except Invalid:
            pass
        return

    
    def _on_range_deleted(self, buffer, start, end):
        if self._has_flag(self.NO_RECORD): return

        m = self._get_attribute(start)
        if m is None or m.update is None:
            return

        try:
            v = m.update()
            m.recordSet(v)
        except Invalid:
            pass

        # just check that we don't have an empty range ahead. If it is
        # the case, we manually insert an editable whitespace, so that
        # the user can still type new text at that point.
        m2i = buffer.get_iter_at_mark
        
        l = m2i(m.update.l)
        r = m2i(m.update.r)

        if l.get_offset() == r.get_offset():
            buffer.insert(l, ' ')
            
            l = m2i(m.update.l)
            r = m2i(m.update.r)
            buffer.remove_all_tags(l, r)

            self._move_at_iter(l)
        return

    
    def _on_add_attribute(self, *args):
        """ Called to insert a new attribute."""
        
        m = self._get_attribute_at_cursor()
        if m is None: return

        # We fetch the attribute type outside of the undo/redo system,
        # as it should only be asked once (and not at every redo !)
        available, create = m.createAttribute()

        if not available: return
        
        # This is a transient document type selector
        q = gtk.Dialog(_('Adding an attribute'),
                       self._view.get_toplevel(),
                       flags=gtk.DIALOG_DESTROY_WITH_PARENT)

        cancel = q.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
        ok = q.add_button(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)

        # The OK button is the one by default
        ok.set_flags(gtk.CAN_DEFAULT)
        ok.grab_default()

        # ...and the Cancel button can be triggered by Escape
        accelerator = gtk.AccelGroup ()
        q.add_accel_group (accelerator)
        cancel.add_accelerator ('clicked', accelerator, gtk.keysyms.Escape, 0, 0)

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        
        bf = gtk.ListStore(str, str)
        tv = gtk.TreeView(bf)

        col = gtk.TreeViewColumn(_('Attribute to be added'),
                                 gtk.CellRendererText(), text=1)
        tv.append_column(col)

        for attr in available:
            bf.append((attr.id, attr.name))

        bf.set_sort_column_id(1, gtk.SORT_ASCENDING)

        # Wait for the user to select an attribute
        result = {'activated': None}
        
        def activate(view, path, *args):
            value = bf.get_value(bf.get_iter(path), 0)
            
            result['activated'] = [att for att in available if att.id == value][0]
            
            q.response(gtk.RESPONSE_ACCEPT)
            
        tv.connect('row-activated', activate)

        scroll.add(tv)
        scroll.set_size_request(-1, 100)

        q.vbox.pack_start(scroll, True)
        q.vbox.show_all ()
        
        accept = q.run() == gtk.RESPONSE_ACCEPT
        q.destroy ()
        
        if not accept: return

        attribute = result['activated']
        
        # Now, we have selected the attribute to add. Register the
        # actions to perform.

        def do():
            self._flag_push(self.NO_RECORD, self.NO_UNDO)
            new = create(attribute, self._text, self._view)
            val = new.insertValue(self._text, self._view)
            self._flag_pop()

            # Once we've added a new value, we can select its range so
            # that the user can edit it directly.
            m2i = self._text.get_iter_at_mark
            self._text.select_range(m2i(val.update.l),
                                    m2i(val.update.r))
            
            newpath = new.getPath()
            
            def undo():
                umark = self._current.getMarkAtPath(newpath)

                self._flag_push(self.NO_RECORD, self.NO_UNDO)
                umark.delete(self._text)
                self._flag_pop()

            return undo

        self._undo.doAction(do, None)
        return

    def _on_insert_value(self, *args):
        """ Called to insert a new value in a specific attribute."""
        
        m = self._get_attribute_at_cursor()
        if m is None: return

        path = m.getPath()

        def do():
            self._flag_push(self.NO_RECORD, self.NO_UNDO)
            mark = self._current.getMarkAtPath(path)
            new = mark.insertValue(self._text, self._view)

            self._flag_pop()

            # Once we've added a new value, we can select its range so
            # that the user can edit it directly.
            m2i = self._text.get_iter_at_mark
            self._text.select_range(m2i(new.update.l),
                                    m2i(new.update.r))
            
            newpath = new.getPath()
            
            def undo():
                umark = self._current.getMarkAtPath(newpath)
                self._flag_push(self.NO_RECORD, self.NO_UNDO)
                umark.delete(self._text)
                self._flag_pop()

            return undo

        self._undo.doAction(do, None)
        return

    def _on_delete_attribute(self, *args):
        """ Called to delete the attribute at the cursor."""
        
        m = self._get_attribute_at_cursor()
        if m is None:
            return

        path = m.getPath()

        def do():
            # Redo will need the current value of the mark
            value = m.get()
            
            # Be prudent with callbacks when we are messing with the
            # text buffer, otherwise we get unexpected side effects
            self._flag_push(self.NO_RECORD, self.NO_UNDO)
            newm = self._current.getMarkAtPath(path)
            newm.delete(self._text)
            self._flag_pop()

            def undo():
                self._flag_push(self.NO_RECORD, self.NO_UNDO)
                # We restore the previous value by asking the parent
                # mark to insert it at its former place
                parent, idx = path[:-1], path[-1]
                
                parent = self._current.getMarkAtPath(parent)
                parent.reinsert(value, newm, idx, self._db, self._text,
                                self._view, self._editable)
                
                self._flag_pop()
                return
            
            return undo
        
        self._undo.doAction(do, None)
        return

    
    def _on_keypress(self, w, e):
        """ Special keys handler. """
        
        if e.keyval == gtk.keysyms.Tab:
            m = self._get_attribute_at_cursor()

            # We loop over the list of marks
            if m is None: return True
            
            # ...and move the cursor to the next place
            self._move_at_iter(m.next().editPoint(self._text))
            return True
        
        return
        

    def _on_focus(self, w, e, focus):
        # When we receive the focus, we display the content in
        # "editable" mode, until we receive a commit() request.
        
        needsUpdate = focus and not self._editable

        if needsUpdate and self._record is not None:
            self._editable = True
            self.emit('merge-ui', 'Entry', self.uim_content, self._actions)
            self.display(self._record, self._db)
        
        return

    def _on_can_undo(self, can):
        self._action_set(can, 'Undo')

    def _on_can_redo(self, can):
        self._action_set(can, 'Redo')


    
