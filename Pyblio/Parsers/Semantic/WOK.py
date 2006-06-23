import logging

from gettext import gettext as _

from Pyblio import Attribute, Store


class Reader(object):
    """ Parse records as returned by Web of Science's web service."""
    
    log = logging.getLogger('pyblio.import.wok')

    # Supported fields

    def do_default(self, node):
        """ Called when no specific handler exist."""
        
        self.log.warn('%s: unhandled attribute %s' % (
            self.uid(), repr(node.tag)))
        return

    def do_ut(self, node):
        self.record.add('ut', node.text, Attribute.ID)

    def do_authors(self, node):
        
        def single(author):
            try:
                last, first = [part.strip() for part in author.split(',')]
                return Attribute.Person(last=last, first=first)
            except ValueError:
                return Attribute.Person(last=author.strip())
        
        for author in node:
            self.record.add('author', author.text, single)
        return

    def do_corp_authors(self, node):
        def single(author):
            return Attribute.Person(last=author)
        
        for author in node:
            self.record.add('author', author.text, single)

    def do_refs(self, node):
        for ref in node:
            self.record.add('ref', ref.text, Attribute.ID)
        return
    
    def do_keywords(self, node):
        for ref in node:
            self.record.add('keyword', ref.text, Attribute.Text)
        return

    def do_keywords_plus(self, node):
        for ref in node:
            self.record.add('keyword-plus', ref.text, Attribute.Text)
        return

    def do_abstract(self, node):
        self.record.add('abstract', node.text, Attribute.Text)
        return

    def do_doctype(self, node):
        tp = self._type(node.get('code'))
                        
        self.record.add('doctype', tp, Attribute.Txo)
        return

    def do_source_title(self, node):
        self.record.add('source', node.text, Attribute.Text)

    def do_item_title(self, node):
        self.record.add('title', node.text, Attribute.Text)

    def do_source_series(self, node):
        self.record.add('source.series', node.text, Attribute.Text)

    def do_source_abbrev(self, node):
        self.record.add('source.abbrev', node.text, Attribute.Text)

    def do_article_nos(self, node):

        for no in node:
            t = no.text.strip()
            if t.startswith('DOI '):
                self.record.add('doi', t[4:], Attribute.ID)
                continue

            self.log.warn('%s: unhandled article_no %s' % (
                self.uid(), repr(t)))
        return

    def do_bib_pages(self, node):
        self.record.add('source.pages', node.text, Attribute.Text)

    def do_bib_issue(self, node):
        for s, d in (('vol', 'source.volume'),
                     ('year', 'source.year')):
            
            v = node.get(s)
            if v:
                self.record.add(d, v, Attribute.Text)
        return


        
    # Fields I either don't need or don't know. Feel free to improve.
    
    def do_i_ckey(self, node):pass
    def do_i_cid(self, node):pass
    def do_sq(self, node):pass
    def do_emails(self, node):pass
    def do_reprint(self, node):pass
    def do_research_addrs(self, node):pass
    def do_languages(self, node):pass
    def do_bib_id(self, node):pass
    def do_editions(self, node):pass


    # Parsing logic and hooks

    def record_begin (self):
        pass

    def record_end (self):
        pass

    def uid(self):
        """ Generate the display name of a record.

        Used when outputting a warning for instance."""
        try:
            return 'ISI:' + self.record['ut'][0]
        except KeyError:
            return repr(self.record.key)

    
    def parse(self, fd, db, rs=None):

        if rs is None:
            rs = db.rs.add(True)
            rs.name = _('Imported from Web of Knowledge')

        self.db = db
        self._type = self.db.txo['doctype'].byname
        
        for item in fd.findall('./REC/item'):
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
    
    
