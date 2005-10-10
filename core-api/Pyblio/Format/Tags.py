"""
Domain specific language to format records.

Rationale: the difficult part in formatting the records is not how the
records are actually laid out on a page, the keys,... but rather the
actual layout of the authors, the publication information,...
especially given that all the records are not complete.

So, this stuff is only to format _this specific part_, not to compose
a whole page.


Heavily borrowed from nevow's stan.
"""

from Pyblio.Format import DSL

def _delayedstring (s):
    if isinstance (s, (str, unicode)): return DSL.T (s)
    return s

class Syntactic (object):
    
    def __init__ (self, tag):
        self.tagName = tag.lower ()
        self.attributes = {}

    def __call__(self, **kw):
        """Change attributes of this tag. This is implemented using
        __call__ because it then allows the natural syntax::
        
          A (href="http://...")

        """
        if not kw:
            return self

        for k, v in kw.iteritems():
            if k[-1] == '_':
                k = k[:-1]
            elif k[0] == '_':
                k = k[1:]
            self.attributes[k] = v
        return self
        
    def __getitem__ (self, children):
        if not isinstance(children, (list, tuple)):
            children = [children]

        children = map (_delayedstring, children)
        
        return Deferred (self.tagName, children, self.attributes)


class Deferred (DSL.Maybe):

    def __init__ (self, tag, children, attributes):

        self.tagName = tag
        self.children = children
        self.attributes = attributes
        
    def __call__ (self):
        return Semantic (self.tagName, 
                         [ x () for x in self.children ],
                         self.attributes)

class Semantic (object):

    def __init__ (self, tag, children, attributes):

        self.tagName = tag
        self.children = children
        self.attributes = attributes
        
    def __repr__(self):
        rstr = ''
        if self.attributes:
            rstr += ', attributes=%r' % self.attributes
        if self.children:
            rstr += ', children=%r' % self.children
        return "Tag(%r%s)" % (self.tagName, rstr)

    def __add__ (self, other):
        return Semantic ('t', [self, other], {})

    def __radd__ (self, other):
        return Semantic ('t', [other, self], {})


class Proto(str):
    """Proto is a string subclass. Instances of Proto, which are constructed
    with a string, will construct Tag instances in response to __call__
    and __getitem__, delegating responsibility to the tag.
    """
    __slots__ = []

    def __call__(self, **kw):
        return Syntactic(self)(**kw)

    def __getitem__(self, children):
        return Syntactic(self)[children]


glob = globals ()

for t in ('A', 'B', 'I', 'T'):
    glob [t] = Proto (t)

BR = Proto ('BR') ['']

