# -*- coding: utf-8 -*-
#
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

''' This module defines a Document class '''

from gnome import ui
import gtk
import gtk.glade

from Pyblio.GnomeUI import Index, Entry, Utils, FileSelector, Editor
from Pyblio.GnomeUI import Search, Format
from Pyblio.GnomeUI.Sort import SortDialog
from Pyblio.GnomeUI.Medline import MedlineUI

from Pyblio import Connector, Open, Exceptions, Selection, Sort, Base, Config
from Pyblio import version, Fields, Types, Query

import Pyblio.Style.Utils

import gettext, os, string, copy, types, sys, traceback, stat

_ = gettext.gettext

import cPickle

pickle = cPickle
del cPickle

printable = string.lowercase + string.uppercase + string.digits

class Document (Connector.Publisher):
    
    def __init__ (self, database):


        gp = os.path.join (version.prefix, 'glade', 'pyblio.glade')
        
        self.xml = gtk.glade.XML (gp, 'main', domain = 'pybliographer')
        self.xml.signal_autoconnect (self)

        self.w = self.xml.get_widget ('main')
        self.paned = self.xml.get_widget ('main_pane')

        # The Index list
        self.index = Index.Index ()
        self.paned.add1 (self.index.w)
        
        self.index.Subscribe ('new-entry',      self.add_entry)
        self.index.Subscribe ('edit-entry',     self.edit_entry)
        self.index.Subscribe ('delete-entry',   self.delete_entry)
        self.index.Subscribe ('select-entry',   self.update_display)
        self.index.Subscribe ('select-entries', self.freeze_display)
        self.index.Subscribe ('drag-received',  self.drag_received)
        self.index.Subscribe ('drag-moved',     self.drag_moved)
        self.index.Subscribe ('click-on-field', self.sort_by_field)

        self.paned.show_all ()

        # The text area
        self.display = Entry.Entry ()
        self.paned.add2 (self.display.w)

        # Status bar
        self.statusbar = self.xml.get_widget ('statusbar')
        
        # set window size
        ui_width  = Utils.config.get_int ('/apps/pybliographic/ui/width') or -1
        ui_height = Utils.config.get_int ('/apps/pybliographic/ui/height') or -1

        if ui_width != -1 and ui_height != -1:
            self.w.set_default_size (ui_width, ui_height)

        # set paned size
        paned_height = Utils.config.get_int ('/apps/pybliographic/ui/paned') or -1
        self.paned.set_position (paned_height)
        
        self.w.show_all ()
        
        # application variables
        self.data      = database
        self.selection = Selection.Selection ()
        self.search_dg = None
        self.sort_dg   = None
        self.lyx       = None
        self.changed   = 0
        self.directory = None

        self.incremental_start  = None
        self.incremental_search = ''
        
        self.modification_date = None

        # set the default sort method
        default = Utils.config.get_string ('/apps/pybliographic/sort/default')
        if default is not None: default = pickle.loads (default)

        self.sort_view (default)
        return


    def set_preferences (self, * arg):
        from Pyblio.GnomeUI import Config
        Config.run(self.w)
        return

    def set_fields (self, * arg):
        from Pyblio.GnomeUI import Fields
        Fields.run (self.w)
        return
    
    # remove !
    def set_entries (self, * arg):
        from Pyblio.GnomeUI import Fields
        Fields.run (self.w)
        return
    

    def update_history (self, history):
        ''' fill the " Previous Documents " menu with the specified list of documents '''

        sub = self.xml.get_widget ('previous_documents')
        factory = gtk.ItemFactory (gtk.Menu, '<main>', None)
        
        menuinfo = []
        
        for item in history:
            # Display name in the menu
            filename = string.replace (item [0], '/', '\/')
            
            menuinfo.append (('/' + filename, None, self._history_open_cb,
                              0, None))

        factory.create_items (menuinfo)

        # Bind the actual file info to each menu entry
        i = 0
        for item in menuinfo:
            w = factory.get_widget (item [0])
            w.set_data ('file', history [i])
            i = i + 1
            
        sub.set_submenu (factory.get_widget ('<main>'))
        return


    def _history_open_cb (self, id, w):

        file, type = w.get_data ('file')
        
        if not self.confirm (): return

        self.open_document (file, type)
        return
    
    
    def redisplay_index (self, changed = -1):
        ''' redisplays the index. If changed is specified, set the
        self.changed status to the given value '''
        
        if changed != -1:
            self.changed = changed

        self.index.display (self.selection.iterator (self.data.iterator ()))
        
        self.update_status ()
        return


    def format_query (self, style, format, output):
        try:
            file = open (output, 'w')
        except IOError, err:
            self.w.error (_("can't open file `%s' for writing:\n%s")
                          % (output, str (err)))
            return
        
        entries = map (lambda x: x.key, self.index.selection ())
        
        if not entries:
            iter    = self.selection.iterator (self.data.iterator ())
            entries = []
            
            e = iter.first ()
            while e:
                entries.append (e.key)
                e = iter.next ()

        url = Fields.URL (style)

        try:
            Pyblio.Style.Utils.generate (url, format, self.data, entries, file)
        except RuntimeError, err:
            print err
            self.w.error (_("Error while parsing `%s':\n%s") % (style, err))
        return


    def format_entries (self, * arg):
        format_dg = Format.FormatDialog (self.w)
        format_dg.Subscribe ('format-query', self.format_query)
        return

    
    def update_status (self, status = -1):
        ''' redisplay status bar according to the current status '''

        if status != -1: self.changed = status
        
        if self.data.key is None:
            text = _("New database")
        else:
            text = str (self.data.key)

        li = len (self.index)
        ld = len (self.data)
        
        if li == ld:
            if   ld == 0: num = _("[no entry]")
            elif ld == 1: num = _("[1 entry]")
            else:         num = _("[%d entries]")    %  ld
        else:
            if   ld == 0: num = _("[no entry]")
            elif ld == 1: num = _("[%d/1 entry]")    % li
            else:         num = _("[%d/%d entries]") % (li, ld)

        text = text + ' ' + num
        
        if self.changed:
            text = text + ' ' + _("[modified]")

        self.statusbar.set_default (text)
        return

    
    def confirm (self):
        ''' eventually ask for modification cancellation '''
        
        if self.changed:
            return Utils.Callback (_("The database has been modified.\nDiscard changes ?"),
                                   self.w).answer ()
        
        return 1

        
    def new_document (self, * arg):
        ''' callback corresponding to the "New Document" button '''
        
        self.issue ('new-document', self)
        return


    def query_database (self, * arg):
        ''' callback corresponding to the "Medline Query..." button '''

        if not self.confirm (): return

        data = MedlineUI (self.w).run ()
        if data is None: return
        
        url = apply (Query.medline_query, data)

        self.open_document (url, 'medline', no_name = True)
        return


    def merge_database (self, * arg):
        ''' add all the entries of another database to the current one '''
        # get a new file name
        (url, how) = FileSelector.URLFileSelection (_("Merge file"),
                                                    url = True, has_auto = True).run ()

        if url is None: return

        try:
            iterator = Open.bibiter (url, how = how)
            
        except (Exceptions.ParserError,
                Exceptions.FormatError,
                Exceptions.FileError), error:
            
            Utils.error_dialog (_("Open error"), error,
                                parent = self.w)
            return

        # loop over the entries
        errors = []
        try:
            entry = iterator.first ()
        except Exceptions.ParserError, msg:
            errors = errors + msg.errors
        
        while entry:
            self.data.add (entry)
            while 1:
                try:
                    entry = iterator.next ()
                    break
                except Exceptions.ParserError, msg:
                    errors = errors + list (msg.errors)
                    continue

        self.redisplay_index (1)

        if errors:
            Utils.error_dialog (_("Merge status"), string.join (errors, '\n'),
                                parent = self.w)
        return

        
    def ui_open_document (self, * arg):
        ''' callback corresponding to "Open" '''
        
        if not self.confirm (): return

        # get a new file name
        (url, how) = FileSelector.URLFileSelection (_("Open file")).run ()

        if url is None: return
        self.open_document (url, how)
        return

    
    def open_document (self, url, how = None, no_name = False):

        Utils.set_cursor (self.w, 'clock')
        
        try:
            data = Open.bibopen (url, how = how)
            
        except (Exceptions.ParserError,
                Exceptions.FormatError,
                Exceptions.FileError), error:
            
            Utils.set_cursor (self.w, 'normal')
            Utils.error_dialog (_("Open error"), error,
                                parent = self.w)
            return

        Utils.set_cursor (self.w, 'normal')

        if no_name: data.key = None
        
        self.data    = data
        self.redisplay_index (0)
        
        # eventually warn interested objects
        self.issue ('open-document', self)
        return

    
    def save_document (self, * arg):
        if self.data.key is None:
            self.save_document_as ()
            return

        file = self.data.key.url [2]
        
        if self.modification_date:
            mod_date = os.stat (file) [stat.ST_MTIME]
            
            if mod_date > self.modification_date:
                if not Utils.Callback (_("The database has been externally modified.\nOverwrite changes ?"),
                                       self.w).answer ():
                    return
        
        Utils.set_cursor (self.w, 'clock')
        try:
            try:
                self.data.update (self.selection.sort)
            except (OSError, IOError), error:
                Utils.set_cursor (self.w, 'normal')
                self.w.error (_("Unable to save `%s':\n%s") % (str (self.data.key),
                                                               str (error)))
                return
        except:
            etype, value, tb = sys.exc_info ()
            traceback.print_exception (etype, value, tb)
            
            Utils.set_cursor (self.w, 'normal')
            self.w.error (_("An internal error occured during saving\nTry to Save As..."))
            return

        Utils.set_cursor (self.w, 'normal')

        # get the current modification date
        self.modification_date = os.stat (file) [stat.ST_MTIME]
        
        self.update_status (0)
        return
    
    
    def save_document_as (self, * arg):
        # get a new file name
        (url, how) = FileSelector.URLFileSelection (_("Save As..."),
                                                    url = False, has_auto = False).run ()
        
        if url is None: return

        if os.path.exists (url):
            if not Utils.Callback (_("The file `%s' already exists.\nOverwrite it ?")
                                   % url, parent = self.w).answer ():
                return

        try:
            file = open (url, 'w')
        except IOError, error:
            self.w.error (_("During opening:\n%s") % error [1])
            return

        Utils.set_cursor (self.w, 'clock')

        iterator = Selection.Selection (sort = self.selection.sort)
        Open.bibwrite (iterator.iterator (self.data.iterator ()),
                       out = file, how = how)
        file.close ()
        
        try:
            self.data = Open.bibopen (url, how = how)
                
        except (Exceptions.ParserError,
                Exceptions.FormatError,
                Exceptions.FileError), error:
                    
            Utils.set_cursor (self.w, 'normal')
            Utils.error_dialog (_("Reopen error"), error,
                                parent = self.w)
            return
            
        self.redisplay_index ()
        self.issue ('open-document', self)
            
        Utils.set_cursor (self.w, 'normal')

        self.update_status (0)
        return

    
    def close_document (self, * arg):
        self.issue ('close-document', self)
        return 1


    def close_document_request (self):
        return self.confirm ()

    
    def exit_application (self, * arg):
        self.issue ('exit-application', self)
        return


    def drag_moved (self, entries):
        if not entries: return
        
        for e in entries:
            del self.data [e.key]

        self.redisplay_index (1)
        return

    
    def drag_received (self, entries):
        for entry in entries:
            
            if self.data.would_have_key (entry.key):
                if not Utils.Callback (_("An entry called `%s' already exists.\nRename and add it anyway ?")
                                       % entry.key.key, parent = self.w).answer ():
                    continue
                
            self.changed = 1
            self.data.add (entry)

        self.redisplay_index ()
        self.index.set_scroll (entries [-1])
        return

                
    def cut_entry (self, * arg):
        entries = self.index.selection ()
        if not entries: return
        
        self.index.selection_copy (entries)
        for entry in entries:
            del self.data [entry.key]
            
        self.redisplay_index (1)
        pass

    
    def copy_entry (self, * arg):
        self.index.selection_copy (self.index.selection ())
        return

    
    def paste_entry (self, * arg):
        self.index.selection_paste ()
        return

    
    def clear_entries (self, * arg):
        if len (self.data) == 0: return

        if not Utils.Callback (_("Really remove all the entries ?"),
                               parent = self.w).answer ():
            return

        keys = self.data.keys ()
        for key in keys:
            del self.data [key]

        self.redisplay_index (1)
        return
    
    
    def select_all_entries (self, * arg):
        self.index.select_all ()
        return
    
    
    def add_entry (self, * arg):
        entry = self.data.new_entry (Config.get ('base/defaulttype').data)
        
        edit = Editor.Editor (self.data, entry, self.w, _("Create new entry"))
        edit.Subscribe ('commit-edition', self.commit_edition)
        return

    
    def edit_entry (self, entries):
        if not (type (entries) is types.ListType):
            entries = self.index.selection ()
        
        l = len (entries)

        if l == 0: return
        
        if l > 5:
            if not Utils.Callback (_("Really edit %d entries ?") % l):
                return

        for entry in entries:
            edit = Editor.Editor (self.data, entry, self.w)
            edit.Subscribe ('commit-edition', self.commit_edition)

        return


    def commit_edition (self, old, new):
        ''' updates the database and the display '''

        if old.key != new.key:
            if self.data.has_key (old.key):
                del self.data [old.key]

        if new.key:
            self.data [new.key] = new
        else:
            self.data.add (new)

        self.freeze_display (None)

        self.redisplay_index (1)
        self.index.select_item (new)
        return
    
    
    def delete_entry (self, * arg):
        ''' removes the selected list of items after confirmation '''
        entries = self.index.selection ()
        l = len (entries)
        if l == 0: return

        offset = self.index.get_item_position (entries [-1])

        if l > 1:
            question = _("Remove all the %d entries ?") % len (entries)
        else:
            question = _("Remove entry `%s' ?") % entries [0].key.key
            
        if not Utils.Callback (question,
                               parent = self.w).answer ():
            return

        for entry in entries:
            del self.data [entry.key]
            
        self.redisplay_index (1)
        self.index.select_item (offset)
        return
    
    
    def find_entries (self, * arg):
        if self.search_dg is None:
            self.search_dg = Search.SearchDialog (self.w)
            self.search_dg.Subscribe ('search-data', self.limit_view)
        else:
            self.search_dg.show ()
        return


    def limit_view (self, search):
        self.selection.search = search
        self.redisplay_index ()
        return

    
    def sort_entries (self, * arg):
        sort_dg = SortDialog (self.selection.sort, self.w)
        sort_dg.Subscribe ('sort-data', self.sort_view)
        return


    def sort_view (self, sort):
        self.selection.sort = sort
        self.redisplay_index ()
        return
    

    def sort_by_field (self, field):
        if field == '-key-':
            mode = Sort.KeySort ()
        elif field == '-type-':
            mode = Sort.TypeSort ()
        else:
            mode = Sort.FieldSort (field)
            
        self.selection.sort = Sort.Sort ([mode])
        self.redisplay_index ()
        return


    def lyx_cite (self, * arg):
        entries = self.index.selection ()
        if not entries: return
        
        if self.lyx is None:
            from Pyblio import LyX

            try:
                self.lyx = LyX.LyXClient ()
            except IOError, msg:
                self.w.error (_("Can't connect to LyX:\n%s") % msg [1])
                return

        keys = string.join (map (lambda x: x.key.key, entries), ', ')
        try:
            self.lyx ('citation-insert', keys)
        except IOError, msg:
            self.w.error (_("Can't connect to LyX:\n%s") % msg [1])
        return
    

    def update_display (self, entry):
        self.display.display (entry)
        return

    
    def freeze_display (self, entry):
        self.display.clear ()
        return


    def key_pressed (self, app, event):
        # filter out special keys
        if (event.string < 'a' or event.string > 'z') and \
           (event.string < '0' or event.string > '9'): return 1

        if self.selection.sort is None:
            app.flash ("Select a column to search in first.")
            return 1
        
        if event.string in printable:
            # the user searches the first entry in its ordering that starts with this letter
            if self.incremental_search == '':
                self.incremental_search = event.string
                self.incremental_start  = event.time
            else:
                if event.time - self.incremental_start > 1000:
                    self.incremental_search = event.string
                else:
                    # two keys in a same shot: we search for the composition of the words
                    self.incremental_search = self.incremental_search + event.string
                
                self.incremental_start  = event.time

            # search first occurence
            if self.index.go_to_first (self.incremental_search,
                                       self.selection.sort.fields [0]):
                app.flash ("Searching for '%s...'" % self.incremental_search)
            else:
                app.flash ("Cannot find '%s...'" % self.incremental_search)
                
        return 1


    def update_configuration (self):
        ''' save current informations about the program '''
        
        # Save the graphical aspect of the interface
        # 1.- Window size
        alloc = self.w.get_allocation ()
        Utils.config.set_int ('/apps/pybliographic/ui/width',  alloc [2])
        Utils.config.set_int ('/apps/pybliographic/ui/height', alloc [3])

        # 2.- Proportion betzeen list and text
        height = self.paned.get_position ()
        Utils.config.set_int ('/apps/pybliographic/ui/paned', height)

        # updates the index's config
        self.index.update_configuration ()

        return

    
    def about (self, *arg):
        
        about = ui.About ('Pybliographic',
                          version.version,
                          _("This program is copyrighted under the GNU GPL"),
                          _("Gnome interface to the Pybliographer system."),
                          ['Hervé Dréau',
                           'Frédéric Gobry',
                           'Travis Oliphant',
                           'Darrell Rudmann',
                           'Peter Schulte-Stracke',
                           'John Vu'],
                          ['Yuri Bongiorno',
                           'Frédéric Gobry'],
                          _('Gnome Translation Team'))

        about.set_transient_for (self.w)
        
        link = ui.HRef ('http://www.pybliographer.org/',
                        _("Pybliographer Home Page"))
        link.show ()
        about.vbox.pack_start (link)
        about.show()
        return
