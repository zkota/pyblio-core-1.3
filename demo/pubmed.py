from StringIO import StringIO

from nevow import rend, loaders, stan
from nevow.inevow import IRequest

from nevow import tags as T

from Pyblio import Store, Registry, Adapter
from Pyblio.External import PubMed
from Pyblio.Parsers.Semantic.BibTeX import Writer

Registry.parse_default()

# This will output the database in BibTeX format
w = Writer()


# Define a simple citation format
from Pyblio.Format import one, all, join, switch, I, B, A
from Pyblio.Format import Person, Date
from Pyblio.Format.HTML import generate

title = B[one('title') | u'(no title)']

title = A(href=one('url'))[title] | title

authors = join(', ', last=' and ')[Person.initialLast(all('author'))]

article = join(u', ')[
    I[one('journal')],
    
    u'vol. ' + one('volume'),
    u'nr. '  + one('number'),
    u'pp. '  + one('pages'),
    
    Date.year(one('date'))
    ]

default = Date.year(one('date'))

place = switch('doctype')

place = place.case(article=article)
place = place.default(default)

citation = join(u', ')[authors, title, place] + '.'



class Page(rend.Page):
    
    docFactory = loaders.xmlfile('pubmed.xml')

    def render_query(self, ctx, data):
        query = IRequest(ctx).args.get('q', [''])[0]
        
        return ctx.tag(value=query)

    def data_results(self, ctx, data):
        query = IRequest(ctx).args.get('q', None)
        if query is None:
            return None

        query = query[0]
        
        s = Registry.getSchema('org.pybliographer/pubmed/0.1')
        db = Store.get('memory').dbcreate(None, s)

        remote = PubMed.PubMed(db)
        d, rs = remote.search(query, maxhits=20)

        def success(total):
            bibtex = Adapter.adapt_schema(db, 'org.pybliographer/bibtex/0.1')
            return True, query, bibtex

        def failure(failure):
            return False, query, failure

        d.addCallback(success).addErrback(failure)
        
        return d

    def render_results(self, ctx, data):
        if data is None:
            return ctx.tag

        success, query, db = data

        if not success:
            ctx.tag[T.h1[u'Failed to process query %s' % query]]
            ctx.tag[T.pre[str(db)]]

            return ctx.tag
        
        ctx.tag[T.h1[u'%d results for query "%s"' % (
            len(db.entries), query)]]

        # Cite the records
        formatter = citation(db)

        cited = T.ul[[T.li[stan.xml(generate(formatter(record)))]
                      for record in db.entries.itervalues()]]

        ctx.tag[cited]

        # Display the raw BibTeX too
        res = StringIO()
        w.write(res, db.entries, db)

        res = res.getvalue().decode('utf-8')
        ctx.tag[T.pre[res]]
    
        return ctx.tag
    
