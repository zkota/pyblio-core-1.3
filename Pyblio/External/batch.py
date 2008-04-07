# This file is part of pybliographer
# 
# Copyright (C) 1998-2008 Frederic GOBRY
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

"""Fetch results in batches."""

import logging

from twisted.internet import defer, reactor

class Batch(object):

    log = logging.getLogger('pyblio.external.batch')

    def __init__(self, maxhits, batch_size):
        self.current = 0
        self.maxhits = maxhits
        self.batch_size = batch_size
        self.result = defer.Deferred()

    def fetch(self, query_runner):
        def _on_failure(failure):
            self.result.errback(failure)

        def _on_success(data):
            received, total = data
            self.current += received

            objective = min(total, self.maxhits)
            missing = objective - self.current
            self.log.info('fetched %d/%d (capping at %d)' % (
                self.current, total, self.maxhits))
            if missing > 0:
                d = query_runner(self.current, min(self.batch_size, missing))
                d.addCallback(_on_success).addErrback(_on_failure)
            else:
                # we already collected all the results
                self.result.callback(total)

        d = query_runner(self.current, min(self.maxhits, self.batch_size))
        d.addCallback(_on_success).addErrback(_on_failure)

        return self.result
