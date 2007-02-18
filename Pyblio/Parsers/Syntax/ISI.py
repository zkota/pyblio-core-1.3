# This file is part of pybliographer
# 
# Copyright (C) 1998-2006 Frederic GOBRY
# Email : gobry@pybliographer.org
# 	   
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2 
# of the License, or (at your option) any later version.
#   
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details. 
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""
Parser for the ISI file format.
"""

from Pyblio.Parsers.Syntax import Tagged
from Pyblio import Attribute
from Pyblio.Exceptions import ParserError

from gettext import gettext as _

import re, string

start_re = re.compile (r'^(\w\w)\s(.*?)\r?$')
contd_re = re.compile (r'^\s{3,3}(.*?)\r?$')

class ISIParser (Tagged.Parser):

    """ This parser knows how to split ISI records in fields """

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

        raise ParserError(_('line %d: unexpected data: %s') % (count, repr (line)))


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
    """This reader has no knowledge of an actual scheme to map the
    fields to.  Check Pyblio.Parsers.Semantic.ISI for a parser that
    knows the actual ISI fields.
    """

    Parser = ISIParser

    mapping = {}

    def person_add(self, field, value):
        ''' Parse a person name in ISI format '''

        self.record [field] = [ _mkperson (txt) for txt in value.split ('\n') ]
        return


    def do_default(self, line, tag, data):
        try:
            meth, field = self.mapping[tag]
        except KeyError:
            raise ParserError(_("line %s: unknown tag '%s'") % (line, tag))

        except ValueError:
            self.emit ('warning',
                       (_("line %s: unsupported tag '%s'") % (line, tag)))
            return

        meth(self, field, data)
        return
