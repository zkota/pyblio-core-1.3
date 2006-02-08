from Pyblio.Sort import OrderBy

view = db.entries.view(OrderBy('year', asc=False) &
                       OrderBy('author'))

for record in view.itervalues():
    # do something with the record
    # ...
