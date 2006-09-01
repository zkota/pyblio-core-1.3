from Pyblio.Parsers.Syntax import BibTeX
from Pyblio import Attribute

_monthmap={
    'january': 1,
    'february': 2,
    'march': 3,
    'april': 4,
    'may': 5,
    'june': 6,
    'july': 7,
    'august': 8,
    'september': 9,
    'october': 10,
    'november': 11,
    'december': 12,
    }

class Reader(BibTeX.Reader):
    """ Default BibTeX parser.
    """

    def string_add(self, data):
        # Simply fill in the provided strings
        for key, value in data.fields:
            self.env.strings[key] = value
        return

    def type_add(self, name):
        txo = self.db.schema.txo['doctype'].byname(name.lower())
        self.record.add('doctype', txo, Attribute.Txo)
        return

    def record_begin(self):
        self.date = Attribute.Date()
        return
    
    def record_end(self):
        if self.date != Attribute.Date():
            self.record['date'] = [self.date]
        return
    
    def do_year(self, value):
        year = self.to_text(value).strip()
        if not year: return
        
        try:
            self.date.year = int(year)
        except ValueError, msg:
            raise ValueError('in %s: %s' % (self.key, msg))
        return
    
    def do_month(self, value):
        month = self.to_text(value).lower().strip()
        if not month: return
        
        try:
            self.date.month =_monthmap[month]
        except KeyError, msg:
            raise KeyError('in %s: %s' % (self.key, msg))
            
        return
    
        
    
class Writer(BibTeX.Writer):
    pass
