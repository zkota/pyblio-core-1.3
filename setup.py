# -*- coding: utf-8 -*-

VERSION = '1.3.1'

try:
   from ez_setup import use_setuptools
   use_setuptools()
except ImportError:
   pass

from setuptools import setup, find_packages

setup(
    name = "pybliographer",
    version = VERSION,
    packages = find_packages(),

    package_data = {
    'Pyblio': ['RIP/*.xml', 'RIP/*.rip'],
    },

    author = "Frédéric Gobry",
    author_email = "gobry@pybliographer.org",
    
    description = "pybliographer base package",

    long_description = """\
Pybliographer is a bibliographic database management toolkit. This
core package is a framework on which you can:

  - easily build parsers for multiple publication database formats, or
    extend existing parsers

  - define citation formats

  - modify / search / sort bibliographic data

""",
    
    license = "LGPL",
)

