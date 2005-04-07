"""
Definition of the base mechanisms providing the formatting domain
specific language:

 - join ()
 - access ()


 - lazy ()
 - Maybe 

"""


class Missing (KeyError): pass


class Maybe (object):

    def __add__ (self, other):
        return Sum (self, other)

    def __radd__ (self, other):
        return Sum (T (other), self)

    def __or__ (self, other):
        return Or (self, other)
    
    def __ror__ (self, other):
        return Or (T (other), self)
    

class Sum (Maybe):

    def __init__ (self, a, b):
        if isinstance (b, (str, unicode)): b = T (b)

        self.a = a
        self.b = b
        return

    def __call__ (self):
        return self.a () + self.b ()

class Or (Maybe):

    def __init__ (self, a, b):
        if isinstance (b, (str, unicode)): b = T (b)
        
        self.a = a
        self.b = b
        return

    def __call__ (self):
        try: return self.a ()
        except Missing: return self.b ()


class T (Maybe):

    def __init__ (self, t):
        self.t = t
        return

    def __call__ (self):
        return self.t
    


class join (object):

    def __init__ (self, middle, last = None):

        self.middle = middle
        self.last   = last or middle

    def __getitem__ (self, children):
        
        if not isinstance (children, (list, tuple)):
            children = [ children ]

        class _join (Maybe):

            def __init__ (self, middle, last):
                self.middle = middle
                self.last   = last
                return
            
            def __call__ (self):
                ls = []
                    
                for arg in children:
                    if isinstance (arg, (str, unicode)):
                        ls.append (arg)
                        continue
                    
                    try: v = arg ()
                    except Missing: continue

                    if isinstance (v, (list, tuple)):
                        ls += v
                    else: ls.append (v)

                if len (ls) == 0: raise Missing ('empty join')

                r = ls.pop (0)
                while ls:
                    l = ls.pop (0)
                    if ls: r += self.middle
                    else:  r += self.last

                    r += l

                return r
                
        return _join (self.middle, self.last)


def access (record):

    """ Return two accessors (all, one) for the specified record:

      - all (field) : return all the values for the field

      - one (field) : return a single value for the field
    """

    
    class accessor (Maybe):
        def __init__ (self, field):
            self._f = field

            
    class all (accessor):
        def __call__ (self):
            try:
                v = record [self._f]
            except KeyError, msg:
                raise Missing ('no field %s in record' % repr (self._f))
            
            if not v:
                raise Missing ('no field %s in record' % repr (self._f))
            
            return v
        
    class one (accessor):
        def __call__ (self):
            try: return record [self._f] [0]
            except (KeyError, IndexError), msg:
                raise Missing ('no field %s in record' % repr (self._f))


    return all, one


def lazy (fn):

    """ Transform a simple function into a lazy function lifted in the
    Maybe monad.

    This is only sugar : the initial function must be aware that every
    argument must be made strict by calling them before use.

    """

    class _caller (Maybe):

        def __init__ (self, * args, ** kargs):
            self.__args  = args
            self.__kargs = kargs
            
        def __call__ (self):
            return fn (* self.__args, ** self.__kargs)

    return _caller

