import os, pybut, sys, string

from PyblioUI import Config


class TestConfig (pybut.TestCase):

    """ Test the PyblioUI.Config base functions """

    def setUp (self):

        self.cfg = Config.Storage ()
        return

    def testDomains (self):

        d = self.cfg.domains ()
        assert d == []

        for k in ('sample/toto', 'sample/tutu', 'gronf/toto'):
            self.cfg [k] = Config.Item ('', Config.String ())
            
        d = self.cfg.domains ()
        assert d == ['sample', 'gronf'], 'got %s' % `d`

        return

    def testDefine (self):

        try:
            self.cfg ['my/key']
            assert False, 'not to be reached'
            
        except KeyError: pass

        self.cfg ['my/key'] = Config.Item ('help', Config.String ())

        try:
            self.cfg ['my/key']

        except KeyError:
            assert 'should be defined'

        return

    def testSet (self):

        self.cfg ['my/key'] = Config.Item ('help', Config.String ())

        k = self.cfg ['my/key']
        
        assert k.value is None

        k.value = 'toto'

        assert self.cfg ['my/key'].value == 'toto'
        return

    def testKeys (self):

        assert self.cfg.keys () == []

        assert self.cfg.keys_in_domain ('sample') == []

        for k in ('sample/toto', 'sample/tutu', 'gronf/toto'):
            self.cfg [k] = Config.Item ('', Config.String ())

        r = self.cfg.keys_in_domain ('sample')
        r.sort ()
        
        assert  r == [ 'sample/toto', 'sample/tutu' ], \
               'got %s' % `r`

        return


class TestMatch (pybut.TestCase):

    """ Test the PyblioUI.Config value matching functions """

    def testString (self):

        k = Config.Item ('', Config.String ())
        
        k.value = 'toto'
        
        try:
            k.value = 1
            assert False, 'should not be accepted'
            
        except TypeError: pass

        return

    def testString (self):

        k = Config.Item ('', Config.Boolean ())
        
        k.value = True
        
        try:
            k.value = 1
            assert False, 'should not be accepted'
            
        except TypeError: pass

        return

    def testInteger (self):
        
        k = Config.Item ('', Config.Integer ())
        
        k.value = 1
        
        try:
            k.value = 'toto'
            assert False, 'should not be accepted'
            
        except TypeError: pass

        k = Config.Item ('', Config.Integer (min = 3))

        k.value = 3
        k.value = 4

        try:
            k.value = 2
            assert False, 'should not be accepted'
            
        except ValueError: pass

        
        k = Config.Item ('', Config.Integer (max = 3))

        k.value = 3
        k.value = 2

        try:
            k.value = 4
            assert False, 'should not be accepted'
            
        except ValueError: pass


        k = Config.Item ('', Config.Integer (min = 2, max = 4))

        k.value = 3
        k.value = 2
        k.value = 4

        try:
            k.value = 1
            assert False, 'should not be accepted'
            
        except ValueError: pass

        try:
            k.value = 5
            assert False, 'should not be accepted'
            
        except ValueError: pass
        return

    def testElementList (self):

        vs = [1, 2, 'a']
        
        k = Config.Item ('', Config.Element (vs))

        for v in vs:
            k.value = v

        try:
            k.value = 3
            assert False, 'not to be reached'
            
        except ValueError: pass

        return
    
    def testTuple (self):

        vs = [Config.Integer (max = 3), Config.String ()]
        
        k = Config.Item ('', Config.Tuple (vs))
        
        k.value = (1, 'a')

        for v in ((1, 2), (4, 'a'), 'toto'):
            try:
                k.value = v
                assert False, 'not to be reached for %s' % `v`
            
            except TypeError:
                pass
            except ValueError:
                pass
        return

    def testList (self):

        vs = Config.Integer (max = 4)
        k  = Config.Item ('', Config.List (vs))

        k.value = [1, 2, 3]
        
        for v in ([1, 2, 5], [1, 'a', 2], 'toto'):
            try:
                k.value = v
                assert False, 'not to be reached for %s' % `v`
            
            except TypeError:
                pass
            except ValueError:
                pass
        return

    def testDict (self):

        kt = Config.String ()
        vt = Config.Integer (max = 4)

        k = Config.Item ('', Config.Dict (kt, vt))

        k.value = {'a': 1, 'b': 2}
        k.value = {}

        for v in ({1:1}, {'a':'a'}, 'toto'):
            try:
                k.value = v
                assert False, 'not to be reached for %s' % `v`
            
            except TypeError:
                pass
            except ValueError:
                pass
        return
    
config = pybut.makeSuite (TestConfig, 'test')
match  = pybut.makeSuite (TestMatch, 'test')

pybut.run (pybut.TestSuite ((config, match)))
