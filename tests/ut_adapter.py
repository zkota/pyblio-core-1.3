import pybut

from Pyblio import Adapter, Store, Schema, Attribute

class A2BAdapter(Adapter.OneToOneAdapter):
    """ This adapter renames field 'a' into field 'b' """

    schema = Schema.Schema(open('ut_adapter/b.sip'))

    def source2target(self, record):
        new = Store.Record()
        new.key = record.key

        if 'a' in record:
            new['b'] = record['a']

        return new

    def target2source(self, record):
        new = Store.Record()
        new.key = record.key

        if 'b' in record:
            new['a'] = record['b']

        return new
        
class TestFromAtoB(pybut.TestCase):

    def setUp(self):
        sa = Schema.Schema(open('ut_adapter/a.sip'))

        fmt = Store.get('memory')
        self.dba = fmt.dbcreate(None, sa)
        self.dbb = A2BAdapter(self.dba)
        return

    def testAddAndDel(self):
        """ Add to A, and check in B """

        r = Store.Record()
        k = r.add('a', 'A sample !', Attribute.Text)

        # Add a record in A...
        self.dba.add(r)

        # ...and it show up in B (with the proper value)
        res = [self.dbb[k] for k in self.dbb.entries]
        self.failUnlessEqual(len(res), 1)

        new = res[0]
        self.failUnlessEqual(new['b'], r['a'])

        res = list(self.dbb.entries.itervalues())[0]
        self.failUnlessEqual(res['b'], r['a'])

        k, res = list(self.dbb.entries.iteritems())[0]
        self.failUnlessEqual(res['b'], r['a'])

        del self.dba[k]
        self.failUnlessEqual(list(self.dbb.entries.itervalues()), [])


    def testXMLWrite(self):
        r = Store.Record()
        k = r.add('a', 'A sample !', Attribute.Text)
        self.dba.add(r)

        tmp = pybut.dbname()
        fd = open(tmp, 'w')
        self.dbb.xmlwrite(fd)
        fd.close()

        pybut.fileeq(tmp, 'ut_adapter/saved-b.bip')

class TestResolution(pybut.TestCase):
    def testResolveA2B(self):
        sa = Schema.Schema(open('ut_adapter/a.sip'))

        fmt = Store.get('memory')
        self.dba = fmt.dbcreate(None, sa)

        from Pyblio import Registry
        Registry.reset()
        Registry.parse('ut_adapter')

        dest = Adapter.adapt_schema(self.dba, 'b')
        self.failUnlessEqual(dest.schema.id, 'b')
        
suite = pybut.suite(TestFromAtoB, TestResolution)

if __name__ == '__main__':  pybut.run (suite)
