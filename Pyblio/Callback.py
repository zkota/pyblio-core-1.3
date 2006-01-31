"""
A generic callback mechanism.

Classes that wish to emit events inherit from L{Publisher}. Interested
clients call the L{Publisher.register} method on the object. The
publisher then calls L{Publisher.emit} to emit the event."""

import weakref


class WeakError (Exception):
    """ Invoked when a function call is performed on a destroyed method """
    pass


class WeakMethodBound :

    """ A weak reference on a bound method """
    
    def __init__ (self, f):

        # Keep a hard reference on the function itself
        self.f = f.im_func
        self.c = weakref.ref(f.im_self)
        return

    
    def __call__ (self , *arg):

        o = self.c()
        
        if o is None:
            raise WeakError, 'Method called on dead object'
        
        return apply (self.f, (o,) + arg)

    def same(self, fn):

        try:
            rf = fn.im_func
        except AttributeError:
            return False
        
        return self.f is rf and self.c() is fn.im_self


class WeakMethodFree:

    """ A weak reference on an unbound method """
    
    def __init__ (self, f):
        self.f = weakref.ref(f)
        return
    
    def __call__ (self, *arg):
        o = self.f()
        
        if o is None :
            raise WeakError , 'Function no longer exist'
        
        return apply(o, arg)

    def same(self, fn):
        return self.f() is fn


def weakmethod (f):
    
    try: f.im_func
    
    except AttributeError:
        return WeakMethodFree(f)
    
    return WeakMethodBound(f)


class Publisher (object):

    """ Base class for objects that wish to emit signals to registered
    clients."""

    
    def __init__ (self):
        """ Intialize the publisher """
        
        self.__observers = {}
        return
    

    def emit(self, signal, *args):

        """ Call this method to emit a signal. Registered client will
        have their callbacks automatically invoked, with the specified
        arguments """
        
        try:
            queue = self.__observers[signal]
            
        except KeyError:
            return

        for data in queue[:]:

            cb, bound = data

            try:
                apply (cb, args + bound)
                
            except WeakError:
                queue.remove (data)
                continue

        return
    

    def register(self, signal, callback, *args):

        """ Clients interested in a given signal must register with
        this method. The optional args are passed as the last
        arguments (after the emit arguments) to the callback. """
        
        queue = self.__observers.setdefault(signal, [])
        queue.append((weakmethod(callback), args))
        return

    def unregister(self, signal, callback):
        """ Stop notifying events for the specified signal/callback
        pair."""

        queue = self.__observers.get(signal,[])

        for data in queue[:]:
            cb, bound = data

            if cb.same(callback):
                queue.remove(data)

        return
