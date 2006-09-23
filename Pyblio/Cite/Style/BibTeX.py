from Pyblio.Format import join, one, all
from Pyblio.Cite.Style.Base import Alpha
    
class AuthorYear(Alpha):
    def _generate(self, uid):
        rec = self.db[uid]
        if not ('date' in rec or 'author' in rec):
            return 'Unknown'

        k = []
        if 'author' in rec:
            k.append(rec['author'][0].last)

        if 'date' in rec:
            k.append(str(rec['date'][0].year))

        return ':'.join(k)
    

plain = one('title')


