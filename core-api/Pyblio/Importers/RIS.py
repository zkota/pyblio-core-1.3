from Pyblio.Importers import Tagged
from Pyblio import Attribute

from gettext import gettext as _

import re, string

start_re = re.compile (r'^(\w\w)\s\s-\s(.*?)\r?$')
contd_re = re.compile (r'^\s{6,6}(.*?)\r?$')

class RISParser (Tagged.Parser):

    """ This parser knows how to split RIS records in fields """

    def line_handler (self, line, count):

        if line.strip () == '': return

        m = start_re.match (line)

        if m:
            tag, data = m.groups ((1, 2))

            if tag == 'TY':
                self.record_start ()

            elif self.state == self.ST_IN_FIELD:
                self.field_end ()
                
            if tag == 'ER':
                self.record_end ()
                return
            
            self.field_start (tag, count)
            self.field_data (data)
            return

        m = contd_re.match (line)
        if m:
            self.field_data (' ' + m.group (1))
            return
        
        raise SyntaxError (_('line %d: unexpected data') % count)


class Importer (Tagged.Importer):

    """ The importer knows how to map the RIS fields to the 'standard'
    pyblio model."""

    Parser = RISParser


    def person_add (self, field, value):

        ''' Parse a person name in RIS format '''
        
        last, first, lineage = (map (string.strip,
                                     value.split (',')) + [None, None]) [:3]


        a = self.record.get (field, [])
        a.append (Attribute.Person (last = last,
                                    first = first,
                                    lineage = lineage))
        
        self.record [field] = a
        return


    def date_add (self, field, value):

        ''' Parse a date in RIS format '''

        year, month, day = (map (int, value.split ('/')) + [None, None]) [:3]

        
        a = self.record.get (field, [])
        a.append (Attribute.Date (year = year, month = month, day = day))
        
        self.record [field] = a
        return
    
    
    mapping = {

        'T1': (Tagged.Importer.text_add, 'title'),
        'TI': (Tagged.Importer.text_add, 'title'),
        'CT': (Tagged.Importer.text_add, 'title'),
        'BT': (Tagged.Importer.text_add, 'title'),
        'N1': (Tagged.Importer.text_add, 'note'),
        'AB': (Tagged.Importer.text_add, 'note'),
        'JF': (Tagged.Importer.text_add, 'journal'),
        'JO': (Tagged.Importer.text_add, 'journal'),
        'JA': (Tagged.Importer.text_add, 'journal'),
        'J1': (Tagged.Importer.text_add, 'journal'),
        'J2': (Tagged.Importer.text_add, 'journal'),
        'VL': (Tagged.Importer.text_add, 'volume'),
        'IS': (Tagged.Importer.text_add, 'issue'),
        'CP': (Tagged.Importer.text_add, 'issue'),
        'CY': (Tagged.Importer.text_add, 'city'),
        'PB': (Tagged.Importer.text_add, 'publisher'),
        'N2': (Tagged.Importer.text_add, 'abstract'),
        'SN': (Tagged.Importer.text_add, 'issn'),
        'AV': (Tagged.Importer.text_add, 'availability'),
        'AD': (Tagged.Importer.text_add, 'address'),

        'ID': (Tagged.Importer.id_add, 'id'),

        'UR': (Tagged.Importer.url_add, 'url'),

        'A1': (person_add, 'author'),
        'AU': (person_add, 'author'),

        'Y1': (date_add, 'date'),
        'PY': (date_add, 'date'),
        
        'L1': '? pdf ?',
        'L2': '? fulltext ?',

        'TY': '? type ?',

        'KW': '? keyword ?',

        'SP': '? start page ?',
        'EP': '? end page ?',
        
        'RP': '? reprint ?',


        'T2': '? title secondary ?',
        'A2': '? author secondary ?',
        'ED': '? author secondary ?',
        
        'T3': '? title series ?',
        'A3': '? author series ?',

        'Y2': '? date secondary ?',

        'U1': '? user defined ?',
        'U2': '? user defined ?',
        'U3': '? user defined ?',
        'U4': '? user defined ?',
        'U5': '? user defined ?',

        'M1': '? misc ?',
        'M2': '? misc ?',
        'M3': '? misc ?',

        'L3': '? related ?',
        'L4': '? images ?'
        }


    def do_TY (self, line, tag, data):

        pass

    def do_SP (self, line, tag, data):

        self._sp = data.strip ()
        return
    
    def do_EP (self, line, tag, data):

        self._ep = data.strip ()
        return
    
    def do_KW (self, line, tag, data):

        pass
    
    def do_RP (self, line, tag, data):

        pass
    

    def do_default (self, line, tag, data):

        try:
            meth, field = self.mapping [tag]

        except KeyError:

            raise SyntaxError (_("line %s: unknown tag '%s'") % (line, tag))

        except ValueError:

            self.emit ('warning',
                       (_("line %s: unsupported tag '%s'") % (line, tag)))
            return
        
        meth (self, field, data)
        return
    
