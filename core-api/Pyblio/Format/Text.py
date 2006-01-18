
def generate (t):
    if isinstance (t, (str, unicode)): return t
    return _map [t.tag] (t)
    
def _do_t (t):
    return ''.join (map (generate, t.children))

def _do_a (t):
    return '%s <%s>' % (''.join (map (generate, t.children)),
                        t.attributes ['href'])

def _do_br (t):
    return '\n'
    

_map = {
    't' : _do_t,
    'i' : _do_t,
    'b' : _do_t,
    'a' : _do_a,
    'br': _do_br,
    }


