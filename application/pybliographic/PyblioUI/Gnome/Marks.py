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

""" Used to keep track of specific attributes in the view. They are
invoked when the user wants to add, update or remove an attribute.

The hierarchy is:

 Record
   |
   +-> AttributeList (one for each key)
      |
      +-> Attribute
         |
         +-> QualifierList (one for each subkey)
            |
            +-> Qualifier
            

The marks are set up like that:

  start         sub               end
  ->|           |<-               |<-
    |T|i|t|l|e|\|-| |b|l|a|b|l|a|\|
    
"""

from sets import Set

from PyblioUI.Gnome.Display import fillTextBuffer, newValue

DASH = u'\u2013\xa0'


def stylize(buffer, b, e, *ss):
    """ Set some style to a portion of text, starting at 'b'
    (which is an offset), and ending at 'e', which is an
    iterator."""

    b = buffer.get_iter_at_offset(b)
    for s in ss:
        buffer.apply_tag_by_name (s, b, e)
    return

def IMark(object):

    """Interface for the objects forming the structure of a marked
    record."""

    def get(self):
        pass

    def recordSet(self, value):
        pass
    
    def delete(self, buffer):
        pass

    def next(self):
        pass
    
    def editPoint(self, buffer):
        pass

    def markup(self, buffer):
        pass

    def getPath(self):
        pass

    def getMarkAtPath(self, path):
        pass

    def insertValue(self):
        pass

    def createAttribute(self, idx=0):
        pass
    

class _Base(object):
    """ Virtual base class defining the most basic visual behavior."""
    
    def __init__(self, parent):
        self.reset()
        self.parent = parent
        return

    def reset(self):
        self.start = None
        self.end   = None
        self.sub   = None
        self.children = []
        self.update = None
        return

    def delete(self, buffer):
        to_iter = buffer.get_iter_at_mark
        buffer.delete(to_iter(self.start), to_iter(self.end))

        self.deleteMarks(buffer)
        return
    
    def deleteMarks(self, buffer):
        buffer.delete_mark(self.start)
        buffer.delete_mark(self.end)
        
        if self.sub: buffer.delete_mark(self.sub)

        if self.update:
            if self.update.l: buffer.delete_mark(self.update.l)
            if self.update.r: buffer.delete_mark(self.update.r)
        return

    def find(self, offset, buffer):
        """ Return the mark at the specified offset, or None. """

        # We need to compare the offsets to find out if we own the
        # specified position.
        l, r = self._to_offset(buffer)

        if offset >= l and offset < r:
            return self
        return None

    def insert(self, i, *args, **kargs):
        # This is a simple wrapper around the actual insert method,
        # which takes note of the begin and end position in the
        # buffer.
        self.start = i.get_offset()
        self._insert(i, *args, **kargs)
        self.end   = i.get_offset()
        return

    def markup(self, buffer):
        i = buffer.get_iter_at_offset(self.start)
        self.start = buffer.create_mark(None, i, False)
        
        i = buffer.get_iter_at_offset(self.end)
        self.end = buffer.create_mark(None, i, True)
        return

    def getPath(self):
        return self.parent.getPath() + (self.parent.children.index(self),)

    def getMarkAtPath(self, path):
        if path is (): return self
        return self.children[path[0]].getMarkAtPath(path[1:])
    
    def next(self):
        if self.children:
            return self.children[0]

        if self.parent:
            return self.parent._next(self)

        return self

    def editPoint(self, buffer):
        s = buffer.get_iter_at_mark(self.start)
        return s

    
    # --------------------------------------------------
    
    def _top(self):
        r = self
        while r.parent: r = r.parent
        return r

    def _to_offset(self, buffer):
        i2o = buffer.get_iter_at_mark
        
        return i2o(self.start).get_offset(), i2o(self.end).get_offset()
        
    
