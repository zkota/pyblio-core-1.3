"""
Provides the base framework for manipulating bibliographic
databases. A database is a set of L{records <Pyblio.Store.Record>},
which contains B{typed} L{attributes <Pyblio.Attribute>}. The
definition of the available attributes is done in a L{schema
<Pyblio.Schema>}, which provides names, types and textual description
of the fields.

 - to know how to create, open and delete databases, check the
   L{Pyblio.Store} module.
   
"""
