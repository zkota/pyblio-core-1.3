import os, stat, sys

from distutils.core import setup

version = "0.1"

setup (name = "pybliographer-core",
       version = version,

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
