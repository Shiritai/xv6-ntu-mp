#!/bin/bash
# pin_graded_sources_test.sh — verify the C1 anti-cheat restore mechanic.
#
# The official-grading scenario:
#   target_sha = student's pre-deadline submission
#   GRADING_SHA = TA's pristine harness with private tests injected
#
# After pinning, the worktree must end up with:
#   - student source files restored from target_sha
#   - TA-owned harness (protected_list.txt) kept at GRADING_SHA
#   - TA-injected files (present in GRADING_SHA but absent in target_sha) intact
#
# Also exercises the fail-closed guard on an empty protected_list (R1).

LIB_DIR=$(realpath "$(dirname "$(readlink -f "$0")")/../lib")
source "$LIB_DIR/test_utils.sh"

setup_sandbox "pin_graded_sources"

REPO="$SANDBOX_DIR/repo"
PIN="$PROJECT_ROOT/scripts/pin-graded-sources"

mkdir -p "$REPO" && cd "$REPO"
git init -q && git config user.email "t@t.t" && git config user.name "T"
mkdir -p grade kernel user doc scripts .github/workflows

# ----- target commit: student-v1 work + pristine v1 harness -----
echo "PRISTINE-v1" > grade/run.py
echo "PRISTINE-v1" > mp.sh
echo "student-v1"  > kernel/proc.c
echo "STUDENT_ID=12345" > student.conf
echo "- [x] done" > checklist.md
cat > doc/protected_list.txt <<EOF
mp.sh
grade/
.github/workflows/grading.yml
scripts/pin-graded-sources
EOF
cp "$PIN" scripts/pin-graded-sources && chmod +x scripts/pin-graded-sources
git add -A && git commit -q -m "target"
TARGET=$(git rev-parse HEAD)

# ----- grading commit: TA's updated harness + injected private test -----
echo "PRISTINE-v2-TA-UPDATED" > grade/run.py
echo "private-grading-workflow" > .github/workflows/grading.yml
mkdir -p tests
echo "private content" > tests/private_test.py
git add -A && git commit -q -m "grading (TA harness + private)"
GRADING=$(git rev-parse HEAD)

# ----- Run pin -----
TARGET_SHA="$TARGET" bash scripts/pin-graded-sources > /tmp/pin_out.log 2>&1 \
    || failure "pin-graded-sources exited non-zero: $(cat /tmp/pin_out.log)"

# Expectations
[ "$(cat grade/run.py)" = "PRISTINE-v2-TA-UPDATED" ] \
    && success "TA harness (grade/run.py) kept at GRADING_SHA" \
    || failure "grade/run.py was overwritten — harness boundary broken"

[ "$(cat kernel/proc.c)" = "student-v1" ] \
    && success "student source (kernel/proc.c) restored from target_sha" \
    || failure "kernel/proc.c = $(cat kernel/proc.c), expected student-v1"

[ "$(cat student.conf)" = "STUDENT_ID=12345" ] \
    && success "student.conf restored from target_sha" \
    || failure "student.conf not restored as expected"

[ "$(cat .github/workflows/grading.yml)" = "private-grading-workflow" ] \
    && success "protected grading.yml kept at GRADING_SHA" \
    || failure "protected grading.yml was changed"

[ -f tests/private_test.py ] \
    && success "TA-injected file (tests/private_test.py) survives the restore" \
    || failure "TA-injected file was removed by restore"

# ----- TARGET == HEAD: no-op early exit -----
cd "$REPO"
TARGET_SHA="$GRADING" bash scripts/pin-graded-sources > /tmp/pin_noop.log 2>&1 \
    || failure "no-op path failed: $(cat /tmp/pin_noop.log)"
grep -q "nothing to pin" /tmp/pin_noop.log \
    && success "TARGET == HEAD short-circuits cleanly" \
    || failure "no-op path did not print expected message"

# ----- Missing TARGET_SHA: explicit error -----
out=$(bash scripts/pin-graded-sources 2>&1); rc=$?
[ "$rc" -ne 0 ] && echo "$out" | grep -q "TARGET_SHA" \
    && success "missing TARGET_SHA errors out clearly" \
    || failure "missing TARGET_SHA did not fail loudly (rc=$rc, out=$out)"

# ----- R1: empty PROTECTED list must fail closed -----
# Erase protected_list.txt in the GRADING commit, then attempt to pin.
: > doc/protected_list.txt
git add -A && git commit -q -m "break protected_list (test)"
EMPTY_GRADING=$(git rev-parse HEAD)
out=$(TARGET_SHA="$TARGET" bash scripts/pin-graded-sources 2>&1); rc=$?
[ "$rc" -ne 0 ] && echo "$out" | grep -qi "protected_list" \
    && success "empty protected_list fails closed (refuses to restore)" \
    || failure "empty protected_list did NOT fail closed (rc=$rc, out=$out)"

success "pin-graded-sources test suite passed."
