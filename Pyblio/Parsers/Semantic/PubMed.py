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
    
    
