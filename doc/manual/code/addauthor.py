from Pyblio import Attribute

for record in db.entries.itervalues():
    person = Attribute.Person(last=u"Gobry",
                              first=u"Frédéric")

    record.add('author', person)

    db[record.key] = record
    
db.save()
