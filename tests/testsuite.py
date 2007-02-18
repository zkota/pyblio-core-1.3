import os, sys
import pybut


skip = [ x for x in os.environ.get ('UT_SKIP', '').split (':') if x ]

if skip:
    print "warning: skipping %s" % ', '.join (skip)
    
suits = []

for f in os.listdir ('.'):

    if os.path.splitext (f) [1] != '.py': continue
    if f [:3] != 'ut_': continue

    if f in skip: continue
    
    l = {}
    try:
        execfile(f, l, l)
    except ImportError, msg:
        sys.stderr.write("%s: missing dependency %s" % (
            repr(f), msg))
        continue
    
    try:
        suits.append (l['suite'])        
    except KeyError:
        sys.stderr.write ("test %s does not export 'suite' variable. Use 'trial' instead?\n" % f)

from Pyblio import init_logging

logfile = os.path.abspath('+pyblio.log')
if os.path.exists(logfile):
    os.unlink(logfile)
init_logging(logfile)

pybut.run(pybut.TestSuite(suits))
