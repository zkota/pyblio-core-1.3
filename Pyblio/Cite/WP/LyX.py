# This file is part of pybliographer
# 
# Copyright (C) 1998-2004 Frederic GOBRY
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

"""
Operations on a running LyX instance.

LyX only allows you to insert keys at the current cursor position.
"""

import os, string, select, signal

from gettext import gettext as _

from Pyblio.Cite.WP import CommunicationError, OperationError

class LyX(object):
    def __init__(self, pipe='~/.lyx/lyxpipe'):
        self.pipe = pipe
        self.pin  = None
        self.pout = None

        self.buffer = ''
        return

    def connect(self):
        if self.is_connected():
            return
        
        pin  = os.path.expanduser(self.pipe + '.in')
        pout = os.path.expanduser(self.pipe + '.out')

        def safe_connect(f, mode):
            try:
                fd  = os.open(f,  os.O_NONBLOCK | mode)
            except OSError, msg:
                if msg.errno == 6:
                    os.unlink(f)
                    raise CommunicationError(_("pipe %r is not connected to LyX") % f)
                if msg.errno == 2:
                    raise CommunicationError(_("Cannot find pipe %r") % f)
                else:
                    raise
            return fd
        
        self.pin  = safe_connect(pin,  os.O_WRONLY)
        self.pout = safe_connect(pout, os.O_RDONLY)
                
        self._send('hello', base='LYXSRV')
        return

    def is_connected(self):
        return self.pin is not None
    
    def disconnect(self):
        if self.is_connected():
            self._send('bye', base='LYXSRV')
            self._close()
        return
    
    def cite(self, keys):
        if not self.is_connected():
            raise OperationError(_("Cannot cite when not connected"))

        # make actual keys by joining the "readable" part with the
        # constant part.
        full = ['%s:(%s)' % x for x in keys]
        
        self._send('citation-insert:' + ' '.join(full))
        return

    def fetch(self):
        return None
    
    def update_keys(self, keymap):
        return

    def update_biblio(self):
        return None

    def _close(self):
        os.close(self.pin)
        os.close(self.pout)
        self.pin = None
        self.pout = None
        return
    
    def _send(self, msg, base='LYXCMD'):
        raw = msg.encode('latin-1', 'replace')
        
        try:
            os.write(self.pin, '%s:pyblio:%s\n' % (base, raw))
        except OSError, msg:
            self._close()
            raise CommunicationError(_("cannot perform operation (%s)") % msg)

        # This message has no answer
        if msg == 'bye':
            return
        
        answer = None
        
        while 1:
            r = select.select([self.pout], [], [], 2)
            if not r[0]:
                break
            self.buffer += os.read(self.pout, 1024)

            if '\n' in self.buffer:
                answer, self.buffer = self.buffer.split('\n', 1)
                break
            
        # if the answer is empty or starts with "ERROR", there is sth
        # wrong.
        if not answer:
            self._close()
            raise CommunicationError(_("LyX did not answer to our request"))

        parts = answer.split(':')
        if parts[0] == 'ERROR':
            raise OperationError(_("LyX rejected the command: %s") % parts[-1])
        return

    def __del__ (self):
        self.disconnect()
        return
