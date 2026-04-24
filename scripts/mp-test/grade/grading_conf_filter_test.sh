#!/bin/bash
# grading_conf_filter_test.sh — regression test for Issue 2.
#
# Proves that grade/run.py only IMPORTS test files matched by grading.conf.
# An unmatched file in tests/ must not execute top-level code, so malicious
# or broken student-authored tests cannot poison gradelib state, clear the
# TESTS registry, or inflate the score.
#
# Each case runs in its own sandbox subdir with a fresh grade/ + tests/ copy.

LIB_DIR=$(realpath "$(dirname "$(readlink -f "$0")")/../lib")
source "$LIB_DIR/test_utils.sh"

setup_sandbox "grading_conf_filter"

# Shared fixture — evil test file that unambiguously marks its execution.
# It touches a marker file, clears TESTS, and attempts to inflate TOTAL.
write_evil_test() {
    local dst="$1"
    local marker="$2"
    cat > "$dst" <<PYEOF
import gradelib
open(r"$marker", "w").close()
gradelib.TESTS.clear()
gradelib.TOTAL = 999999
PYEOF
}

# A harmless official test that registers one test worth 10 points.
write_official_test() {
    local dst="$1"
    cat > "$dst" <<'PYEOF'
from gradelib import test

@test(10, "public_basic")
def test_basic():
    return 10
PYEOF
}

# Set up a minimal repo layout inside a given dir so grade/run.py can execute.
# Returns via globals: LAST_REPO, LAST_MARKER.
prepare_repo() {
    local name="$1"
    local grading_conf_body="$2"
    local repo="$SANDBOX_DIR/$name"
    local marker="$SANDBOX_DIR/${name}_EVIL_MARKER"
    rm -rf "$repo"
    mkdir -p "$repo"
    inject_grade "$repo"

    cat > "$repo/mp.conf" <<EOF
DOCKER_IMAGE="ntuos/mp2"
ASSIGNMENT="mp0"
EOF
    # Identity must be non-default or run.py zeros the score.
    cat > "$repo/student.conf" <<EOF
STUDENT_ID="b11111111"
STUDENT_NAME="Sandbox Tester"
GITHUB_USERNAME="sandbox-tester"
EOF

    echo "$grading_conf_body" > "$repo/tests/grading.conf"
    write_official_test "$repo/tests/public_basic.py"
    write_evil_test "$repo/tests/student_custom.py" "$marker"

    LAST_REPO="$repo"
    LAST_MARKER="$marker"
}

# Run run.py inside the repo; ignore its rc (make will fail in the sandbox —
# we only care about side effects of test loading).
run_grader() {
    (cd "$LAST_REPO" && python3 grade/run.py >/dev/null 2>&1)
    return 0
}

# --------------------------------------------------------------------------
# Case 1: Wildcard grading.conf — sanity check that the evil file CAN load.
# Demonstrates the attack surface exists; the fix in Case 2 must suppress it.
# --------------------------------------------------------------------------
echo -e "\n--- Case 1: Wildcard conf loads evil file (attack surface) ---"
prepare_repo "wildcard" "*.py"
run_grader
if [ -f "$LAST_MARKER" ]; then
    success "Wildcard conf loaded evil file (attack surface confirmed)."
else
    failure "Wildcard conf should have loaded evil file — fixture may be broken."
fi

# --------------------------------------------------------------------------
# Case 2: Narrow grading.conf (TA-style) — evil file MUST NOT load.
# This is the core fix: unmatched files are not imported.
# --------------------------------------------------------------------------
echo -e "\n--- Case 2: Narrow conf blocks evil file (the fix) ---"
prepare_repo "narrow" "public_*.py"
run_grader
if [ -f "$LAST_MARKER" ]; then
    failure "Evil file was imported despite narrow grading.conf!"
else
    success "Evil file blocked: grading.conf enforced as whitelist."
fi

# --------------------------------------------------------------------------
# Case 3: Blank / missing grading.conf falls back to *.py *.txt default.
# Evil file SHOULD load (documented default behaviour for local dev).
# --------------------------------------------------------------------------
echo -e "\n--- Case 3: Missing grading.conf uses permissive default ---"
prepare_repo "empty" ""
rm "$LAST_REPO/tests/grading.conf"
run_grader
if [ -f "$LAST_MARKER" ]; then
    success "Missing conf correctly defaults to permissive wildcard."
else
    failure "Missing conf should have used permissive default."
fi

# --------------------------------------------------------------------------
# Case 4: Script-based (.txt) tests also filtered.
# --------------------------------------------------------------------------
echo -e "\n--- Case 4: grading.conf also filters .txt script tests ---"
prepare_repo "txt_filter" "public_*.py"
# Add a .txt that would register a script test if loaded; the filter must
# keep it out of the TESTS registry. We detect via run.py JSON report.
echo "ls" > "$LAST_REPO/tests/student_script.txt"
REPORT="$LAST_REPO/report.json"
(cd "$LAST_REPO" && python3 grade/run.py --json "$REPORT" >/dev/null 2>&1)
if [ -f "$REPORT" ] && ! grep -q "student_script" "$REPORT"; then
    success "Unmatched .txt excluded from TESTS registry."
else
    failure "Unmatched .txt script was registered (found in report)."
fi

success "grading.conf filter suite passed."
