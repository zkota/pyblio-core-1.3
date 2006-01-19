"""
Bibliographic database parsers for foreign formats.

This module contains extensible parsers for some known bibliographic
formats. In order to avoid hardcoding a predefined pybliographer
schema in these parsers, they are separated in two modules:

  - L{Pyblio.Parsers.Syntax} contains parsers that only know the
    syntactic rules for reading and writing the format

  - L{Pyblio.Parsers.Semantic} extends the syntactic parsers to make
    them usable on a I{specific} schema.

"""