class _Container(_Base):

    def find(self, offset, buffer):
        """ Return the mark at the specified offset, or None. """

        l, r = self._to_offset(buffer)

        # Our positions do encompass the whole attribute list, so if
        # we don't own it, no need to ask our children.
        if offset < l or offset >= r:
            return None

        for c in self.children:
            m = c.find(offset, buffer)

            if m is not None:
                return m

        # If we find no better match, then it means we are in the
        # header of the attribute list.
        return self

    def markup(self, buffer):
        _Base.markup(self, buffer)

        for c in self.children:
            c.markup(buffer)
        return

    def deleteMarks(self, buffer):
        for child in self.children:
            child.deleteMarks(buffer)
            
        _Base.deleteMarks(self, buffer)
        return
    
    def reinsert(self, value, base, offset, db, buffer, view, editable):
        """ Reinsert a value at the specified offset."""

        # WARNING! Tricky code ahead
        
        def do_reinsert(i):
            # Actually recreate the mark with its new content.
            base.parent = self
            base.reset()

            base.insert(i, value, db, buffer, view, editable)
            base.markup(buffer)

            # ...and reinsert it at the right place
            self.children.insert(offset, base)

            # Now, we can update the value in the record itself.
            base.recordCreate(value)
            

        # These two functions together make it easy to ensure a mark
        # does not move during editing. The first one gets the offset
        # of the mark, the second recreates the mark.
        def store(mark):
            i = buffer.get_iter_at_mark(mark)
            buffer.delete_mark(mark)
            return i.get_offset()
        def restore(offset, left = True):
            i = buffer.get_iter_at_offset(offset)
            return buffer.create_mark(None, i, left)

        # When a mark is modified at its end, it is necessary to move
        # the end mark manually, possibly recursively.
        def restore_end(child):
            while 1:
                parent = child.parent
                if not parent: break
                
                idx = parent.children.index(child)

                if idx < len(parent.children) - 1:
                    break

                buffer.delete_mark(parent.end)
                i = buffer.get_iter_at_mark(child.end)
                parent.end = buffer.create_mark(None, i, True)

                child = parent
            return
        
        # We need to find a proper place for the new object. We insert
        # _before_ the specified offset.
        if offset == 0:
            # for the initial item, we use our own 'sub' mark, which
            # takes into account the possible header of the Container.
            if self.sub:
                # We move the sub mark after the operation, as we
                # cannot use a right mark, which blocks the update
                # (why?)
                i = buffer.get_iter_at_mark(self.sub)

                self.sub = store(self.sub)
                do_reinsert(i)
                self.sub = restore(self.sub)

            else:
                i = buffer.get_iter_at_mark(self.start)

                self.start = store(self.start)
                do_reinsert(i)
                self.start = restore(self.start, False)
                
            # We might have to move the end too, if this is our
            # only child
            if len(self.children) == 1:
                restore_end(base)
        else:
            # Otherwise, we add after the end mark of the preceding
            # item. We need to recreate the end mark.
            child = self.children[offset-1]

            i = buffer.get_iter_at_mark(child.end)
                
            do_reinsert(i)

            # If we inserted the last child of a sequence, we need to
            # move the end point.
            if len(self.children) == offset + 1:
                restore_end(base)
            
        return

    def createAttribute(self, idx=0):
        idx = self.parent.children.index(self)
        return self.parent.createAttribute(idx=idx)
    
    def _next(self, child):
        idx = self.children.index(child)
        try:
            return self.children[idx+1]
        except IndexError:
            return self.parent._next(self)
        return
    
class _AttributeContainer(_Container):
    def __init__(self, parent, key, atype):
        _Container.__init__(self, parent)
        
        self.key = key
        self.attributeType = atype
        return
    
    def _insert(self, i, attrs, db, buffer, view, editable):

        # Insert all the children one after the other
        for attr in attrs:
            child = self.child(self)
            child.insert(i, attr, db, buffer, view, editable)
            
            self.children.append(child)
        return

    def insertValue(self, buffer, view):
        db = self._top().db
        
        value = newValue(self.attributeType, db)

        new = self.child(self)
        self.reinsert(value, new, 0, db, buffer, view, True)

        return new
    

class _Leaf(object):
    
    def _getInfo(self):
        idx = self.parent.children.index(self)
        key = self.parent.key

        return key, idx

    def editPoint(self, buffer):

        s = buffer.get_iter_at_mark(self.start)
        s.forward_chars(2)

        return s
    
    def insertValue(self, buffer, view):
        db = self._top().db
        
        value = newValue(self.parent.attributeType, db)

        key, idx = self._getInfo()
        
        new = self.__class__(self.parent)
        self.parent.reinsert(value, new, idx + 1, db, buffer, view, True)

        return new



