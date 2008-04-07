# This file is part of pybliographer
# 
# Copyright (C) 1998-2008 Frederic GOBRY
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

"""Query arXiv.org."""

# TODO: seems to be using so called opensearch spec. Might be
# interesting to factor out.

import logging
import urllib

from gettext import gettext as _

from Pyblio import Compat
from Pyblio.Exceptions import QueryError
from Pyblio.External.HTTP import HTTPRetrieve
from Pyblio.External import batch
from Pyblio.Parsers.Semantic.arxiv import Reader

def _xml(data):
    """ Parse the result from the server, and immeditately catch
    possible errors."""
    tree = Compat.ElementTree.XML(data)

    err = tree.find('./ERROR')
    if err is not None:
        raise QueryError(err.text)
    return tree


class Arxiv(object):
    """Send queries to arXiv."""

    schema = 'org.pybliographer/arxiv/0.1'

    baseURL = 'http://export.arxiv.org/api/query'
    BATCH_SIZE = 100

    log = logging.getLogger('pyblio.external.arxiv')

    def __init__(self, db):
        """Create an object which will send queries to arXiv and
        collect the results in 'db'.

        Args:
          db: a Pyblio.Store.Database
        """
        self.db = db
        self.reader = Reader()

        self._pending = None

    def count(self, query):
        """Return the number of results for the specified query.

        Args:
          query: string in arXiv syntax
        Returns:
          deferred(int)
        """
        d = self._send_query(query, 0, 0)

        def success(data):
            s = data.find(
                '{http://a9.com/-/spec/opensearch/1.1/}totalResults')
            if s is None:
                raise QueryError('cannot find result count')
            return int(s.text)

        return d.addCallback(success)

    def search(self, query, maxhits=BATCH_SIZE):
        self._query = query
        self._batch = batch.Batch(maxhits, self.BATCH_SIZE)
        self._rs = self.db.rs.new()
        self._rs.name = _('Imported from arXiv')
        self.log.info('searching for %r' % query)
        return self._batch.fetch(self._runner), self._rs

    def cancel(self):
        """ Cancel a running query.

        The database is not reverted to its original state."""
        if self._pending:
            self._pending.cancel()

    def _send_query(self, query, start, max_results):
        assert self._pending is None

        all = {'search_query': query,
               'start': start,
               'max_results': max_results}
        url = self.baseURL + '?' + urllib.urlencode(all)
        self._pending = HTTPRetrieve(url)

        def done(data):
            self._pending = None
            return data

        return self._pending.deferred.\
               addBoth(done).\
               addCallback(_xml)

    def _runner(self, start, count):
        """Invoked to fetch successive result blocks.

        Returns:
          a deferred which provides the number of results
          fetched
        """
        def _received(data):
            s = data.find(
                '{http://a9.com/-/spec/opensearch/1.1/}totalResults')
            total = int(s.text)
            s = data.find(
                '{http://a9.com/-/spec/opensearch/1.1/}itemsPerPage')
            received = int(s.text)
            return received, total

        return self._send_query(self._query, start, count).\
               addCallback(_received)
                               
