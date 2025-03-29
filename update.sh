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
    "test/public"
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

TEMP_REPO_DIR="${SCRIPT_DIR}/../_xv6-ntu-mp2"
REPO_URL="https://github.com/Shiritai/xv6-ntu-mp2.git"

cleanup() {
    if [[ -d "${TEMP_REPO_DIR}" ]]; then
        rm -rf "${TEMP_REPO_DIR}" || echo "Warning: Failed to remove temporary directory ${TEMP_REPO_DIR}"
    fi
}

trap 'echo "Script interrupted"; cleanup; exit 1' INT TERM

main() {
    if ! command -v git &> /dev/null; then
        echo "Error: git is not installed or not in PATH"
        exit 1
    fi

    if [[ -d "${TEMP_REPO_DIR}" ]]; then
        echo "Error: ${TEMP_REPO_DIR} already exists"
        echo "Please remove or rename it before running this script"
        exit 1
    fi

    echo "Cloning repository from ${REPO_URL}..."
    if ! git clone "${REPO_URL}" "${TEMP_REPO_DIR}"; then
        echo "Error: Failed to clone repository"
        exit 1
    fi

    if ! cd "${TEMP_REPO_DIR}"; then
        echo "Error: Cannot change to directory ${TEMP_REPO_DIR}"
        cleanup
        exit 1
    fi

    echo "Current directory: $(pwd)"

    for file in "${FILES[@]}"; do
        if [[ -z "${file}" ]]; then
            echo "Warning: Empty file entry in FILES array"
            continue
        fi

        if [[ -d "${file}" ]]; then
            echo "Updating directory ${file} if needed..."
            mkdir -p "${SCRIPT_DIR}/${file}" || echo "Warning: Failed to create directory ${SCRIPT_DIR}/${file}"
            cp -r "${file}"/* "${SCRIPT_DIR}/${file}" 2>/dev/null || echo "Warning: Failed to copy some files from ${file}"
        elif [[ -f "${file}" ]]; then
            diff -q "${file}" "${SCRIPT_DIR}/${file}" >/dev/null 2>&1 || (
                echo "Updating file ${file}..."
                mkdir -p "$(dirname "${SCRIPT_DIR}/${file}")" || echo "Warning: Failed to create directory for ${file}"
                cp "${file}" "${SCRIPT_DIR}/${file}" 2>/dev/null || echo "Warning: Failed to copy ${file}"
            )
        else
            echo "Warning: ${file} not found in repository"
        fi
    done

    if [[ -d "doc" ]]; then
        echo "Updating documentation if needed..."
        mkdir -p "${SCRIPT_DIR}/doc" || echo "Warning: Failed to create doc directory"
        cp -r doc/* "${SCRIPT_DIR}/doc" 2>/dev/null || echo "Warning: Failed to copy documentation"
    fi

    if ! cd "${SCRIPT_DIR}"; then
        echo "Error: Cannot return to ${SCRIPT_DIR}"
        cleanup
        exit 1
    fi

    cleanup
    echo "Script completed successfully"
}

main