class Qualifier(_Leaf, _Base):
    """ A qualifier attribute."""

    def _getQInfo(self):
        attributeKey = self.parent.parent.parent.key
        attributeIdx = self.parent.parent.parent.children.index(self.parent.parent)

        return attributeKey, attributeIdx

    def delete(self, buffer):
        _Base.delete(self, buffer)

        record = self._top().record
        
        # update the data. we need to locate our parent Attribute
        # inside its group.
        attributeKey, attributeIdx = self._getQInfo()

        key, idx = self._getInfo()
        
        q = record[attributeKey][attributeIdx].q

        del q[key][idx]
        
        self.parent.children.remove(self)
        return

    def get(self):
        record = self._top().record

        attributeKey, attributeIdx = self._getQInfo()
        key, idx = self._getInfo()

        return record[attributeKey][attributeIdx].q[key][idx]

    def _recordChange(self, value, set):
        record = self._top().record

        aKey, aIdx = self._getQInfo()
        key, idx = self._getInfo()

        q = record[aKey][aIdx].q

        if set: q[key][idx] = value
        else:   q[key].insert(idx, value)
        return
    
    def recordSet(self, value):
        return self._recordChange(value, True)
    
    def recordCreate(self, value):
        return self._recordChange(value, False)
    
    def _insert(self, i, attr, db, buffer, view, editable):
        # syntactic sugar for the remaining of the code
        insert = buffer.insert_with_tags_by_name

        insert(i, DASH, 'qualified', 'static', 'colored')

        b = i.get_offset()
        self.update = fillTextBuffer(editable, attr, db, buffer, i, view)
        stylize(buffer, b, i, 'qualified')
        return

    def createAttribute(self, idx=0):
        return self.parent.createAttribute(idx)
    
    
class QualifierList(_AttributeContainer):
    """ Holder of the qualifiers of a given subkey. Has Qualifier
    children.""" 

    child = Qualifier
    
    def _getQInfo(self):
        attributeKey = self.parent.parent.key
        attributeIdx = self.parent.parent.children.index(self.parent)

        return attributeKey, attributeIdx

    def get(self):
        record = self._top().record
        attributeKey, attributeIdx = self._getQInfo()

        return record[attributeKey][attributeIdx].q[self.key]

    def recordSet(self, value):
        record = self._top().record
        attributeKey, attributeIdx = self._getQInfo()

        record[attributeKey][attributeIdx].q[self.key] = value
        return

    recordCreate = recordSet
    
    def delete(self, buffer):
        # erase visually
        _AttributeContainer.delete(self, buffer)

        record = self._top().record

        # update the data. we need to locate our parent Attribute
        # inside its group.
        attributeKey, attributeIdx = self._getQInfo()
        
        del record[attributeKey][attributeIdx].q[self.key]

        # remove from the structure
        self.parent.children.remove(self)
        return
    
    def _insert(self, i, record, db, buffer, view, editable):
        # syntactic sugar for the remaining of the code
        insert = buffer.insert_with_tags_by_name

        # Field title
        name = self.attributeType.name.replace('\n', ' ')

        insert(i, name, 'static', 'qualified field', 'field')
        insert(i, '\n', 'static', 'qualified field')

        self.sub = buffer.create_mark(None, i, True)

        _AttributeContainer._insert(self, i, record, db, buffer, view, editable)
        return
    

