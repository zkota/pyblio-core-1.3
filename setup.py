# -*- coding: utf-8 -*-

NAME = 'pyblio-core'

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from Pyblio import version as VERSION

print "setup for %s-%s" % (NAME, VERSION)

try:
   from ez_setup import use_setuptools
   use_setuptools()
except ImportError:
   pass

from setuptools import setup, find_packages
from setuptools.command.sdist import sdist as _sdist

class sdist(_sdist):
    def run(self):
       # Recompile the doc if possible
       import os, sys

       print >> sys.stderr, "sdist: regenerating the documentation"
       r = os.system('epydoc -n "%s %s" -o doc/reference Pyblio' % (NAME, VERSION))
       
       assert r == 0, 'unable to regenerate the documentation, please install "epydoc"'
       
       return _sdist.run(self)


setup(
    name = NAME,
    version = VERSION,

    cmdclass = { 'sdist': sdist },

    # First, I need to find out how to properly handle the case of
    # modules being installed externally (via debs or rpms for
    # instance).
    #
    # install_requires = ['elementtree', 'cElementTree'],
    
    packages = find_packages(),

    package_data = {
    'Pyblio': ['RIP/*.sip', 'RIP/*.rip', 'RIP/*.cip'],
    },

    author = "Frédéric Gobry",
    author_email = "gobry@pybliographer.org",

    url = 'http://pybliographer.org/',
    
    description = "pybliographer base package",

    long_description = """\
Pybliographer is a bibliographic database management toolkit. This
core package is a framework on which you can easily build parsers for
multiple publication database formats, or extend existing parsers;
define citation formats; modify, search and sort bibliographic data.
""",
    
    license = "GPL",

    classifiers=[
   'Development Status :: 4 - Beta',
   'Intended Audience :: Developers',
   'Operating System :: MacOS :: MacOS X',
   'Operating System :: Microsoft :: Windows',
   'Operating System :: POSIX',
   'Programming Language :: Python'],
)

