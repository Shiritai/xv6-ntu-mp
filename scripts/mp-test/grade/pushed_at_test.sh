#!/bin/bash
# pushed_at_test.sh — verify_committer + run.py interplay around the
# authoritative push time (audit K1).
#
# Locally we can't reach the GitHub API, so we exercise:
#  (a) verify_committer writes pushed_at=null / source=unavailable cleanly
#      when GITHUB_TOKEN is absent;
#  (b) run.py gather_verdict refuses to compute late_days from anything other
#      than the server-stamped push time (strict fail-closed, audit D1).

LIB_DIR=$(realpath "$(dirname "$(readlink -f "$0")")/../lib")
source "$LIB_DIR/test_utils.sh"

setup_sandbox "pushed_at"

REPO="$SANDBOX_DIR/repo"
mkdir -p "$REPO" && cd "$REPO"
git init -q && git config user.email "student@x" && git config user.name "Student"
inject_grade "$REPO"

cat > "$REPO/mp.conf" <<EOF
ASSIGNMENT="mp0"
DEADLINE="2026-06-30T23:59:59+08:00"
TA_EMAILS="ta_lead@ntu.edu.tw"
EOF
cat > "$REPO/student.conf" <<EOF
STUDENT_ID="b11111111"
STUDENT_NAME="Tester"
GITHUB_USERNAME="tester"
EOF

# Two commits: an "init" by TA, a "student work" by the student.
echo init > a; git add a
git commit -q -m "ta init" --author="ta_lead@ntu.edu.tw <ta_lead@ntu.edu.tw>"
echo work > a; git add a; git commit -q -m "student work"

# (a) No GITHUB_TOKEN -> source=unavailable, pushed_at=null
unset GITHUB_TOKEN GITHUB_REPOSITORY
python3 grade/verify_committer.py > /dev/null 2>&1 || true
src=$(python3 -c "import json; print(json.load(open('target_commit.json'))['pushed_at_source'])")
pa=$(python3 -c "import json; print(json.load(open('target_commit.json'))['pushed_at'])")
[ "$src" = "unavailable" ] && [ "$pa" = "None" ] \
    && success "no-token path writes pushed_at=null, source=unavailable" \
    || failure "expected unavailable/null, got source=$src pushed_at=$pa"

# (b) Strict fail-closed: pushed_at=null but DEADLINE in the past — late_days
# must be 0 (not computed from forgeable committer time) AND verified=False.
# Use a deadline in 2020 so committer time (today) would be very late.
cat > mp.conf <<EOF
ASSIGNMENT="mp0"
DEADLINE="2020-01-01T00:00:00+00:00"
TA_EMAILS="ta_lead@ntu.edu.tw"
EOF
python3 -c "
import sys; sys.path.insert(0, 'grade')
import run
v = run.gather_verdict()
assert v['late_days'] == 0, f'late_days={v[\"late_days\"]}, expected 0 (strict)'
assert v['submission_verified'] is False, 'verified should be False'
print('OK')
" > /tmp/out.log 2>&1 && success "strict path: late_days stays 0 when push time is unverified" \
    || failure "$(cat /tmp/out.log)"

# (c) Strict positive: forge a target_commit.json with a real pushed_at far
# past the deadline. Lateness must come from pushed_at, not committer ts.
cat > target_commit.json <<EOF
{ "sha":"abc", "author":"s@x", "timestamp": 946684800, "pushed_at": 1735689600, "pushed_at_source": "actions_runs" }
EOF
python3 -c "
import sys; sys.path.insert(0, 'grade')
import run
v = run.gather_verdict()
assert v['late_days'] > 0, f'late_days={v[\"late_days\"]}, expected > 0 (from pushed_at)'
assert v['submission_verified'] is True, 'verified should be True'
print('OK')
" > /tmp/out.log 2>&1 && success "positive path: late_days computed from server pushed_at" \
    || failure "$(cat /tmp/out.log)"

success "pushed_at test suite passed."
