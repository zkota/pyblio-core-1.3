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
Handles decoding of @string substitution and of LaTeX commands.

The @string substitution is a one-way operation, as it is probably not
possible to do something better, except in some restricted cases
(dates for instance). Commands, on the other side, can be reencoded
when they represent unicode characters for instance.
"""

from Pyblio.Parsers.Syntax.BibTeX import Parser, Coding

def _accent(stack, cmd, tt):

    try:
        m = Coding.basemap[cmd]

    except KeyError:
        return Parser.Text('?')
    
    if isinstance(tt, Parser.Text):

        if len(tt) > 1:
            t = tt[0]
            stack.insert(0, Parser.Text(tt[1:]))
        else:
            t = tt
            
    elif isinstance(tt, Parser.Block):
        t = tt._d [0]

        if isinstance(t, Parser.Text):
            pass

        elif isinstance(t, Parser.Cmd):
            # There are a few special cases where one wants to accent a command, like:
            #              \'{\i}
            if t._cmd == 'i':
                t = Parser.Text('i')
            else:
                raise Exceptions.ParserError('cannot evaluate expression %s' % repr((cmd, tt)))

        else:
            raise Exceptions.ParserError('cannot evaluate expression %s' % repr((cmd, tt)))

    else:
        raise Exceptions.ParserError('cannot evaluate expression %s' % repr((cmd, tt)))

    try:
        return Parser.Text(m[t])
    except KeyError:
        raise KeyError ("cannot find %s in map %s" % (repr (t), repr (cmd)))


class Environ(object):

    commands = {
        "'":  (_accent, 1),
        '`':  (_accent, 1),
        '^':  (_accent, 1),
        '"':  (_accent, 1),
        'c':  (_accent, 1),
        '~':  (_accent, 1),
        }

    commands.update(Coding.staticmap)

    def run(self, cmd, stack):
        try:
            fn, count = self.commands[cmd]

        except KeyError:
            # The \char macro is special: \char125 -> character with ascii code 125
            if cmd.startswith('char'):
                try: return Parser.Text(unichr(int(cmd[4:])))
                except ValueError: pass

            # Try with local extensions
            fn = getattr(self, 'do_' + cmd, None)

            if fn:
                return fn(cmd, stack)
            
            return Parser.Text(cmd)

        # we have found a known command. as a convenience, we fetch
        # the required number of arguments and pass it to the actual
        # function handling the command.
        args = []
        
        while count:
            try:
                args.append(stack.pop(0))
            except IndexError:
                raise Exceptions.ParserError('command %s requires %d arguments, got %s' % (
                    repr(cmd), count, len(args)))
            
            count -= 1
            
        if callable(fn):
            return fn(stack, cmd, *args)

        return Parser.Text(fn)
    
            
