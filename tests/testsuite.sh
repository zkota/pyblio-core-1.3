#!/bin/sh

for ut in `find . -name 'ut_*.py' -print` ; do
  echo "Running ${ut}"
  python ${ut}
done
