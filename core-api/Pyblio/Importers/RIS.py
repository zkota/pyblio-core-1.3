from Pyblio.Importers import Tagged

from gettext import gettext as _

import re

start_re = re.compile (r'^(\w\w)\s\s-\s(.*?)\r?$')
contd_re = re.compile (r'^\s{6,6}(.*?)\r?$')

class Transport (Tagged.Tagged):

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
            self.field_data (m.group (1))
            return
        
        raise SyntaxError (_('line %d: unexpected data') % count)
