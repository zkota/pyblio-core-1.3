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

from Pyblio.Format import join, one, all, I, switch, BR, B, Span
from Pyblio.Format.Misc import plural
from Pyblio.Format.Date import year
from Pyblio.Format.Person import firstLast

from Pyblio.Cite.Style.Base import Alpha
    
class AlphaKey(Alpha):
    """ Generate keys based on authors and year. """
    
    def _generate(self, uid):
        rec = self.db[uid]
        if not ('date' in rec or 'author' in rec):
            return 'Unknown'

        k = []
        if 'author' in rec:
            au = rec['author']
            if len(au) == 1:
                k.append(au[0].last[:3])
            else:
                k.append(''.join([a.last[0] for a in au[:3]]))
            
        if 'date' in rec:
            k.append(str(rec['date'][0].year)[-2:])

        return ''.join(k)

# This formats a list of authors according to the Chicago manual of
# style.
def Chicago(people):
    return plural(people,
                  one  = join ('') [ people ],
                  two  = join (' and ') [ people ],
                  more = join (', ', last = ', and ') [ people ])


# Definitions of the "Plain" (and derived) citation format.
plain_author = Chicago(firstLast(all('author')))

plain_journal = join(', ')[
    I[one('journal')],
    join(':')[one('volume'), one('number')],
    year(one('date'))
]

plain_place = switch('doctype')
plain_place = plain_place.case(article=plain_journal)
plain_place = plain_place.default(year(one('date')))

plain = join('. ')[plain_author, one('title'), plain_place] + '.'

# The "full" format also provides an abstract.
full = join('\n')[Span(size='large', weight='bold')[one('title')],
                  Span(size='large')[plain_author],
                  Span(size='large')[plain_place],
                  Span(color='#505050')[one('abstract')]]
