import os, pybut, sys, string

from PyblioUI import Config


class TestConfig (pybut.TestCase):

    """ Test the PyblioUI.Config base functions """

    def setUp (self):

        Config.reset ()
        return

    def testDomains (self):

        d = Config.domains ()
        assert d == []

        Config.parse ('ut_config')

        d = Config.domains ()
        assert d == ['sample', 'fake'], 'got %s' % `d`

        return

    def testDefine (self):

        try:
            Config.get ('my/key')
            assert False, 'not to be reached'
            
        except KeyError: pass

        Config.define ('my/key', 'help', Config.String ())

        try:
            Config.get ('my/key')

        except KeyError:
            assert 'should be defined'

        return

    def testSet (self):

        Config.define ('my/key', 'help', Config.String ())

        k = Config.get ('my/key')
        
        assert k.value is None

        k.value = 'toto'

        assert Config.get ('my/key').value == 'toto'
        return

    def testKeys (self):

        assert Config.keys () == []

        Config.parse ('ut_config')

        assert Config.keys () == []

        assert Config.keys_in_domain ('sample') == \
               [ 'sample/string' ]

        # after importing a key, it is available in the global list
        assert Config.keys () == \
               [ 'sample/string' ]

        return


class TestMatch (pybut.TestCase):

    """ Test the PyblioUI.Config value matching functions """

    def setUp (self):

        Config.reset ()
        Config.parse ('ut_config')
        return

    def testString (self):

        k = Config.get ('sample/string')

        k.value = 'toto'
        
        try:
            k.value = 1
            assert False, 'should not be accepted'
            
        except RuntimeError:
            pass
        
    
config = pybut.makeSuite (TestConfig, 'test')
match  = pybut.makeSuite (TestMatch, 'test')

pybut.run (pybut.TestSuite ((config, match)))
