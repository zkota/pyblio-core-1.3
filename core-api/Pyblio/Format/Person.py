import re

from Pyblio.Format.DSL import lazy


def maybe (value, prefix = '', postfix = '', default = ''):
    if value: return prefix + value + postfix
    return default

def _lastFirst (authors):
    return [ '%s%s' % (x.last, maybe (x.first, prefix = ', '))
             for x in authors () ]
    
lastFirst = lazy (_lastFirst)

def _firstLast (authors):
    return [ '%s%s' % (maybe (x.first, postfix = ' '), x.last)
             for x in authors () ]

firstLast = lazy (_firstLast)

_ini_re = re.compile (r'([.-]|\s+)')

def initials (name):
    """ Normalizes a first name as an initial """

    if not name: return None
    
    res = []
    
    for p in _ini_re.split (name):
        if not p.strip () or p == '.': continue

        if p != '-': p = p [0] + '.'

        res.append (p)
        
    return ''.join (res)
    
def _initialLast (authors):
    return [ '%s%s' % (maybe (initials (x.first), postfix = ' '), x.last)
             for x in authors () ]

initialLast = lazy (_initialLast)
    
