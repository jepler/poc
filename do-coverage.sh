#!/bin/sh
python3-coverage run ./poc || true
for i in examples/*.poc; do
    echo $i
    python3-coverage run -a ./poc $i || exit $?
done
python3-coverage report -m
