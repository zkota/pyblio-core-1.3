from Pyblio.Adapter import OneToOneAdapter
from Pyblio import Store, Attribute, Registry

class WOK2BibTeX(OneToOneAdapter):

    def __init__(self, base):
        OneToOneAdapter.__init__(self, base)

        self.schema = Registry.getSchema('org.pybliographer/bibtex/0.1')
        return

    typemap = {
        '@': 'article'
        }
    
    def source2target(self, wok):
        bibtex = Store.Record()
        bibtex['id'] = wok['ut']

        dt = wok['doctype'][0]
        dt = self.base.schema.txo[dt.group][dt.id].names['C']

        if dt in self.typemap:
            bibtex.add('doctype', self.schema.txo['doctype'].byname(
                self.typemap[dt]), Attribute.Txo)
        for k in ('title', 'author', 'abstract'):
            if k in wok:
                bibtex[k] = wok[k]

        if 'source' in wok:
            bibtex.add('journal', unicode(wok.get('source')[0]),
                       Attribute.Text)
            for sub in ('pages', 'volume', 'number', 'year'):
                data = wok.get('source.' + sub)
                if data: bibtex.add(sub, data[0])
        return bibtex
    
