"""
Format the records contained in a pybliographer database (a bip file)
and insert them in an open OpenOffice document.

You need to start openoffice with the following options:

   oowriter '-accept=socket,host=localhost,port=2002;urp;'

Usage: bip2ooo.py <BIP file>
"""

import sys

from Pyblio import Store

# Read the database passed as argument to the script
in_f = sys.argv[1]

db = Store.get('file').dbopen(in_f)

# Check that the bip file actually uses the expected schema

assert db.schema.id == "org.pybliographer/bibtex/0.1"

# Define the citation format using pyblio's domain specific language

from Pyblio.Format import one, all, join, switch, I, B, A
from Pyblio.Format import Person, Date


# title is either the title attribute, or the string "(no title)"
title = B[one('title') | u'(no title)']

# if there is an URL available, make the title clickable
title = A(href=one('url'))[title] | title

# To generate the list of authors, take all the elements in the
# 'author' attribute, pass them to a formatter that returns the names
# as "Initials Last_Name", and bind them together with commas as
# separators, except between the last two authors, which are separated
# by the word 'and'.

authors = join(', ', last=' and ')[Person.initialLast(all('author'))]

# Information about where the document was published. We display the
# journal name in italics, and append the volume, number and pages
# information. Fields are separated by commas.

article = join(u', ')[
    I[one('journal')],
    
    u'vol. ' + one('volume'),
    u'nr. '  + one('number'),
    u'pp. '  + one('pages'),
    
    Date.year(one('date'))
    ]

# For non-articles, just provide the date.
default = Date.year(one('date'))

# Depending on the document type, we select a specific layout. This
# code only handles the case of an article, simply add other
# place.case(...) statements for the document types you wish to
# verride.

place = switch('doctype')

place = place.case(article=article)
place = place.default(default)

# Bind everything together.
citation = join(u', ')[authors, title, place] + '.'

# Now, we can 'compile' our citation formatter to use the specified
# schema.
formatter = citation(db)

# Display the content of the database in HTML, ordered by decreasing
# publication date.
from Pyblio import Sort
from Pyblio.Format.OpenOffice import Generator
from Pyblio.Cite.WP.OpenOffice import OOo

view = db.entries.view(Sort.OrderBy('date', asc=False))

# Hopefully connect to openoffice
oo = OOo()
oo.connect()

generate = oo.update_biblio()

for record in view.itervalues():
    generate(formatter(record))
    generate.do_br(None)
    
