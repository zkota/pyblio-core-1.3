
def generate (t):
    if isinstance (t, (str, unicode)): return t
    return _map [t.tagName] (t)
    
def _do_t (t):
    return ''.join (map (generate, t.children))

def _do_i (t):
    return '<i>' + ''.join (map (generate, t.children)) + '</i>'
    
def _do_b (t):
    return '<b>' + ''.join (map (generate, t.children)) + '</b>'
    
def _do_a (t):
    return '<a href="%s">' % (t.attributes ['href']) + ''.join (map (generate, t.children)) + '</a>'

def _do_br (t):
    return '<br>'
    

_map = {
    't' : _do_t,
    'i' : _do_i,
    'b' : _do_b,
    'a' : _do_a,
    'br': _do_br,
    }


