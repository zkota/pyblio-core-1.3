from Pyblio.Format import join, one, all, I, switch
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
