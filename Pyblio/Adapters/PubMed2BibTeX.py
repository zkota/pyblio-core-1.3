from Pyblio.Adapter import OneToOneAdapter
from Pyblio import Store, Attribute, Registry

class PubMed2BibTeX(OneToOneAdapter):

    def __init__(self, base):
        OneToOneAdapter.__init__(self, base)

        self.schema = Registry.getSchema('org.pybliographer/bibtex/0.1')
        return
    
    def source2target(self, medline):
        bibtex = Store.Record()

        bibtex.add('doctype', self.schema.txo['doctype'].byname('article'), Attribute.Txo)

        bibtex['id'] = medline['pmid']
        
        for k in ('title', 'author', 'abstract'):
            if k in medline:
                bibtex[k] = medline[k]

        return bibtex
    
