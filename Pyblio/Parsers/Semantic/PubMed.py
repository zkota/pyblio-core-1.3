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
Parser for the XML format returned by PubMed's Web API
"""

import logging

from gettext import gettext as _

from Pyblio import Attribute, Store
from cElementTree import dump

_DEBUG = False

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

    def do_MedlineJournalInfo(self, node):
        # this can contain the journal title, but as a fallback
        self._fallback_journal = node.findtext('./MedlineTA')

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
        def maybe(dst, key, conv):
            v = node.find(key)
            if v is not None:
                self.record.add(dst, v.text, conv)

        # optionally, the title can come from the MedlineTA field
        maybe('journal', 'Title', Attribute.Text)
        maybe('journal.issn', 'ISSN', Attribute.ID)
        
        maybe('journal.volume', 'JournalIssue/Volume', Attribute.Text)
        maybe('journal.issue', 'JournalIssue/Issue', Attribute.Text)

        maybe('journal.year', 'JournalIssue/PubDate/Year', Attribute.Text)
        maybe('journal.month', 'JournalIssue/PubDate/Month', Attribute.Text)

    def do_Article_AuthorList(self, node):
        def v(n, k):
            l = n.find(k)
            if l is not None:
                return l.text
            return None
        
        for au in node.findall('./Author'):
            person = Attribute.Person(
                last=v(au, './LastName'),
                first=v(au, './ForeName'))
            self.record.add('author', person)

    def do_Article_Pagination(self, node):
        v = node.find('./MedlinePgn')
        if v is not None and v.text:
            # pubmed will return abbreviated page ranges (1234-45
            # meaning 1234-1245). We transform them into full ranges,
            # as this is only some kind of space saving convention.
            pages = v.text
            textual_pair = pages.split('-')
            try:
                pair = [int(x) for x in textual_pair]
            except ValueError:
                pair = []
            if len(pair) == 2 and pair[1] < pair[0]:
                # we could play with logs to find out the actual cut
                # point, but using the textual representation is
                # probably more natural
                left, right = textual_pair
                full_right = left[:len(left)-len(right)] + right
                if int(full_right) > pair[0]:
                    pages = '%s-%s' % (left, full_right)
            self.record.add('journal.pages', pages, Attribute.Text)

    def do_PMID(self, node):
        self.record.add('pmid', node.text, Attribute.ID)

    # Parsing logic and hooks

    def record_begin (self):
        pass

    def record_end(self):
        # in some cases, the journal title wasn't in the Journal node,
        # but can be recovered from the MedlineTA field.
        j = self.record.get('journal')
        if j and not j[0].is_complete() and self._fallback_journal:
            self.record.add('journal', self._fallback_journal, Attribute.Text)

    def parse(self, fd, db, rs=None):

        if rs is None:
            rs = db.rs.new()
            rs.name = _('Imported from PubMed')

        self.db = db
        
        for item in fd.findall('./PubmedArticle/MedlineCitation'):
            self.record = Store.Record()
            self.record_begin()

            if _DEBUG:
                dump(item)
            for child in item:
                fn = getattr(self, 'do_' + child.tag,
                             self.do_default)
                fn(child)

            self.record_end()
            
            k = db.add(self.record)
            rs.add(k)
        
        return rs
