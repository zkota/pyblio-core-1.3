# This file is part of pybliographer
# 
# Copyright (C) 1998-2003 Frederic GOBRY
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

"""
Support for RIP files.

RIP files are files containing registering information for schemas,
and extension classes customized for these schemas (like importers,
exporters, citation formatters,...)

First, you need to parse a few RIP repositories with L{parse}, then
you can browse the results with L{schemas}, L{getSchema} and L{get}.
"""

import os, re

from ConfigParser import SafeConfigParser as Parser

from Pyblio import Schema

from gettext import gettext as _


# Global registry of schemas
_schema = {}

# We have a system-wide directory of RIPs that is known to the system,
# and a local one, in the user's home directory.
import Pyblio

_base = os.path.abspath(os.path.dirname(Pyblio.__file__))
_user = os.path.expanduser('~/.pyblio')

RIP_dirs = {
    'system': os.path.join(_base, 'RIP'),
    'user': _user,
    }


def get(schema, category):
    """ Return the extensions in a given category, for a given schema."""
    
    try:
        return _schema[schema][category]
    except KeyError:
        return []

def getSchema(schema):
    """ Return the L{Pyblio.Schema.Schema} corresponding to an
    identifier returned by L{schemas}."""
    
    rip = _schema[schema]
    
    s = Schema.Schema(open(rip.path))
    
    assert s.id == schema, _('schema %s has not the same id %s as in the RIP files') % (
        rip.path, schema)
    return s


def schemas():
    """ Return the list of known schemas."""
    
    return [k for k in _schema.keys() if _schema[k].path]


def reset():
    """ Forget all the schemas and extensions previously parsed with
    L{parse}.
    """
    
    global _schema
    _schema = {}


class RIP(object):

    """ A RIP object represents a dynamic class that can be loaded on
    demand, and that has been registered via the Registry system.

    These objects are usually not instanciated by the user, but
    returned by L{get}."""
    
    def __init__(self, schema, category, name):
        self.schema = schema
        self.category = category
        self.name = name
        self._module = None
        return
    
    def __call__(self):
        """ When the RIP is called, it returns the dynamic class it
        refers to, or raises an ImportError exception.
        """
        
        if not self._module:
            parts = self.name.split('.')
            
            module = __import__('.'.join(parts[:-1]))

            for comp in parts[1:]:
                module = getattr (module, comp)

            self._module = module
            
        return self._module        

    def help(self):
        """ Return some help associated with the corresponding dynamic class.

        Warning: this forces loading of the class.
        """
        
        m = self()
        
        doc = m.__doc__
    
        if not doc:
            doc = _('undocumented %s' % repr(self.name))
        else:
            doc = doc.lstrip()
            doc = doc.split('\n')[0].rstrip(' .\n')

        return doc

class AdapterRIP(RIP):
    """ A special RIP that keeps the description of an Adapter."""
    
    def __init__(self, schema, category, name, target):
        RIP.__init__(self, schema, category, name)

        self.target = target
        return

_adapt_re = re.compile(r'([\w\d.]+)\s*->\s*([\w\d./]+)')
    
class _RIPCategory(dict):
    def __init__(self, schema):
        dict.__init__(self)
        self.schema = schema
        self.path = None
        return

    
def parse(directory):
    """ Parse the specified directory, and load all the .rip files it
    contains."""

    for f in os.listdir(directory):
        base, ext = os.path.splitext(f)
        if ext != '.rip': continue
        
        name = os.path.join(directory, f)

        allvars = {}
        allvars.update(RIP_dirs)
        allvars['cwd'] = directory
        
        p = Parser(allvars)
        p.readfp(open(name), name)
        
        for schema in p.sections():
            for cat in p.options(schema):
                value = p.get(schema, cat).strip()

                # Schema are special values, which are not merged but
                # checked for unicity.
                if cat == 'path':
                    if _schema.has_key(schema):
                        s = _schema[schema]
                        assert (s.path is None or
                                s.path == value), \
                                _('Schema %s is available in %s and %s') % (
                            s.path, value)

                        s.path = value

                    else:
                        r = _RIPCategory(schema)
                        r.path = value

                        _schema[schema] = r

                    continue
                
                if cat == 'adapters':
                    names = []
                    for m, t in _adapt_re.findall(value):
                        names.append(AdapterRIP(schema, cat, m, t))
                    

                else:
                    names = [RIP(schema, cat, x.strip())
                             for x in value.split('\n') ]

                # For the other fields, we simply extend the list
                # of known values.
                try:
                    _schema[schema].setdefault(cat,[]).extend(names)

                except KeyError:
                    r = _RIPCategory(schema)
                    r[cat] = names

                    _schema[schema] = r
                    
    return

def parse_default():
    for d in RIP_dirs.values():
        try:
            parse(d)
        except OSError:
            pass
    return
