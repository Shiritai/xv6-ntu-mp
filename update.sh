#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR=$(realpath "$(dirname "${BASH_SOURCE[0]}")") || {
    echo "Error: Failed to determine script directory"
    exit 1
}

# check if this repo need to be updated
if command -v curl >/dev/null 2>&1; then
    if [[ $(cat "$SCRIPT_DIR/version" 2>/dev/null) = \
          $(curl https://raw.githubusercontent.com/Shiritai/xv6-ntu-mp2/refs/heads/ntuos/mp2-submit/version 2>/dev/null) ]]; then
        # no need to update
        echo "Your mp2 is the newest version!"
        exit 0
    else
        echo "Your mp2 is not the newest version, updating..."
    fi
else
    echo "Please install curl command to run the update script!"
    exit 1
fi

declare -a FILES=(
    # basic
    "version"
    "mp2.sh"
    "scripts/action_grader.sh"
    "scripts/pre-commit"
    "scripts/pre-push"
    # doc part
    "doc/mp2-spec.md"
    "doc/mp2-spec.pdf"
    "doc/mp2-spec-zh_TW.md"
    "doc/mp2-spec-zh_TW.pdf"
    "doc/img/mp2-git.png"
    "doc/img/mp2-kmem_cache.png"
    "doc/img/mp2-slab-alloc.png"
    "doc/img/mp2-slab-free.png"
    "doc/img/mp2-slab-mem.png"
    "doc/img/mp2-slab.png"
    "doc/img/slab-alloc.png"
    "doc/img/vscode-git.png"
    # kernel part
    "kernel/main.c"
    "kernel/mp2_checker.h"
    "kernel/param.h"
    "kernel/file.h"
    "kernel/list.h"
    # test part
    "test/check_cache.cpython-39-x86_64-linux-gnu.so"
    "test/check_list.cpython-39-x86_64-linux-gnu.so"
    "test/check_slab.cpython-39-x86_64-linux-gnu.so"
    "test/pseudo_fslab.cpython-39-x86_64-linux-gnu.so"
    "test/check_cache.cpython-39-aarch64-linux-gnu.so"
    "test/check_list.cpython-39-aarch64-linux-gnu.so"
    "test/check_slab.cpython-39-aarch64-linux-gnu.so"
    "test/pseudo_fslab.cpython-39-aarch64-linux-gnu.so"
    "test/congratulations.txt"
    "test/gradelib.py"
    "test/private_tests.zip.enc"
    "test/public/mp2-0.txt"
    "test/public/mp2-1.txt"
    "test/public/mp2-2.txt"
    "test/public/mp2-3.txt"
    "test/public/mp2-4.txt"
    "test/public/mp2-5.txt"
    "test/public/mp2-6.txt"
    "test/public/mp2-7.txt"
    "test/public/mp2-8.txt"
    "test/public/mp2-9.txt"
    "test/public/mp2-10.txt"
    "test/public/mp2-11.txt"
    "test/public/mp2-12.txt"
    "test/public/mp2-13.txt"
    "test/public/mp2-14.txt"
    "test/public/mp2-15.txt"
    "test/public/mp2-16.txt"
    "test/public/mp2-17.txt"
    "test/public/mp2-18.txt"
    "test/public/mp2-19.txt"
    "test/public/mp2-20.txt"
    "test/public/mp2-21.txt"
    "test/public/mp2-22.txt"
    "test/public/mp2-23.txt"
    "test/public/mp2-24.txt"
    "test/setup.py"
    "test/run_mp2.py"
    # user programs
    "user/initcode.S"
    "user/ok.h"
    "user/cat.c"
    "user/debugswitch.c"
    "user/forktest.c"
    "user/grind.c"
    "user/ln.c"
    "user/mkdir.c"
    "user/oap.c"
    "user/printf.c"
    "user/sh.c"
    "user/tee.c"
    "user/umalloc.c"
    "user/zombie.c"
    "user/checkstr.c"
    "user/echo.c"
    "user/gah.c"
    "user/grep.c"
    "user/init.c"
    "user/kill.c"
    "user/ls.c"
    "user/mp2.c"
    "user/oak.c"
    "user/prepare.c"
    "user/rm.c"
    "user/stressfs.c"
    "user/ulib.c"
    "user/user.h"
    "user/usertests.c"
    "user/wc.c"
    "user/user.ld"
    "user/usys.pl"
    # action part
    ".github/workflows/autograde.yml"
    ".github/workflows/autosubmit.yml"
)

function download_and_replace() {
    tar="$SCRIPT_DIR/$1"
    tar_dir=$(dirname "${tar}")
    mkdir -p "$tar_dir"
    src="https://raw.githubusercontent.com/Shiritai/xv6-ntu-mp2/refs/heads/ntuos/mp2-submit/$1"
    if ! [[ -f $"$tar" ]]; then
        # if file not exists -> add
        echo "Adding file ${tar}..."
        curl "$src" --output "$tar" 2>/dev/null
    else
        # if file exists -> try update
        echo "Updating file ${tar}..."
        curl "$src" --output "${tar}" 2>/dev/null
    fi
}

trap 'echo "Script interrupted"; cleanup; exit 1' INT TERM

export -f download_and_replace
export SCRIPT_DIR=$(pwd)

if [[ "$OSTYPE" == "darwin"* ]]; then
    cpus=$(sysctl -n hw.ncpu)
else
    cpus=$(nproc)
fi

printf '%s\n' "${FILES[@]}" | xargs -n 1 -P "$cpus" -I {} bash -c 'download_and_replace "{}"'
