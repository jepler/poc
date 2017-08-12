#!/bin/bash
if [ -z "${DISPLAY-}" ]; then
    exec xvfb-run -s "-screen 0 640x480x24" bash "$0"
fi

find examples -name "*.poc" -print0 | xargs -0 -n1 -P`getconf _NPROCESSORS_ONLN` ./pocimg
