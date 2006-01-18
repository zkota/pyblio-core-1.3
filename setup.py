# -*- coding: utf-8 -*-
import os, stat, sys

try:
   from ez_setup import use_setuptools
   use_setuptools()
except ImportError:
   pass

def version_get ():

    full = os.popen ('tla logs -r -f 2> /dev/null').read ().split ('\n') [0].strip ()

    if full == '': return None, None

    vid = full.split ('/') [1].split ('--')
    numerical = '%s.%s' % (vid [2], vid [3].split ('-') [1])

    return full, numerical

version, vid = version_get ()

if version:
    print 'running setup on version %s [%s]' % (version, vid)

from setuptools import setup, find_packages

setup(
    name = "pybliographer",
    version = vid,
    packages = find_packages(),

    package_data = {
    'Pyblio': ['RIP/*.xml', 'RIP/*.rip'],
    },

    author = "Frédéric Gobry",
    author_email = "gobry@pybliographer.org",
    
    description = "pybliographer core API",
    
    license = "LGPL",
)

