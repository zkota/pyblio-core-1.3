import os, stat, sys

from distutils.core import setup

def version_get ():

    full = os.popen ('tla logs -r -f 2> /dev/null').read ().split ('\n') [0].strip ()

    if full == '': return None, None

    vid = full.split ('/') [1].split ('--')
    numerical = '%s.%s' % (vid [2], vid [3].split ('-') [1])

    return full, numerical

version, vid = version_get ()

if version:
    print 'running setup on version %s [%s]' % (version, vid)

setup (name = "pybliographer-core",
       version = vid,

       description = "Pybliographer Core API",
       author = "Frederic Gobry",
       author_email = 'gobry@pybliographer.org',
       url = 'http://pybliographer.org/',

       license = 'GPL',
       
       long_description = \
'''
This module contains the core API of Pybliographer.
''',

       packages = [ 'Pyblio',
                    'Pyblio.Importers',
                    'Pyblio.Importers.BibTeX',
                    'Pyblio.Format',
                    'Pyblio.Stores' ]
       )
