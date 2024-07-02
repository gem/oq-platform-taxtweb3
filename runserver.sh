#!/bin/bash
if ! (echo "$PYTHONPATH" | grep -q ":\?${PWD}:\?" ); then
    export PYTHONPATH="${PYTHONPATH}:${PWD}"
fi
if ! (echo "$PYTHONPATH" | grep -q ":\?../oq-platform-ipt:\?" ); then
    export PYTHONPATH="${PYTHONPATH}:../oq-platform-ipt"
fi
cd ../oq-platform-standalone
./runserver.sh
