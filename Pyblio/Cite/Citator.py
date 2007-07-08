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
Defines the Citator, a class that glues together every aspect related
to citations. It reads and stores this information from an XML file,
making it easy to distribute per-journal citation styles for instance.

WARNING: this object loads python modules by their name. It might do
nasty things if the file comes from untrusted sources.
"""


import logging
from cElementTree import ElementTree
from gettext import gettext as _

from Pyblio.Exceptions import ParserError

log = logging.getLogger('pyblio.cite.citator')

class Citator(object):
    """ """
    
    def __init__(self):
        pass

    def xmlload(self, fd):
        tree = ElementTree(file=fd)
        root = tree.getroot()
        if root.tag != 'pyblio-citator':
            raise ParserError(_("file is not a Citator XML file"))

        self.name = root.find('./name').text
        
        def get_last(name):
            name = root.find(name).text.strip()
            idx = name.rfind('.')
            return name[:idx], name[idx+1:]
        
        self.style = get_last('./citation-style')
        self.keys  = get_last('./key-style')
        self.order = get_last('./bibliography-order')
        return

    def prepare(self, db, wp, extra_info=None):
        """Link the citator with a specific database and word
        processor. @extra_info is an optional function that will
        return a string to store along with the entry, if the word
        processor allows it.

        Args:
          db: Pyblio.Store.Database
          wp: Pyblio.Cite.WP.IWordProcessor
          extra_info: str = fn(Pyblio.Store.Key, Pyblio.Store.Database) or None
        """
        
        def load(path):
            mod = __import__(path[0], {}, {}, [path[1]])
            return getattr(mod, path[1])
        
        self.m_style = load(self.style)
        self.m_keys  = load(self.keys)
        self.m_order = load(self.order)

        self.db = db
        self.wp = wp
        self.extra_info = extra_info or (lambda key, db: None)
        
        # keygen will generate the new keys
        self.keygen = self.m_keys(self.db)

        # formatter is the compiled citation formatter
        self.formatter = self.m_style(self.db)
        return
    
    def update(self):
        """ Force an update of keys and bibliography content """
        
        # We need to resynchronize the local state with the remote
        # info. Fetch the list of known references from the current
        # document
        known = self.wp.fetch()
        log.info('fetched keys from document: %r' % known)

        if known is not None:
            # Regenerate the keys, and update the ones that changed.
            # We need to restart the key generator, to ensure it
            # provides them in a coherent order.
            self.keygen = self.m_keys(self.db)
            
            to_update = {}
            for uid, key, extra in known:
                newkey = self.keygen.make_key(uid)
                if newkey != key:
                    to_update[uid] = newkey

            known = self.wp.update_keys(to_update)

            # update the biblio itself
            insert = self.wp.update_biblio()

            insert.begin_biblio()
            for uid, key in self.m_order(known):
                insert.begin_reference(key)
                insert(self.formatter(self.db[uid]))
                insert.end_reference(key)
            insert.end_biblio()
        return
    
    def cite(self, uids):
        """ Insert the specified record identifiers in the current
        document"""
        
        keys = [(ref,
                 self.keygen.make_key(ref),
                 self.extra_info(ref, self.db)) for ref in uids]
        self.wp.cite(keys, self.db)
        return
    
    
