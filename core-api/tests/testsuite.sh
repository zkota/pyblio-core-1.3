#!/bin/sh

PYTHON=${PYTHON:-python}

for ut in `find . -name 'ut_*.py' -print` ; do
  echo "unittest: running suite ${ut}"
  ${PYTHON} ${ut}
  echo "unittest: =================================================="
done
