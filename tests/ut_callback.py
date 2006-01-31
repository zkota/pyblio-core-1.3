
import pybut


class Bound(object):

    def __init__(self):
        self.count = []
        
    def bound(self, x):
        self.count.append(x)

from Pyblio.Callback import Publisher

class Publish(Publisher):
    pass


class TestCallback(pybut.TestCase):

    def testFunction(self):
        count = []

        def free_function(x):
            count.append(x)
        
        p = Publish()
        p.register('yorgl', free_function, '1234')

        # Check that emitting works
        p.emit('yorgl')
        assert count == ['1234']

        # Check that we can unregister our function
        p.unregister('yorgl', free_function)

        p.emit('yorgl')
        assert count == ['1234'], count

    def testMethod(self):
        o = Bound()
        
        p = Publish()
        p.register('yorgl', o.bound, '1234')

        # Check that emitting works
        p.emit('yorgl')
        assert o.count == ['1234']

        # Check that we can unregister our function
        p.unregister('yorgl', o.bound)

        p.emit('yorgl')
        assert o.count == ['1234']

        
suite = pybut.suite(TestCallback)
if __name__ == '__main__':  pybut.run (suite)
