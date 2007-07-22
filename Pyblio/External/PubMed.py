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

    query_fields = {
        'ALL': _('All Fields'),
        'AD': _('Affiliation'),
        'AU': _('Author Name'),
        'RN': _('EC/RN Number'),
        'EDAT': _('Entrez Date'),
        'FILTER': _('Filter'),
        'IP': _('Issue'),
        'TA': _('Journal Title'),
        'LA': _('Language'),
        'MHDA': _('MeSH Date'),
        'MAJR': _('MeSH Major Topic'),
        'SH': _('MeSH Subheading'),
        'MH': _('MeSH Terms'),
        'PG': _('Pagination'),
        'DP': _('Publication Date'),
        'PT': _('Publication Type'),
        'SI': _('Secondary Source ID'),
        'NM': _('Substance Name'),
        'TW': _('Text Word'),
        'TI': _('Title'),
        'TIAB': _('Title/Abstract'),
        'PMID': _('UID'),
        'VI': _('Volume'),
        }
    publication_types = {
        'addresses': _('Addresses'),
        'bibliography': _('Bibliography'),
        'biography': _('Biography'),
        'classical article': _('Classical Article'),
        'clinical conference': _('Clinical Conference'),
        'clinical trial': _('Clinical Trial'),
        'clinical trial, phase I': _('Clinical Trial, Phase I'),
        'clinical trial, phase II': _('Clinical Trial, Phase II'),
        'clinical trial, phase III': _('Clinical Trial, Phase III'),
        'clinical trial, phase IV': _('Clinical Trial, Phase IV'),
        'comment': _('Comment'),
        'congresses': _('Congresses'),
        'consensus development conference': _('Consensus Development Conference'),
        'consensus development conference, NIH': _('Consensus Development Conference, NIH'),
        'controlled clinical trial': _('Controlled Clinical Trial'),
        'corrected and republished article': _('Corrected and Republished Article'),
        'dictionary': _('Dictionary'),
        'directory': _('Directory'),
        'duplicate publication': _('Duplicate Publication'),
        'editorial': _('Editorial'),
        'evaluation studies': _('Evaluation Studies'),
        'festschrift': _('Festschrift'),
        'government publications': _('Government Publications'),
        'guideline': _('Guideline'),
        'historical article': _('Historical Article'),
        'interview': _('Interview'),
        'journal article': _('Journal Article'),
        'lectures': _('Lectures'),
        'legal cases': _('Legal Cases'),
        'legislation': _('Legislation'),
        'letter': _('Letter'),
        'meta-analysis': _('Meta-Analysis'),
        'multicenter study': _('Multicenter Study'),
        'news': _('News'),
        'newspaper article': _('Newspaper Article'),
        'overall': _('Overall'),
        'periodical index': _('Periodical Index'),
        'practice guideline': _('Practice Guideline'),
        'randomized controlled trial': _('Randomized Controlled Trial'),
        'retraction of publication': _('Retraction of Publication'),
        'retracted publication': _('Retracted Publication'),
        'review': _('Review'),
        'review, academic': _('Review, Academic'),
        'review, literature': _('Review Literature'),
        'review, multicase': _('Review, Multicase'),
        'review of reported cases': _('Review of Reported Cases'),
        'review, tutorial': _('Review, Tutorial'),
        'scientific integrity review': _('Scientific Integrity Review'),
        'technical report': _('Technical Report'),
        'twin study': _('Twin Study'),
        'validation studies': _('Validation Studies'),
    }

    language = {
        'english': _('English'),
        'french': _('French'),
        'german': _('German'),
        'italian': _('Italian'),
        'japanese': _('Japanese'),
        'russian': _('Russian'),
        'spanish': _('Spanish'),
    }

    age_range = [
        ('infant', _('All Infant (birth-23 month)')),
        ('child', _('All Child (0-18 years)')),
        ('adult', _('All Adult (19+ years)')),
        ('infant, newborn', _('Newborn (birth-1 month)')),
        ('infant', _('Infant (1-23 months)')),
        ('child, preschool', _('Preschool Child (2-5 years)')),
        ('child', _('Child (6-12 years)')),
        ('adolescence', _('Adolescent (13-18 years)')),
        ('adult', _('Adult (19-44 years)')),
        ('middle age', _('Middle Aged (45-64 years)')),
        ('aged', _('Aged (65+ years)')),
        ('aged, 80 and over', _('80 and over')),
    ]

    human_animal = {
        'human': _('Human'),
        'animal': _('Animal'),
    }

    gender = {
        'female': _('Female'),
        'male': _('Male'),
    }

    subset = {
        'bioethics[ab]': _('Bioethics'),

        'jsubsetaim': _('Core clinical journals'), #AIM - Abridged Index Medicus A list of core clinical journals created 20 years ago 
        'jsubsetb': _('Biotechnology journals'), #B -  biotechnology journals (assigned 1990 - 1998), non-Index Medicus
        'jusbsetc': _('Communication disorders journals'), #C -  communication disorders journals (assigned 1977 - 1997), non-Index Medicus
        'jsubsetd': _('Dental journals'), #D  -  dentistry journals 
        'jsubsete': _('Bioethics journals'), #E -  bioethics journals, non-Index Medicus
        'jsubseth': _('Health administration journals'), #H -  health administration journals, non-Index Medicus 
        'jsubsetim': _('Index Medicus journals'), #IM -  Index Medicus journals 
        'jsubsetk': _('Consumer health journals'), #K -  consumer health journals, non-Index Medicus 
        'jsubsetn': _('Nursing journals'), #N  -  nursing journals 
        'jsubsetq': _('History of Medicine journals'), #Q -  history of medicine journals, non-Index Medicus 
        'jsubsetr': _('Reproduction journals'), #R -  reproduction journals (assigned 1972 - 1979), non-Index Medicus
        'jsubsets': _('NASA journals'), #S -  National Aeronautics and Space Administration (NASA) journals, non-Index Medicus 
        'jsubsett': _('Health tech assesment journals'), #T -  health technology assessment journals, non-Index Medicus 
        'jsubsetx': _('AIDS/HIV journals'), #X -  AIDS/HIV journals, non-Index Medicus 
    
        'aids[sb]': _('AIDS'),
        'cam[sb]': _('Complementary and Alternative Medicine'),
        'history[sb]': _('History of Medicine'),
        'in process[sb]': _('In process'),
        'medline[sb]': _('MEDLINE'),
        'medline pmc[sb]': _('PubMed Central'),
        'space[sb]': _('Space Life Sciences'),
        'publisher[sb]': _('Supplied by Publisher'),
        'tox[sb]': _('Toxicology'),
    }
    
    def makeQuery(self, field='ALL', keyword=None, abstract=False,
                  epubahead=False, publication_type=None,
                  language=None, subset=None, age_range=None,
                  human_animal=None, gender=None,
                  use_publication_date=False, from_date=None,
                  to_date=None):
        
        """Compose an advanced query.

        'field' is a single value from self.query_fields.
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
          field: string
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
            parts.append(keyword + '[%s]' % field)
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
            parts.append(age_range + '[mh]')
        if human_animal:
            parts.append(human_animal + '[mh]')
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

    schema = 'org.pybliographer/pubmed/0.1'

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

            self.log.info('%d results, retrieving %d' % (
                all_results, stats['missing']))

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
                    self.log.info('finished')
                    results.callback(all_results)
                    return

                # No need to fetch 500 results if only 20 are requested
                batch = min(self.BATCH_SIZE, stats['missing'])
                self.log.info('retrieving next %d' % batch)
                
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
