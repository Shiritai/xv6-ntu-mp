#!/bin/bash

if [[ "$1" == "test" ]]; then
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
elif [[ "$1" == "start" ]]; then
    echo "start"
fi
