#!/bin/bash

SCRIPT_DIR=$(realpath $(dirname $0))
CONTAINER_NAME=mp2
RUNNING_DIR=~/runner

if [[ "$1" == "testcase" ]]; then
    if [[ -n "$2" ]]; then
        from="$2"
        to=$((from + 1))
        if [[ -n "$3" ]]; then
            to="$3"
        fi
        python3 test/run_mp2.py "$from" "$to"
    else
        python3 test/run_mp2.py
    fi
elif [[ "$1" == "pull" ]]; then
    docker pull ntuos/mp2
elif [[ "$1" == "test" ]]; then
    docker run --rm -it -v "$(realpath $SCRIPT_DIR)":"/home/student/mp2" \
        -u student -w /home/student/mp2 \
        --name $CONTAINER_NAME ntuos/mp2 ./mp2.sh
elif [[ "$1" == "run" ]]; then
    docker run --rm -it -v "$(realpath $SCRIPT_DIR)":"/home/student/mp2" \
        -u student -w /home/student/mp2 \
        --name $CONTAINER_NAME ntuos/mp2 bash
else
    mkdir -p $RUNNING_DIR
    cp -r . $RUNNING_DIR
    cd $RUNNING_DIR
    python3 test/run_mp2.py
fi