class Attribute(_Leaf, _Container):
    """ A single attribute. Has QualifierList children."""

    child = QualifierList

    def getPath(self):
        return self.parent.getPath() + (self.parent.children.index(self),)

    def delete(self, buffer):
        _Container.delete(self, buffer)

        # We need to find out our own place in the hierarchy
        key, idx = self._getInfo()
        
        del self._top().record[key][idx]
        self.parent.children.remove(self)
        return

    def get(self):
        record = self._top().record
        key, idx = self._getInfo()

        return record[key][idx]
        
    def _recordChange(self, value, set):
        # we need to change the value of the specified attribute,
        # without changing its qualifiers.
        record = self._top().record
        
        key, idx = self._getInfo()

        if set:
            q = record[key][idx].q
            value.q = q
            
            record[key][idx] = value
        else:
            record[key].insert(idx, value)
        return

    def recordSet(self, value):
        return self._recordChange(value, True)
    
    def recordCreate(self, value):
        return self._recordChange(value, False)

    def createAttribute(self, idx=0):
        
        # return the list of attributes not yet available in the
        # record, plus a function that will perform the actual
        # creation of the attribute.
        top = self._top()

        key, idx = self._getInfo()

        schema = top.db.schema[key].q
        
        known = Set(top.record[key][idx].q.keys())
        avail = Set(schema.keys())

        def create(schema, buffer, view):
            # do the actual creation
            new = self.child(self, schema.id, schema)
            self.reinsert([], new, idx, top.db, buffer, view, True)
            
            return new
        
        return [schema[k] for k in avail - known], create

    def _insert(self, i, attr, db, buffer, view, editable):
        # syntactic sugar for the remaining of the code
        insert = buffer.insert_with_tags_by_name

        insert(i, DASH, 'attribute', 'static', 'colored')

        b = i.get_offset()
        self.update = fillTextBuffer(editable, attr, db, buffer, i, view)
        stylize(buffer, b, i, 'attribute')

        self.sub = buffer.create_mark(None, i, True)

        fields = attr.q.keys()
        fields.sort()

        # We need info from the parent attributes
        parentKey = self.parent.key
        parentSchema = db.schema[parentKey].q
        
        for k in fields:
            desc = parentSchema [k]

            attlist = QualifierList(self, k, desc)
            attlist.insert(i, attr.q[k], db, buffer, view, editable)

            self.children.append(attlist)
        return
    
    
class AttributeList(_AttributeContainer):
    """ Holder of the attributes of a given key. Has Attribute
    children."""

    child = Attribute

    def get(self):
        record = self._top().record
        return record[self.key]

    def recordSet(self, value):
        record = self._top().record
        record[self.key] = value
        return

    recordCreate = recordSet

    def delete(self, buffer):
        # erase visually
        _AttributeContainer.delete(self, buffer)

        # update the data
        del self.parent.record[self.key]

        # remove from the structure
        self.parent.children.remove(self)
        return

    def _insert(self, i, record, db, buffer, view, editable):
        # syntactic sugar for the remaining of the code
        insert = buffer.insert_with_tags_by_name

        name = self.attributeType.name.replace('\n', ' ')

        insert(i, name, 'static', 'field')
        insert(i, '\n', 'static', 'attribute')

        self.sub = buffer.create_mark(None, i, True)

        _AttributeContainer._insert(self, i, record, db, buffer, view, editable)
        return
    

class Record(_Container):
    """ Holder of a complete record. Has AttributeList children."""

    child = AttributeList
    
    def __init__(self):
        _Container.__init__(self, None)
        return

    def reset(self):
        _Container.reset(self)
        
        self.db = None
        self.record = None
        return
    
    def _insert(self, i, record, db, buffer, view, editable):

        self.db = db
        self.record = record
        
        fields = self.record.keys()
        fields.sort()

        for k in fields:
            desc = self.db.schema[k]

            attlist = AttributeList(self, k, desc)
            attlist.insert(i, self.record[k], self.db, buffer, view, editable)

            self.children.append(attlist)
        return


    def _next(self, child):
        idx = self.children.index(child)
        try:
            return self.children[idx+1]
        except IndexError:
            return self.children[0]

    def getPath(self):
        return ()

    def createAttribute(self, idx=0):
        
        # return the list of attributes not yet available in the
        # record, plus a function that will perform the actual
        # creation of the attribute.
        schema = self.db.schema
        
        known = Set(self.record.keys())
        avail = Set(schema.keys())

        def create(schema, buffer, view):
            # do the actual creation
            new = self.child(self, schema.id, schema)
            self.reinsert([], new, idx, self.db, buffer, view, True)
            
            return new
        
        return [schema[k] for k in avail - known], create
    
    def find(self, offset, buffer):
        l, r = self._to_offset(buffer)

        # The Record class is the one to be alive when it has no
        # content.
        if l == r == offset:
            return self

        return _Container.find(self, offset, buffer)
    
