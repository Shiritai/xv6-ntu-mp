#!/bin/bash
# scripts/mp-test/lib/test_utils.sh - Shared utilities for testing

PROJECT_ROOT=$(realpath "$(dirname "$(readlink -f "$0")")/../../../")
SANDBOX_BASE="$PROJECT_ROOT/tmp/mp_test_sandbox"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

success() { echo -e "${GREEN}[PASS]${NC} $1"; }
failure() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

setup_sandbox() {
    local sandbox_name="$1"
    local sandbox_dir="$SANDBOX_BASE/$sandbox_name"
    
    rm -rf "$sandbox_dir"
    mkdir -p "$sandbox_dir"
    cd "$sandbox_dir" || exit 1
    
    # Export for sub-scripts
    export SANDBOX_DIR="$sandbox_dir"
}

create_mock_origin() {
    git init origin.git --bare >/dev/null 2>&1
    echo "$(pwd)/origin.git"
}

inject_mp_sh() {
    local target_dir="$1"
    cp "$PROJECT_ROOT/mp.sh" "$target_dir/"
    cp -r "$PROJECT_ROOT/scripts" "$target_dir/"
    chmod +x "$target_dir/mp.sh"
}

# Copy the grading harness (grade/ + a minimal tests/) into a sandbox target,
# so grade/run.py can be invoked inside the sandbox without touching the real
# project tree.
inject_grade() {
    local target_dir="$1"
    cp -r "$PROJECT_ROOT/grade" "$target_dir/"
    # Strip any stale pyc — the sandbox python uses the copied source.
    rm -rf "$target_dir/grade/__pycache__"
    mkdir -p "$target_dir/tests"
}
