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
Parser for the ISI format returned by the Web of Knowledge.
"""

import logging

from Pyblio.Parsers.Syntax import ISI
from Pyblio import Attribute

class Reader(ISI.Reader):
    # mapping between document types declared in the ISI file format,
    # and doctypes declared in the XML Web of Knowledge format...  Not
    # very readable, but would it be more sensible to add an
    # additional notation in this mess?
    # See Pyblio/RIS/wok.sip for detailed explanations on the document types.
    doctype_mapping = {
        'J': '@'
        }

    log = logging.getLogger('pyblio.import.isi')

    def record_begin(self):
        self._page_start = None

    def do_PT(self, line, tag, data):
        # publication type
        type_name = self.doctype_mapping[data]
        self.record.add('doctype', self.db.schema.txo['doctype'].byname(type_name),
                        Attribute.Txo)

    def do_DT(self, line, tag, data):
        # document type? difference with PT?
        pass

    def do_ID(self, line, tag, data):
        # keywords
        for kw in data.split(';'):
            self.record.add('keyword', kw.strip(), Attribute.Text)

    def do_AU(self, line, tag, data):
        # author
        self.person_add('author', data)

    def do_TI(self, line, tag, data):
        # title
        self.record.add('title', data, Attribute.Text)

    def do_UT(self, line, tag, data):
        # identifier
        if ':' in data:
            source, uid = data.split(':')
            if source == 'ISI':
                self.record.add('ut', uid, Attribute.ID)

    def do_AB(self, line, tag, data):
        # abstract
        self.record.add('abstract', data, Attribute.Text)

    def do_SO(self, line, tag, data):
        # source
        self.record.add('source', data, Attribute.Text)

    def do_JI(self, line, tag, data):
        self.record.add('source.abbrev', data, Attribute.Text)
    def do_J9(self, line, tag, data):
        self.record.add('source.abbrev', data, Attribute.Text)

    def do_PY(self, line, tag, data):
        # publication year
        self.record.add('source.year', data, Attribute.Text)

    def do_SE(self, line, tag, data):
        # series
        self.record.add('source.series', data, Attribute.Text)

    def do_VL(self, line, tag, data):
        # volume
        self.record.add('source.volume', data, Attribute.Text)

    def do_IS(self, line, tag, data):
        # number (issue)
        self.record.add('source.number', data, Attribute.Text)

    def do_SN(self, line, tag, data):
        # ISSN
        self.record.add('source.issn', data, Attribute.ID)

    def do_C1(self, line, tag, data):
        # authors' addresses
        pass
    def do_RP(self, line, tag, data):
        # authors' addresses
        pass

    def do_BP(self, line, tag, data):
        self._page_start = data
    def do_EP(self, line, tag, data):
        if self._page_start is not None:
            if self._page_start == data:
                page_range = data
            else:
                page_range = self._page_start + '-' + data
            self.record.add('source.pages', page_range, Attribute.Text)

    def do_default(self, line, tag, data):
        try:
            ISI.Reader.do_default(self, line, tag, data)
        except ISI.ParserError, msg:
            self.log.warn(str(msg))
