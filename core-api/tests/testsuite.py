import os, sys
import pybut


skip = os.environ.get ('UT_SKIP', '').split (':')

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
