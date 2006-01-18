# -*- coding: utf-8 -*-

try:
   from ez_setup import use_setuptools
   use_setuptools()
except ImportError:
   pass

from setuptools import setup, find_packages

setup(
    name = "pybliographic",
    version = "0.1",
    packages = find_packages(),
    install_requires = ['RuleDispatch', 'pybliographer>=1.3'],

    package_data = {
    'PyblioUI.Gnome': ['Glade/*.glade'],
    },

    scripts = ['pybliographic'],

    author = "Frédéric Gobry",
    author_email = "gobry@pybliographer.org",
    
    description = "Graphical interface for pybliographer",
    license = "PSF",
    keywords = "hello world example examples",
    url = "http://example.com/HelloWorld/",   # project home page, if any

    
)
