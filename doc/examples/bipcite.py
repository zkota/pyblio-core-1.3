"""
Cite the references contained in a pybliographer database (a bip
file).

Usage: bipcite.py <BIP file> <output>

If <output> is the string 'OOo', try to cite in a running OpenOffice
document. If it is 'LyX', it connects to a running instance of
Lyx. Otherwise, cite into the specified file, in HTML.

OpenOffice must be started with the following option:

   oowriter '-accept=socket,host=localhost,port=2002;urp;'

LyX must be configured to create named pipes called:

   ~/.lyx/lyxpipe.in
   ~/.lyx/lyxpipe.out
   
"""

import sys, os

from Pyblio import Store, Sort

# Read the database passed as argument to the script
in_f, ou_f = sys.argv[1:3]

db = Store.get('file').dbopen(in_f)

# Check that the bip file actually uses the expected schema
assert db.schema.id == "org.pybliographer/bibtex/0.1"

# Load a standard citation definition, as an XML file. This defines
# the citation of the references, the key and the ordering of the
# bibliography.
from Pyblio.Cite.Citator import Citator
from Pyblio import Registry

citator = Citator()
citator.xmlload(os.path.join(Registry.RIP_dirs['system'], 'unsrt.cip'))

# Citations are inserted in word processors. For the purpose of this
# example, we use either a "virtual word processor" that helps writing
# citations to a simple file, or the actual OpenOffice interface.
if ou_f == 'OOo':
    # Connect to OpenOffice
    from Pyblio.Cite.WP.OpenOffice import OOo

    wp = OOo()
    wp.connect()

elif ou_f == 'LyX':
    from Pyblio.Cite.WP.LyX import LyX

    wp = LyX()
    wp.connect()
    
else:
    # Connect to a file
    from Pyblio.Cite.WP.File import File

    import codecs
    output = codecs.open(ou_f, 'w', encoding='utf-8')

    wp = File(output)

# We can now connect our database to the document in which we will
# cite the records.
citator.prepare(db, wp)

# "cite" the references in our document, arbitrarily using the
# chronological order.
view = db.entries.view(Sort.OrderBy('date', asc=False))
for k in view.iterkeys():
    citator.cite([k])

# ...and ask for an update of the bibliography, which will actually
# write the file.
citator.update()
