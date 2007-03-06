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
Programmatic access to the PubMed database
"""

# Documentation taken from:
#   http://eutils.ncbi.nlm.nih.gov/entrez/query/static/eutils_help.html
#

import logging, urllib
import datetime

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

class QueryHelper(object):

    publication_types = {
        _('Addresses'): 'addresses',
        _('Bibliography'): 'bibliography',
        _('Biography'): 'biography',
        _('Classical Article'): 'classical article',
        _('Clinical Conference'): 'clinical conference',
        _('Clinical Trial'): 'clinical trial',
        _('Clinical Trial, Phase I'): 'clinical trial, phase I',
        _('Clinical Trial, Phase II'): 'clinical trial, phase II',
        _('Clinical Trial, Phase III'): 'clinical trial, phase III',
        _('Clinical Trial, Phase IV'): 'clinical trial, phase IV',
        _('Comment'): 'comment',
        _('Congresses'): 'congresses',
        _('Consensus Development Conference'): 'consensus development conference',
        _('Consensus Development Conference, NIH'): 'consensus development conference, NIH',
        _('Controlled Clinical Trial'): 'controlled clinical trial',
        _('Corrected and Republished Article'): 'corrected and republished article',
        _('Dictionary'): 'dictionary',
        _('Directory'): 'directory',
        _('Duplicate Publication'): 'duplicate publication',
        _('Editorial'): 'editorial',
        _('Evaluation Studies'): 'evaluation studies',
        _('Festschrift'): 'festschrift',
        _('Government Publications'): 'government publications',
        _('Guideline'): 'guideline',
        _('Historical Article'): 'historical article',
        _('Interview'): 'interview',
        _('Journal Article'): 'journal article',
        _('Lectures'): 'lectures',
        _('Legal Cases'): 'legal cases',
        _('Legislation'): 'legislation',
        _('Letter'): 'letter',
        _('Meta-Analysis'): 'meta-analysis',
        _('Multicenter Study'): 'multicenter study',
        _('News'): 'news',
        _('Newspaper Article'): 'newspaper article',
        _('Overall'): 'overall',
        _('Periodical Index'): 'periodical index',
        _('Practice Guideline'): 'practice guideline',
        _('Randomized Controlled Trial'): 'randomized controlled trial',
        _('Retraction of Publication'): 'retraction of publication',
        _('Retracted Publication'): 'retracted publication',
        _('Review'): 'review',
        _('Review, Academic'): 'review, academic',
        _('Review Literature'): 'review, literature',
        _('Review, Multicase'): 'review, multicase',
        _('Review of Reported Cases'): 'review of reported cases',
        _('Review, Tutorial'): 'review, tutorial',
        _('Scientific Integrity Review'): 'scientific integrity review',
        _('Technical Report'): 'technical report',
        _('Twin Study'): 'twin study',
        _('Validation Studies'): 'validation studies',
    }

    language = {
        _('English'): 'english',
        _('French'): 'french',
        _('German'): 'german',
        _('Italian'): 'italian',
        _('Japanese'): 'japanese',
        _('Russian'): 'russian',
        _('Spanish'): 'spanish',
    }

    age_range = {
        _('All Infant: birth-23 month'): 'infant',
        _('All Child: 0-18 years'): 'child',
        _('All Adult: 19+ years'): 'adult',
        _('Newborn: birth-1 month'): 'infant, newborn',
        _('Infant: 1-23 months'): 'infant',
        _('Preschool Child: 2-5 years'): 'child, preschool',
        _('Child: 6-12 years'): 'child',
        _('Adolescent: 13-18 years'): 'adolescence',
        _('Adult: 19-44 years'): 'adult',
        _('Middle Aged: 45-64 years'): 'middle age',
        _('Aged: 65+ years'): 'aged',
        _('80 and over: 80+ years'): 'aged, 80 and over',
    }

    human_animal = {
        _('Human'): 'human',
        _('Animal'): 'animal',
    }

    gender = {
        _('Female'): 'female',
        _('Male'): 'male',
    }

    subset = {
        _('Bioethics'): 'bioethics[ab]',

        _('Core clinical journals'): 'jsubsetaim', #AIM - Abridged Index Medicus A list of core clinical journals created 20 years ago 
        _('Biotechnology journals'): 'jsubsetb', #B -  biotechnology journals (assigned 1990 - 1998), non-Index Medicus
        _('Communication disorders journals'): 'jusbsetc', #C -  communication disorders journals (assigned 1977 - 1997), non-Index Medicus
        _('Dental journals'): 'jsubsetd', #D  -  dentistry journals 
        _('Bioethics journals'): 'jsubsete', #E -  bioethics journals, non-Index Medicus
        _('Health administration journals'): 'jsubseth', #H -  health administration journals, non-Index Medicus 
        _('Index Medicus journals'): 'jsubsetim', #IM -  Index Medicus journals 
        _('Consumer health journals'): 'jsubsetk', #K -  consumer health journals, non-Index Medicus 
        _('Nursing journals'): 'jsubsetn', #N  -  nursing journals 
        _('History of Medicine journals'): 'jsubsetq', #Q -  history of medicine journals, non-Index Medicus 
        _('Reproduction journals'): 'jsubsetr', #R -  reproduction journals (assigned 1972 - 1979), non-Index Medicus
        _('NASA journals'): 'jsubsets', #S -  National Aeronautics and Space Administration (NASA) journals, non-Index Medicus 
        _('Health tech assesment journals'): 'jsubsett',#T -  health technology assessment journals, non-Index Medicus 
        _('AIDS/HIV journals'): 'jsubsetx', #X -  AIDS/HIV journals, non-Index Medicus 
    
        _('AIDS'): 'aids[sb]',
        _('Complementary and Alternative Medicine'): 'cam[sb]',
        _('History of Medicine'): 'history[sb]',
        _('In process'): 'in process[sb]',
        _('MEDLINE'): 'medline[sb]',
        _('PubMed Central'): 'medline pmc[sb]',
        _('Space Life Sciences'): 'space[sb]',
        _('Supplied by Publisher'): 'publisher[sb]',
        _('Toxicology'): 'tox[sb]',
    }
    
    def makeQuery(self, keyword=None, abstract=False, epubahead=False,
                  publication_type=None, language=None, subset=None,
                  age_range=None, human_animal=None, gender=None,
                  use_publication_date=False, from_date=None,
                  to_date=None):
        
        """Compose an advanced query.

        'field' is a single value from self.fields.
        'publication_type' is a single value from self.publication_types, or None.
        'language' is from self.language or None
        'subset' is from self.subset or None
        'age_range' is from self.age_range or None
        'human_animal' is from self.human_animal or None
        'gender' is from self.gender or None

        If use_publication_date is True, select publications whose
        publication date is between from_date and to_date, otherwise
        use the entrez date.
        
        Args:
          keyword: string
          abstract: bool
          epubahead: bool
          publication_type: string or None
          language: string or None
          subset: string or None
          age_range: string or None
          human_animal: string or None
          gender: string or None
          pubdate: bool
          from_date: datetime.date() or None
          to_date: datetime.date() or None
        """

        parts = []
        if keyword is not None:
            parts.append(keyword)
        if abstract:
            parts.append('hasabstract')
        if epubahead:
            parts.append('pubstatusaheadofprint')
        if publication_type:
            parts.append(pubtype + '[pt]')
        if language:
            parts.append(language + '[la]')
        if subset:
            parts.append(subset)
        if age_range:
            parts.append(agerange + '[mh]')
        if human_animal:
            parts.append(humananimal + '[mh]')
        if gender:
            parts.append(gender + '[mh]')

        if from_date:
            if not to_date:
                to_date = datetime.date.today()
            date = ':'.join([from_date.strftime('%Y/%m/%d'),
                             to_date.strftime('%Y/%m/%d')])

            if use_publication_date:
                date += '[dp]'
            else:
                date += '[edat]'
            parts.append(date)

        keywords = ' AND '.join(parts)

        return keywords

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

        # ensure all arguments are utf8 encoded
        for k, v in all.items():
            if isinstance(v, unicode):
                all[k] = v.encode('utf-8')
                
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

        query = query.strip()
        
        data = {'db': db,
                'term': query}

        req = self._query(self.SRV_SEARCH, data, usehistory='y')

        # The deferred for the global result
        results = defer.Deferred()

        # The result set that will contain the data
        rs = self.db.rs.new()
        rs.name = _('Imported from PubMed')

        # Special case for no query: this would cause an error from
        # the server if we do not catch it first.
        if not query:
            def autofire():
                results.callback(0)

            reactor.callLater(0, autofire)
            return results, rs
        
        stats = {}

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
            
            stats['missing'] = min(all_results, maxhits)

            self.log.debug('%d results, retrieving %d' % (all_results, stats['missing']))

            def fetch(data):
                # data is None during the initial call to the method,
                # so that we can reuse the same code.
                if data is not None:
                    # Process the incoming XML data
                    previously = len(rs)
                    self.reader.parse(data, self.db, rs)
                    freshly_parsed = len(rs) - previously
                    if freshly_parsed <= 0:
                        self.log.warn("what happend? I increased the result set by %d" % freshly_parsed)
                        # pretend there has been at least one parsing, so
                        # that we ensure that the task
                        # progresses. Otherwise we might loop forever on
                        # an entry we cannot parse.
                        freshly_parsed = 1

                    stats['missing'] -= freshly_parsed
                
                if stats['missing'] <= 0:
                    results.callback(all_results)
                    return

                # No need to fetch 500 results if only 20 are requested
                batch = min(self.BATCH_SIZE, stats['missing'])
                
                d = self._query(self.SRV_FETCH, fetchdata,
                                retstart=len(rs), retmax=batch)
            
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
