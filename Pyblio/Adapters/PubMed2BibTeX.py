from Pyblio.Adapter import OneToOneAdapter
from Pyblio import Store, Attribute, Registry

class PubMed2BibTeX(OneToOneAdapter):

    def __init__(self, base):
        OneToOneAdapter.__init__(self, base)

        self.schema = Registry.getSchema('org.pybliographer/bibtex/0.1')
        return
    
    def source2target(self, medline):
        bibtex = Store.Record()

        bibtex.add('doctype',
                   self.schema.txo['doctype'].byname('article'),
                   Attribute.Txo)

        bibtex['id'] = medline['pmid']
        
        for k in ('title', 'author', 'abstract', 'journal'):
            if k in medline:
                bibtex[k] = medline[k]

        year = medline.get('journal.year')
        if year:
            bibtex.add('date', Attribute.Date(year=int(year[0])))

        bibtex.add('volume', medline.get('journal.volume', [None])[0])
        bibtex.add('number', medline.get('journal.issue', [None])[0])
        
        return bibtex
    
