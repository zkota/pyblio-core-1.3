from Pyblio.External import WOK

s = Registry.getSchema('org.pybliographer/wok/0.1')
db = Store.get('file').dbcreate(output, s)

wok = WOK.WOK(db)

d, rs = wok.search(query)

def success(total):
    print "wok: successfully fetched %d records" % total
    # do something with the database?

d.addCallback(success).addErrback(failure)

reactor.run()
