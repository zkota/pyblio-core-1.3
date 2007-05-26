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
        target_type = self.typemap.get(dt, 'article')
        bibtex.add('doctype', self.schema.txo['doctype'].byname(
            target_type), Attribute.Txo)

        for k in ('title', 'author', 'abstract'):
            if k in wok:
                bibtex[k] = wok[k]

        if 'source' in wok:
            source = wok.get('source')[0]
            bibtex.add('journal', unicode(source), Attribute.Text)
            for sub in ('pages', 'volume', 'number'):
                data = source.q.get(sub)
                if data:
                    bibtex.add(sub, data[0])
            if 'year' in source.q:
                try:
                    bibtex.add('date',
                               Attribute.Date(int(source.q['year'][0])))
                except TypeError:
                    pass
        return bibtex
    
