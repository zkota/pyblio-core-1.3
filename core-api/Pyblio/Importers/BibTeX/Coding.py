# -*- coding: utf-8 -*-

from Pyblio.Importers.BibTeX import Reader
from Pyblio import Exceptions

basemap = {
    "'": {
    'A': u"Á", 'E': u"É",
    'I': u"Í", 'O': u"Ó",
    'U': u"Ú", 'Y': u"Ý",
    'C': u"Ć", 'Z': u"Ź",
    'a': u"á", 'e': u"é",
    'i': u"í", 'o': u"ó",
    'u': u"ú", 'y': u"ý",
    'c': u"ć", 'z': u"ź",
    },
    
    "`": {
    'A': u"À", 'E': u"È",
    'I': u"Ì", 'O': u"Ò",
    'U': u"Ù",
    'a': u"à", 'e': u"è",
    'i': u"ì", 'o': u"ò",
    'u': u"ù",
    },
    
    "^": {
    'A': u"Â", 'E': u"Ê",
    'I': u"Î", 'O': u"Ô",
    'U': u"Û",
    'a': u"â", 'e': u"ê",
    'i': u"î", 'o': u"ô",
    'u': u"û",
    },

    '"': {
    'A': u"Ä", 'E': u"Ë",
    'I': u"Ï", 'O': u"Ö",
    'U': u"Ü",
    'a': u"ä", 'e': u"ë",
    'i': u"ï", 'o': u"ö",
    'u': u"ü", 'y': u"ÿ",
    },

    "c": {
    'C': u"Ç", 'c': u"ç",
    },

    
    "~": {
    'A': u"Ã", 'O': u"Õ",
    'a': u"ã", 'o': u"õ",
    'n': u"ñ", 'N': u"Ñ",
    },

}

def _accent (stack, cmd, tt):

    try:
        m = basemap [cmd]

    except KeyError:
        return Reader.Text ('?')
    
    if isinstance (tt, Reader.Text):

        if len (tt) > 1:
            t = tt [0]
            stack.insert (0, Reader.Text (tt [1:]))
        else:
            t = tt
            
    elif isinstance (tt, Reader.Block):
        t = tt._d [0]

        if isinstance (t, Reader.Text):
            pass

        elif isinstance (t, Reader.Cmd):
            # There are a few special cases where one wants to accent a command, like:
            #              \'{\i}
            if t._cmd == 'i':
                t = Reader.Text ('i')
            else:
                raise Exceptions.ParserError ('cannot evaluate expression %s' % repr ((cmd, tt)))

        else:
            raise Exceptions.ParserError ('cannot evaluate expression %s' % repr ((cmd, tt)))

    else:
        raise Exceptions.ParserError ('cannot evaluate expression %s' % repr ((cmd, tt)))

    try:
        return Reader.Text (m [t])
    except KeyError:
        raise KeyError ("cannot find %s in map %s" % (repr (t), repr (cmd)))


commands = {
    "'":  (_accent, 1),
    '`':  (_accent, 1),
    '^':  (_accent, 1),
    '"':  (_accent, 1),
    'c':  (_accent, 1),
    '~':  (_accent, 1),
    'ss': (u'ß', 0)
    }

class Environ (object):

    def run (self, cmd, stack):

        try:
            fn, count = commands [cmd]

        except KeyError:
            return Reader.Text (cmd)

        args = []
        
        while count:
            try:
                args.append (stack.pop (0))
            except IndexError:
                raise Exceptions.ParserError ('command %s requires %d arguments, got %s' % (
                    repr (cmd), count, len (args)))
            
            count -= 1
            
        if callable (fn):
            return fn (stack, cmd, * args)

        return Reader.Text (fn)
    
            
