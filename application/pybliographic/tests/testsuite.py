#!/usr/bin/python

import os, sys
import pybut

try:
    skip = os.environ ['UT_SKIP'].split (':')

except KeyError:
    skip = []

if skip:
    print "warning: skipping %s" % ', '.join (skip)

    
suits = []

for f in os.listdir ('.'):

    if os.path.splitext (f) [1] != '.py': continue
    if f [:3] != 'ut_': continue

    if f in skip: continue
    
    l = {}
    execfile (f, l, l)

    try:
        suits.append (l ['suite'])
        
    except KeyError:
        sys.stderr.write ("test %s does not export 'suite' variable\n" % f)


pybut.run (pybut.TestSuite (suits))
