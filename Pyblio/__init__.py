"""
A framework for manipulating bibliographic databases.

Definitions
===========

A database is a set of L{Records <Pyblio.Store.Record>}, which
contains B{typed} L{Attributes <Pyblio.Attribute>}. The definition of
the available attributes is done in a L{Schema <Pyblio.Schema>}, which
provides names, types and textual description of the fields.

Getting started
===============

To create, open and start filling a databases, check the
L{Pyblio.Store} module.

"""

import logging

_base = logging.getLogger('pyblio')
_hdlr = logging.StreamHandler()

_fmtr = logging.Formatter('Pyblio[%(levelname)s]: %(message)s')
_hdlr.setFormatter(_fmtr)

_base.addHandler(_hdlr)
