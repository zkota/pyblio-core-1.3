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
"""
Parser for the XML format returned by PubMed's Web API
"""

import logging

from gettext import gettext as _

from Pyblio import Attribute, Store

class Reader(object):
    """ Parse records as returned by PubMed's web service."""
    
    log = logging.getLogger('pyblio.import.pubmed')

    def uid(self):
        """ Generate the display name of a record.

        Used when outputting a warning for instance."""
        try:
            return 'PMID:' + self.record['pmid'][0]
        except KeyError:
            return repr(self.record.key)

    # Supported fields
    def do_default(self, node):
        """ Called when no specific handler exist."""
        
        self.log.warn('%s: unhandled attribute %s' % (
            self.uid(), repr(node.tag)))
        return


    def do_Article(self, node):
        for child in node:
            fn = getattr(self, 'do_Article_' + child.tag,
                         self.do_default)
            fn(child)
        return

    def do_Article_ArticleTitle(self, node):
        self.record.add('title', node.text, Attribute.Text)
        
    def do_Article_Abstract(self, node):
        abstract = node.find('./AbstractText')
        self.record.add('abstract', abstract.text, Attribute.Text)

    def do_Article_Journal(self, node):
        self.record.add('journal', node.find('Title').text, Attribute.Text)
        self.record.add('journal.issn', node.find('ISSN').text, Attribute.ID)
        
        self.record.add('journal.volume',
                        node.find('JournalIssue/Volume').text, Attribute.Text)
        self.record.add('journal.issue',
                        node.find('JournalIssue/Issue').text, Attribute.Text)

        self.record.add('journal.year',
                        node.find('JournalIssue/PubDate/Year').text, Attribute.Text)
        self.record.add('journal.month',
                        node.find('JournalIssue/PubDate/Month').text, Attribute.Text)
        

    def do_Article_AuthorList(self, node):
        for au in node.findall('./Author'):
            person = Attribute.Person(
                last=au.find('./LastName').text,
                first=au.find('./ForeName').text)
            self.record.add('author', person)
        

    def do_PMID(self, node):
        self.record.add('pmid', node.text, Attribute.ID)

    # Parsing logic and hooks

    def record_begin (self):
        pass

    def record_end (self):
        pass
    
    def parse(self, fd, db, rs=None):

        if rs is None:
            rs = db.rs.add(True)
            rs.name = _('Imported from PubMed')

        self.db = db
        
        for item in fd.findall('./PubmedArticle/MedlineCitation'):
            self.record = Store.Record()
            self.record_begin()

            for child in item:
                fn = getattr(self, 'do_' + child.tag,
                             self.do_default)
                fn(child)

            self.record_end()
            
            k = db.add(self.record)
            rs.add(k)
        
        return rs
    
    
