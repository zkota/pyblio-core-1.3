import pybut
import copy

from PyblioUI.Gnome import Marks
from Pyblio import Store, Attribute

class Buffer(object):

    def __init__(self):
        return

    def insert_with_tags_by_name(self, i, text, *attrs):
        i.idx += len(text)
        return

    def create_mark(self, name, i, left):
        return

    def insert(self, i, text):
        i.idx += len(text)
        return

    def get_iter_at_offset(self, o):
        i = Iterator()
        i.idx = o
        return i

    def get_iter_at_mark(self, m):
        return Iterator()
    
    def apply_tag_by_name(self, name, b, e):
        pass

    def remove_all_tags(self, a, b):
        pass

    def delete(self, a, b):
        pass

    def delete_mark(self, m):
        pass
    
class Iterator(object):

    def __init__(self):
        self.idx = 0

    def backward_char(self):
        self.idx -= 1
        
    def forward_char(self):
        self.idx += 1

    def get_offset(self):
        return self.idx
        

class TestRemove (pybut.TestCase):

    def setUp (self):
        self.db = Store.get('file').dbopen('ut_marks/sample.pbl')
        self.rec = self.db[1]
        return

    def _removeAndCheck(self, path, target):
        b = Buffer()
        i = Iterator()
        
        m = Marks.Record()

        m.insert(i, self.rec, self.db, b, None, True)

        # Remove the specified item
        mark = m.getMarkAtPath(path)
        mark.delete(b)

        self.db[self.rec.key] = self.rec

        f = pybut.dbname()

        fd = open(f, 'w')
        self.db.xmlwrite(fd)
        fd.close()
        
        pybut.fileeq (f, target)
        return
    
    def testRemoveQualifier(self):
        self._removeAndCheck((0,0,0,0), 'ut_marks/rem-qualifier.xml')
        
    def testRemoveQualifierList(self):
        self._removeAndCheck((0,0,0), 'ut_marks/rem-qualifier.xml')
        
    def testRemoveAttribute(self):
        self._removeAndCheck((1,1), 'ut_marks/rem-author.xml')
        
    def testRemoveAttributeList(self):
        self._removeAndCheck((1,), 'ut_marks/rem-authors.xml')

class TestInsert (pybut.TestCase):

    def setUp (self):
        self.db = Store.get('file').dbopen('ut_marks/sample.pbl')
        self.rec = self.db[1]
        return

    def _removeAndInsert(self, path):
        b = Buffer()
        i = Iterator()
        
        m = Marks.Record()

        m.insert(i, self.rec, self.db, b, None, True)

        # Remove the specified item
        mark = m.getMarkAtPath(path)

        value = mark.get()
        mark.delete(b)

        # ...and put it back again
        parent, idx = path[:-1], path[-1]
        
        parent = m.getMarkAtPath(parent)
        parent.reinsert(value, mark, idx, self.db, b,
                        None, True)

        self.db[self.rec.key] = self.rec

        f = pybut.dbname()

        fd = open(f, 'w')
        self.db.xmlwrite(fd)
        fd.close()
        
        pybut.fileeq (f, 'ut_marks/sample.pbl')
        return

    def testQualifier(self):
        self._removeAndInsert((0,0,0,0))

    def testQualifierList(self):
        self._removeAndInsert((0,0,0))

    def testAttribute(self):
        self._removeAndInsert((0,0))

    def testAttributeList(self):
        self._removeAndInsert((0,))

    def testInTheMiddle(self):
        self._removeAndInsert((1,1))

suite = pybut.suite (TestRemove, TestInsert)

if __name__ == '__main__':  pybut.run (suite)
