"""
Allows the writing of citation styles like:

authors  = lastFirst (all ('author'))

location = join (', ') ['vol. ' + one ('volume'),
                        'num. ' + one ('number'), ]
                       
citation = join (', ') [ authors , I [ one ('title') | 'untitled' ] ]

"""

from Pyblio.Format.DSL import access, join
from Pyblio.Format.Tags import A, B, I, T

