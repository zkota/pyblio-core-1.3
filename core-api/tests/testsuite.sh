#!/bin/sh

for ut in `find . -name 'ut_*.py' -print` ; do
  echo "unittest: running suite ${ut}"
  python ${ut}
  echo "unittest: =================================================="
done
