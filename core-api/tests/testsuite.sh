#!/bin/sh

PYTHON=${PYTHON:-python}

${PYTHON} testsuite.py

test -z ,,* || rm -rf ,,*
