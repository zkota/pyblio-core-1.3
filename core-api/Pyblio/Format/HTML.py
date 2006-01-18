from xml.sax.saxutils import escape

def generate (t):
    if isinstance (t, (str, unicode)): return escape (t)
    return _map [t.tag] (t)
    
def _do_t (t):
    return ''.join (map (generate, t.children))

def _do_i (t):
    return '<i>' + ''.join (map (generate, t.children)) + '</i>'
    
def _do_b (t):
    return '<b>' + ''.join (map (generate, t.children)) + '</b>'
    
def _do_a (t):
    attrs = ' '.join ([ '%s="%s"' % (k, v) for k, v in t.attributes.items () ])
    return '<a %s>' % attrs + ''.join (map (generate, t.children)) + '</a>'

def _do_br (t):
    return '<br>'
    

_map = {
    't' : _do_t,
    'i' : _do_i,
    'b' : _do_b,
    'a' : _do_a,
    'br': _do_br,
    }


