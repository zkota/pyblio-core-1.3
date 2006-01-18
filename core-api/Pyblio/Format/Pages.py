import re

from Pyblio.Format.DSL import lazy

def _pagesLong (record, pages):

    pages = pages(record)
    
    if pages.find ('-') == -1:
        # no dash, a single page then
        return u'page\xa0' + pages
    else:
        return u'pages\xa0' + pages

pagesLong = lazy (_pagesLong)
