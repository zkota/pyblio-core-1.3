from gettext import gettext as _

from Pyblio import Callback, Store, Attribute

""" Module containing convenience parsers for simple tags """


class Flat (Callback.Publisher):

    Reader = None

    def parse (self, fd, db):

        self._fd = self.Reader (fd)
        self.db = db

        self.emit ('file-start')
        
        while 1:
            record = self._fd.next ()
            
            if record is None: break

            self.record_parse (record)

        self.emit ('file-stop')
        return

    def record_begin (self):

        pass

    def record_end (self):

        pass

    def record_parse (self, record):

        self.record = Store.Record ()
        
        self.record_begin ()
        
        for line, tag, data in record:

            try:
                cmd = getattr (self, 'do_%s' % tag)

            except AttributeError:

                try:
                    cmd = getattr (self, 'do_default')

                except AttributeError:

                    self.emit ('warning', _('line %d: unhandled tag %s' % (
                        line, `tag`)))
                    continue

            cmd (tag, data)

        self.record_end ()

        # The record might have been discarded by self.record_end (),
        # so insert conditionally.
        if self.record is not None:
            
            k = self.db.add (self.record)
            self.emit ('record-added', k)

            self.record = None
            
        return

    def add_text (self, field, value):

        self.record [field] = Attribute.Text (value)
        return
    
    
