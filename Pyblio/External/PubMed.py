# This file is part of pybliographer
# 
# Copyright (C) 1998-2003 Frederic GOBRY
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
# 

"""
Programmatic access to the PubMed database
"""

# Documentation taken from:
#   http://eutils.ncbi.nlm.nih.gov/entrez/query/static/eutils_help.html
#

import logging, urllib

from gettext import gettext as _

from cElementTree import ElementTree, XML, dump

from twisted.web import client
from twisted.internet import defer, reactor

from Pyblio.Exceptions import QueryError
from Pyblio.External.HTTP import HTTPRetrieve
from Pyblio.Parsers.Semantic.PubMed import Reader


def _xml(data):
    """ Parse the result from the server, and immeditately catch
    possible errors."""
    tree = XML(data)

    err = tree.find('./ERROR')
    if err is not None:
        raise QueryError(err.text)

    return tree


class PubMed(object):
    """ A connection to the PubMed database """

    baseURL = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils'

    BATCH_SIZE = 500
    
    toolName = 'pybliographer'
    adminEmail = 'webmaster@pybliographer.org'

    log = logging.getLogger('pyblio.external.pubmed')

    SRV_SEARCH = '/esearch.fcgi'
    SRV_FETCH = '/efetch.fcgi'

    def __init__(self, db):

        self.db = db
        self._pending = None
        self.reader = Reader()
        
        return

    def _query(self, service, args, **kargs):

        all = {'email': self.adminEmail,
               'tool': self.toolName,
               'retmode': 'xml'}
        
        all.update(args)
        all.update(kargs)
        
        url = self.baseURL + service + '?' + urllib.urlencode(all)

        self.log.debug('sending query %r' % url)

        # We have the charge of setting and cleaning self._pending
        self._pending = HTTPRetrieve(url)

        def done(data):
            self._pending = None
            return data
        
        return self._pending.deferred.addBoth(done)


    def count(self, query, db='PubMed'):

        assert self._pending is None, 'no more than one search at a time per connection'

        data = {'db': db,
                'term': query}

        req = self._query(self.SRV_SEARCH, data, rettype='count')

        def success(data):
            return int(data.find('./Count').text)

        return req.addCallback(_xml).addCallback(success)

    
    def search(self, query, maxhits=500, db='PubMed'):

        assert self._pending is None, 'no more than one search at a time per connection'

        data = {'db': db,
                'term': query}

        req = self._query(self.SRV_SEARCH, data, usehistory='y')

        # The deferred for the global result
        results = defer.Deferred()

        # The result set that will contain the data
        rs = self.db.rs.add(True)
        rs.name = _('Imported from PubMed')

        def failed(reason):
            results.errback(reason)
        
        def got_summary(data):
            # Total number of results
            all_results = int(data.find('./Count').text)

            # Parameters necessary to fetch the content of the result set
            fetchdata = {
                'db': db,
                'WebEnv': data.find('./WebEnv').text,
                'query_key': data.find('./QueryKey').text,
                }
            
            wanted = min(all_results, maxhits)
            
            self.log.debug('%d results, retrieving %d' % (all_results, wanted))

            def fetch(data):
                if data is not None:
                    # Process the incoming XML data
                    self.reader.parse(data, self.db, rs)
                    self._remaining = 0
                    pass

                if len(rs) >= wanted:
                    results.callback(all_results)
                    return
                
                d = self._query(self.SRV_FETCH, fetchdata,
                                retstart=len(rs),
                                retmax=self.BATCH_SIZE)
            
                d.addCallback(_xml).\
                    addCallback(fetch).\
                    addErrback(failed)
                return

            # Bootstrap the fetching process
            fetch(None)

        req.addCallback(_xml).\
            addCallback(got_summary).\
            addErrback(failed)

        return results, rs


    def cancel(self):
        """ Cancel a running query. The database is not reverted to its
        original state."""
        if not self._pending:
            return

        self._pending.cancel()
        return
