#!/bin/bash
set -eo pipefail
python-coverage erase
python-coverage run ./poc || true
find examples -name \*.poc -print0 | xargs -0n1 -P`getconf _NPROCESSORS_ONLN` python-coverage run -p ./poc
#for i in examples/*.poc; do
#    echo $i
#    python-coverage run -a ./poc $i || exit $?
#done
python-coverage combine -a .coverage.*
python-coverage report -m --include poctools.py
