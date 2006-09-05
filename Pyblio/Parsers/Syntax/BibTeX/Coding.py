# -*- coding: utf-8 -*-
# This file is part of pybliographer
# 
# Copyright (C) 1998-2006 Frederic GOBRY
# Email : gobry@pybliographer.org
# 	   
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2 
# of the License, or (at your option) any later version.
#   
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details. 
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
# 
# 

"""
Handles coding and decoding of LaTeX-escaped characters.

Coding and decoding tries to be as reversible as possible (though
certain encodings are ambiguous).
"""

# this map is for composing letters with diacritics, like in \'e
basemap = {
    ".": {
    'C': u"Ċ", 'E': u"Ė",
    'G': u"Ġ", 'I': u"İ",
    'Z': u"Ż",
    'c': u"\u010b", 'e': u"Ė",
    'g': u"ġ", 'z': u"ż",
    },
    
    "'": {
    'A': u"Á", 'E': u"É",
    'I': u"Í", 'O': u"Ó",
    'U': u"Ú", 'Y': u"Ý",
    'C': u"Ć", 'Z': u"Ź",
    'N': u"Ń",
    'a': u"á", 'e': u"é",
    'i': u"í", 'o': u"ó",
    'u': u"ú", 'y': u"ý",
    'c': u"ć", 'z': u"ź",
    'n': u"ń",
    },
    
    "`": {
    'A': u"À", 'E': u"È",
    'I': u"Ì", 'O': u"Ò",
    'U': u"Ù",
    'a': u"à", 'e': u"è",
    'i': u"ì", 'o': u"ò",
    'u': u"ù",
    },
    
    "^": {
    'A': u"Â", 'E': u"Ê",
    'I': u"Î", 'O': u"Ô",
    'U': u"Û",
    'a': u"â", 'e': u"ê",
    'i': u"î", 'o': u"ô",
    'u': u"û",
    },

    '"': {
    'A': u"Ä", 'E': u"Ë",
    'I': u"Ï", 'O': u"Ö",
    'U': u"Ü",
    'a': u"ä", 'e': u"ë",
    'i': u"ï", 'o': u"ö",
    'u': u"ü", 'y': u"ÿ",
    },

    "c": {
    'C': u"Ç", 'c': u"ç",
    },

    "~": {
    'A': u"Ã", 'O': u"Õ",
    'a': u"ã", 'o': u"õ",
    'n': u"ñ", 'N': u"Ñ",
    },
}

staticmap = {
    'ss': (u'ß', 0),
    'ae': (u'æ', 0),
    'oe': (u'œ', 0),
}


_reversemap = {}

# construct a simple map that goes from the unicode character to the
# BibTeX representation
for cmd, sub in basemap.iteritems():
    for letter, symbol in sub.iteritems():
        _reversemap[symbol] = '\\%s%s' % (cmd, letter)

for cmd, (symbol, count) in staticmap.iteritems():
    _reversemap[symbol] = '\\%s{}' % cmd

def _encodeone(char):
    o = ord(char)
    if o >= 32 and o <= 127 and char not in '{}%\\':
        return char

    try:
        return _reversemap[char]
    except KeyError:
        return '\\char%d' % o

def encode(text):
    """ encode a unicode string into a valid BibTeX string """
    return u''.join(_encodeone(c) for c in text)



