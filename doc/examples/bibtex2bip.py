"""
Parse a BibTeX file into a BIP (a native pybliographer database) file.

Usage: bibtex2bip.py <BibTeX file> <BIP file>
"""

import sys, os

in_f, out_f = sys.argv[1:3]

from Pyblio.Parsers.Semantic import BibTeX
from Pyblio import Store, Registry

Registry.parse_default()

# This id refers to the bibtex format as known by pybliographer by
# default.
sid = "org.pybliographer/bibtex/0.1"

# Get the schema associated with the specified id
schema = Registry.getSchema(sid)

# Create a new db using this schema. We need to ensure the file does
# not exist yet.
try: os.unlink(out_f)
except OSError: pass

db = Store.get('file').dbcreate(out_f, schema)

# Import the content of the bibtex file into it
fd = open(in_f)

reader = BibTeX.Reader()
reader.parse(fd, db)

db.save()
