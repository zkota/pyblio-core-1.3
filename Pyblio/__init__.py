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

_inited = False

def init_logging(filename=None):
    global _inited
    if _inited:
        return
    _inited = True

    _base = logging.getLogger('pyblio')
    if filename is None:
        log_handler = logging.StreamHandler()
    else:
        from logging.handlers import RotatingFileHandler
        log_handler = RotatingFileHandler(filename, maxBytes=10 * 2**20,
                                          backupCount=5)

    _fmtr = logging.Formatter('%(name)s(%(filename)s) [%(levelname)s]: %(message)s')
    log_handler.setFormatter(_fmtr)
    
    _base.addHandler(log_handler)
