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

"""
Citation formatting layer.

Rationale: the difficult part in formatting the records is not how the
records are actually laid out on a page, the keys,... but rather the
actual layout of the authors, the publication information,...
especially given that all the records are not complete.

So, this module is only intended to handle I{this specific aspect},
not to compose a whole page.

The code here allows the writing of citation styles with a convenient
syntax:

  >>> authors  = lastFirst (all ('author'))

  >>> location = join (', ') ['vol. ' + one ('volume'),
  ...                         'num. ' + one ('number'), ]
                       
  >>> citation = join (', ') [ authors , I [ one ('title') | 'untitled' ] ]


Citing a reference is a multi-stage operation:

 - B{stage 1:} the citation is written by the programmer in a
   convenient Domain Specific Language (DSL)

     >>> citation = join(', ')['vol. ' + one('volume'),
     ...                       'num. ' + one('number')]

 - B{stage 2:} the formatter of stage 1 is 'compiled' on a specific
   database (which allows for some initial checks (existence of the
   requested fields and txo for instance)

     >>> formatter = citation(db)

 - B{stage 3:} the compiled formatter can accept records, and return an
   abstract representation of the citation, with style indications

     >>> cited = formatter(record)

 - B{stage 4:} the abstract representation is turned into a concrete
   representations (plain text, HTML,...)

     >>> html = HTML.generate(cited)


The ideas for the syntax have been heavily borrowed from nevow's stan.

"""


from Pyblio.Format.DSL import join, one, all, switch, A, B, I, BR, Missing, lazy

