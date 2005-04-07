from Pyblio.Format.DSL import lazy


def _lastFirst (authors):
        return [ '%s, %s' % (x.last, x.first) for x in authors () ]
    
lastFirst = lazy (_lastFirst)

def _firstLast (authors):
    return [ '%s %s' % (x.first, x.last) for x in authors () ]

firstLast = lazy (_firstLast)
