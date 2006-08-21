#!/bin/sh

PYTHON=${PYTHON:-python}

${PYTHON} testsuite.py

rm -rf ,,*
rm -rf _trial_temp
