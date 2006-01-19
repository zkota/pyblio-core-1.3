from Pyblio.Parsers.Syntax import Tagged
from Pyblio import Attribute

from gettext import gettext as _

import re, string

# DEBUG
import pprint

start_re = re.compile (r'^(\w\w)\s(.*?)\r?$')
contd_re = re.compile (r'^\s{3,3}(.*?)\r?$')

class ISIParser (Tagged.Parser):

    """ This parser knows how to split RIS records in fields """

    def line_handler (self, line, count):

        if line.strip () == '': return

        m = start_re.match (line)

        if m:
            tag, data = m.groups ((1, 2))

            if tag in ('FN', 'VR', 'EF'):
                return

            if tag == 'PT':
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
            self.field_data ('\n' + m.group (1))
            return

        if line == 'EF': return

        raise SyntaxError (_('line %d: unexpected data: %s') % (count, repr (line)))


def _mkperson (txt):

    res = map (string.strip, txt.split (','))
    if len(res) == 1:
        last = res[0]
        first = None
    else:
       if len(res) == 2:
          last, first = res
       else:
          last = txt
          first = None

    return Attribute.Person (last = last, first = first)


class Reader(Tagged.Reader):

    """ The importer knows how to map the RIS fields to the 'standard'
    pyblio model."""

    Parser = ISIParser

    mapping = {}


    def person_add (self, field, value):

        ''' Parse a person name in ISI format '''

        self.record [field] = [ _mkperson (txt) for txt in value.split ('\n') ]
        return


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
