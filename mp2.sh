#!/bin/bash

if [[ $1 = 'test' ]]; then
    python3 test/run_mp2.py
elif [[ $1 = 'start' ]]; then
    echo start
fi
