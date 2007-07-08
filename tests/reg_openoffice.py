# regression testsuite for OpenOffice.org integration

from Pyblio.Cite.WP.OpenOffice import OOo
from Pyblio.Format import B, one
from Pyblio import Registry, Attribute, Store

Registry.parse_default()
s  = Registry.getSchema('org.pybliographer/bibtex/0.1')
db = Store.get('memory').dbcreate(None, s)

style = u'This has key ' + B[one('id')]
formatter = style(db)

# tests begin here
oo = OOo()
oo.connect()

oo.text.setString(u'')

refs = [(1, 'a', 'bibtex-a'),
        (2, 'b', 'bibtex-b')]
oo.cite(refs, None)

# check that the citations have been inserted in the document
r = oo.text.getString()
assert r == u'[a][b]', repr(r)

# check that the document can return the existing citations
r = oo.fetch()
assert r == refs, repr(r)

# create the bibliography
insert = oo.update_biblio()
insert.begin_biblio()
for uid, key, extra in refs:
    insert.begin_reference(key)
    r = Store.Record()
    r.add('id', key, Attribute.ID)
    insert(formatter(r))
    insert.end_reference(key)
insert.end_biblio()

r = oo.text.getString()
assert r == u'''\
[a][b]

[a]\xa0This has key a
[b]\xa0This has key b

''', r

# update the bibliography
insert = oo.update_biblio()
insert.begin_biblio()
reverse = refs[:]
reverse.reverse()
for uid, key, extra in reverse:
    insert.begin_reference(key)
    r = Store.Record()
    r.add('id', key, Attribute.ID)
    insert(formatter(r))
    insert.end_reference(key)
insert.end_biblio()

r = oo.text.getString()
assert r == u'''\
[a][b]

[b]\xa0This has key b
[a]\xa0This has key a

''', r

# update the labels
oo.update_keys({1:u'b', 2:u'a'})

r = oo.text.getString()
assert r == u'''\
[b][a]

[b]\xa0This has key b
[a]\xa0This has key a

''', r
