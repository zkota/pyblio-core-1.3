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
# 

"""
Citeseer (http://citeseer.ist.psu.edu/) queries
"""

# Citeseer provides two ways to search for documents: its own search
# engine, and Google. This code use the first solution (as Google's
# search API is not what it used to be...): first, all the links to
# all the detailed citation pages are collected, then each page is
# parsed, and the bibtex and abstract are extracted.

import urllib
import logging
import BeautifulSoup
import re
import StringIO

from gettext import gettext as _
from twisted.internet import defer, reactor

from Pyblio import Attribute
from Pyblio.External import IExternal
from Pyblio.External.HTTP import HTTPRetrieve
from Pyblio.Exceptions import QueryError
from Pyblio.Parsers.Semantic import BibTeX

log = logging.getLogger('pyblio.external.citeseer')

whitespace = re.compile(r'[\s\n]+', re.M)

class ResultScraper(object):
    """Parse a Citeseer result page containing links to the actual
    detailed citations."""

    results = re.compile(r'(\d+|No)\s+documents?\s+found')
    def __init__(self, page):
        self.soup = BeautifulSoup.BeautifulSoup(page)
        self.rls = self.soup.findAll(
            text=lambda text: isinstance(text, BeautifulSoup.Comment) and \
            text == 'RLS')[0]
        self.ris = self.soup.findAll(
            text=lambda text: isinstance(text, BeautifulSoup.Comment) and \
            text == 'RIS')

    def count(self):
        """Return the overall result count."""
        # the result count is immediately before the list of results,
        # unless we see no RIS comments, in which case there is no
        # result at all.
        if not self.ris:
            return 0
        current = self.rls.previous
        while current is not None:
            if current.string is not None:
                m = self.results.search(current.string)
                if m:
                    return int(m.group(1))
            current = current.previous
        raise QueryError(_("cannot parse result page"))

    def links(self):
        """Return the result links."""
        return [str(ris.findNext('a')['href']) for ris in self.ris]


class RelaxedBibTeX(BibTeX.Reader):
    def do_default(self, field, value):
        log.warn('dropping field %r' % field)

    def to_text(self, stream):
        text = stream.execute(self.env).flat().strip()
        return Attribute.Text(whitespace.sub(' ', text))

class CitationScraper(object):
    """Parse a detailed citation page, containing an abstract and a
    BibTeX snippet."""

    def __init__(self, page):
        self.soup = BeautifulSoup.BeautifulSoup(page)

    def citation(self):
        content = {'bibtex': self.soup.pre.string}
        abstract = self.soup.findAll(text='Abstract:')
        if abstract:
            abstract = abstract[0].parent.nextSibling.strip()
            content['abstract'] = whitespace.sub(' ', abstract)
        return content
        

class Citeseer(IExternal):
    """A connection to Citeseer."""

    schema = 'org.pybliographer/bibtex/0.1'

    BATCH_SIZE = 50
    FETCHER_POOL = 2 # how many detailed pages to fetch at a time
    
    MIRRORS = ['http://citeseer.ist.psu.edu/cis',
               'http://citeseer.ittc.ku.edu/cs']

    baseURL = MIRRORS[1]
    
    def __init__(self, db):
        self.db = db
        self._pending = None
        self._reader = RelaxedBibTeX('utf-8')

    def _query(self, query, start=0):
        assert self._pending is None, \
               'no more than one search at a time per connection'

        qb = {'dbnum': 1,
              'start': start,
              'am': self.BATCH_SIZE,
              'ao': 'Citations',
              'af': 'Any',
              'qtype': 'document:'}
        all = {'q': query,
               'qb': ','.join('%s=%s' % v for v in qb.iteritems())}
            
        for k, v in all.items():
            if isinstance(v, unicode):
                all[k] = v.encode('utf-8')
        url = self.baseURL +'?' + urllib.urlencode(all)

        log.info('sending query %r' % url)
        self._pending = HTTPRetrieve(url)

        def done(data):
            self._pending = None
            return data
        def parse(data):
            return ResultScraper(data)
        return self._pending.deferred.\
               addBoth(done).\
               addCallback(parse)

    def count(self, query):
        req = self._query(query)
        results = defer.Deferred()

        def failed(reason):
            results.errback(reason)
        def got_summary(data):
            results.callback(data.count())
        req.addCallback(got_summary).addErrback(failed)
        return results
    
    def search(self, query, maxhits=100):
        rs = self.db.rs.new()
        rs.name = _('Imported from Citeseer')

        req = self._query(query)
        results = defer.Deferred()

        self._abort = False

        def failed(reason):
            results.errback(reason)

        def got_page(data, link):
            """Handle a detailed citation page."""
            if data:
                log.info('obtained page %r' % link)
                citation = data.citation()
                fd = StringIO.StringIO(citation['bibtex'].encode('utf-8'))
                obtained = self._reader.parse(fd, self.db)
                for key in obtained:
                    # we can enrich the result with an abstract
                    if 'abstract' in citation:
                        record = self.db[key]
                        record.add('abstract',
                                   citation['abstract'],
                                   Attribute.Text)
                        self.db[key] = record
                    rs.add(key)
            if self._links and not self._abort:
                # there are more links to process, launch a new
                # HTTPRetrieve().
                link = self._links.pop()
                fetcher = HTTPRetrieve(link)
                log.info('fetching detailed page %r' % link)
                self._running.append(link)
                def done(data):
                    self._running.remove(link)
                    return data
                def parse_citation(data):
                    return CitationScraper(data)
                def inner_failure(data):
                    if not self._running:
                        results.errback(data)
                    self._abort = data
                fetcher.deferred.\
                        addBoth(done).\
                        addCallback(parse_citation).\
                        addCallback(got_page, link).\
                        addErrback(inner_failure)
            elif not self._running:
                # we are done once there is no pending link to fetch
                # and all the running fetchers have returned.
                if not self._abort or self._abort is True:
                    results.callback(self._total)
                else:
                    results.errback(self._abort)

        def got_summary(data):
            """Handle a result page."""
            # initial pass, collect all the results, up to maxhits
            self._total = data.count()
            self._target = min(maxhits, self._total)
            self._current = 0
            log.info('%d results for the query' % self._total)
            self._links = set()

            def got_links(data):
                current = data.links()
                previous = len(self._links)
                self._links.update(current)
                obtained = len(self._links) - previous
                if obtained == 0:
                    log.warn('this batch did not provide new links, stopping')
                self._current += self.BATCH_SIZE
                log.info('%d links in this batch (%s/%d)' % (
                    len(current), len(self._links), self._total))
                missing = self._target - len(self._links)
                if missing > 0 and obtained > 0:
                    log.info('getting batch at %d, %d missing' % (
                        self._current, missing))
                    next = self._query(query, self._current)
                    next.addCallback(got_links).addErrback(failed)
                else:
                    # start getting the detailed citation pages
                    self._running = []
                    for i in xrange(self.FETCHER_POOL):
                        got_page(None, None)
            got_links(data)
        req.addCallback(got_summary).addErrback(failed)
        return results, rs

    def cancel(self):
        self._abort = True
        if self._pending:
            self._pending.cancel()
    
