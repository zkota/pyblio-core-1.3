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

"""Support for queries on external services."""

from gettext import gettext as _

class IExternal(object):
    """Interface for querying external databases.

    This queries uses Twisted's deferred mechanism to handle
    asynchronous results. At most one query can run on a given
    IExternal object at a time.
    """

    schema = '' # schema of the database this IExternal can parse into
    
    def __init__(self, db):
        """Create a new external query interface.

        Args:
          db: Pyblio.Store.Database
        """
        assert db.schema.id == self.schema, \
               _('invalid schema: %r instead of %r' % (
            db.schema.id, self.schema))

    def count(self, query):
        """Return the number of matches for the specified query.

        Args:
          query: string
        Return:
          twisted.internet.defer.Deferred() -> int
        """

    def search(self, query, maxhits=100):
        """Return the number of matches for the specified query and a
        ResultSet() with the records that have been retrieved (at most
        maxhits).

        Args:
          query: string
          maxhit: integer
        Return:
          (twisted.internet.defer.Deferred() -> int,
           Pyblio.Store.ResultSet)
        """

    def cancel(self):
        """Cancel a pending query."""

