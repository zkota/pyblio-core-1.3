import os, pybut

from Pyblio import Core, Schema

class TestCore (pybut.TestCase):

    def testEmpty (self):
        """ Create an empty database with a schema """
        
        schema = Schema.Schema ('ut_core/s:simple.xml')
        db = Core.Database (schema)

        assert len (db) == 0

        file = open (',,t1.xml', 'w')
        db.xmlwrite (file)
        file.close ()

        h1 = open (',,t1.xml').read ()
        h2 = open ('ut_core/empty.xml').read ()
        
        assert h1 == h2

        os.unlink (',,t1.xml')
        return
    
pybut.run (pybut.makeSuite (TestCore, 'test'))
