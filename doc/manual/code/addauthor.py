from Pyblio import Attribute

for record in db.entries.itervalues():
    person = Attribute.Person(last=u"Gobry",
                              first=u"Fr�d�ric")

    record.add('author', person)

    db[record.key] = record
    
db.save()
