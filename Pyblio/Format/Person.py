import re

from Pyblio.Format.DSL import lazy


def maybe (value, prefix = '', postfix = '', default = ''):
    if value: return prefix + value + postfix
    return default

def _lastFirst(record, authors):
    return [ '%s%s' % (x.last, maybe (x.first, prefix = ', '))
             for x in authors(record) ]
    
lastFirst = lazy (_lastFirst)

def _firstLast (record, authors):
    return [ '%s%s' % (maybe (x.first, postfix = ' '), x.last)
             for x in authors(record) ]

firstLast = lazy (_firstLast)

_ini_re = re.compile (r'([.-]|\s+)')

def initials (name):
    """ Normalizes a first name as an initial """

    if not name:
        return None

    # if the name is full upper, we assume it is already the
    # contracted initials form.
    if name.upper() == name and len(name) < 4:
        return '.'.join(name) + '.'
    
    res = []
    
    for p in _ini_re.split (name):
        if not p.strip () or p == '.': continue

        if p != '-': p = p [0] + '.'

        res.append (p)
        
    return ''.join (res)
    
def _initialLast (record, authors):
    return [ '%s%s' % (maybe (initials (x.first), postfix = ' '), x.last)
             for x in authors(record) ]

initialLast = lazy (_initialLast)
    
