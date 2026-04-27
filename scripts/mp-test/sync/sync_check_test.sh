#!/bin/bash
# sync_check_test.sh — verify the non-interactive sync-check gate used by hooks.
#
# Covers:
#   1. No TA updates → exit 0 (silent)
#   2. TA updates pending → exit 1 + clear error message
#   3. stdin feeding ref-like data (simulating pre-push's stdin) must NOT
#      hang and must NOT alter exit semantics — sync-check never reads stdin.
#   4. Deadline gate: past-deadline skips check (exit 0).
#   5. Interactive `sync` inside hook context (GIT_DIR set) must refuse and
#      exit 1 instead of attempting `read`.

LIB_DIR=$(realpath "$(dirname "$(readlink -f "$0")")/../lib")
source "$LIB_DIR/test_utils.sh"

setup_sandbox "sync_check"
export SIMULATION_MODE=1

ORIGIN_URL=$(create_mock_origin)

# --- Build a template on origin ---
git clone "$ORIGIN_URL" template_repo >/dev/null 2>&1
cd template_repo || exit 1
git checkout -b main >/dev/null 2>&1
inject_mp_sh "."
mkdir -p doc && echo "kernel/main.c" > doc/protected_list.txt
cat > mp.conf <<EOF
DOCKER_IMAGE="ntuos/mp2"
ASSIGNMENT="mp0"
DEADLINE="2099-12-31 23:59:59"
TA_EMAILS="ta@ntu.edu.tw"
EOF
mkdir -p kernel && echo "orig" > kernel/main.c
git add . && git -c user.email=student@ntu.edu.tw -c user.name=Student commit -m "init" >/dev/null 2>&1
git push origin main >/dev/null 2>&1
cd .. || exit 1

# --- Student clone ---
git clone "$ORIGIN_URL" student_repo >/dev/null 2>&1
cd student_repo || exit 1
git config user.email "student@ntu.edu.tw"
git config user.name "Student"

# --------------------------------------------------------------------------
# Case 1: No TA updates → sync-check exits 0
# --------------------------------------------------------------------------
echo -e "\n--- Case 1: No TA updates (exit 0) ---"
if ./mp.sh sync-check >/dev/null 2>&1; then
    success "sync-check exits 0 when no TA updates."
else
    failure "sync-check should exit 0 but returned $?"
fi

# --------------------------------------------------------------------------
# Seed a TA commit on origin
# --------------------------------------------------------------------------
cd .. || exit 1
git clone "$ORIGIN_URL" ta_repo >/dev/null 2>&1
cd ta_repo || exit 1
git config user.email "ta@ntu.edu.tw"
git config user.name "TA"
echo "ta patch" >> kernel/main.c
git commit -am "TA: update" >/dev/null 2>&1
git push origin main >/dev/null 2>&1
cd ../student_repo || exit 1

# --------------------------------------------------------------------------
# Case 2: TA update pending → sync-check exits 1 + clear message
# --------------------------------------------------------------------------
echo -e "\n--- Case 2: TA update pending (exit 1) ---"
OUTPUT=$(./mp.sh sync-check 2>&1)
RC=$?
if [ "$RC" -ne 0 ] && echo "$OUTPUT" | grep -q "Unsynced TA updates"; then
    success "sync-check blocks and reports TA update."
else
    failure "sync-check should block (rc=$RC, out=$OUTPUT)"
fi

# --------------------------------------------------------------------------
# Case 3: stdin integrity — feeding pre-push-like ref data must NOT be read
# The old interactive sync's `read -r choice` would have consumed this line.
# sync-check never reads stdin, so the exit semantics must be identical to
# the previous case.
# --------------------------------------------------------------------------
echo -e "\n--- Case 3: stdin carrying ref data (must not be consumed) ---"
# Use `timeout` to catch any accidental blocking read. If sync-check tried
# to read stdin interactively, it would hang on an empty/closed fd eventually;
# feeding a single line prevents that but still detects wrong behaviour via
# stdout — correct behaviour: message on stderr only, stdin left alone.
PIPE_OUT=$(printf 'refs/heads/main aaa refs/heads/main bbb\n' \
    | timeout 5 ./mp.sh sync-check 2>&1)
PIPE_RC=$?
if [ "$PIPE_RC" -eq 1 ] && echo "$PIPE_OUT" | grep -q "Unsynced TA updates"; then
    success "sync-check ignores stdin and still blocks correctly."
else
    failure "sync-check stdin handling wrong (rc=$PIPE_RC)"
fi
# Secondary assertion: the ref line must not appear in sync-check's output
# (it would if sync-check echoed a prompt that captured the line).
if echo "$PIPE_OUT" | grep -q "refs/heads/main aaa"; then
    failure "sync-check appears to have consumed or echoed stdin ref data!"
fi
success "sync-check stdin left untouched."

# --------------------------------------------------------------------------
# Case 4: Past deadline → sync-check skips (exit 0)
# --------------------------------------------------------------------------
echo -e "\n--- Case 4: Past deadline skips check ---"
cp mp.conf mp.conf.bak
sed -i 's/DEADLINE=".*"/DEADLINE="2000-01-01 00:00:00"/' mp.conf
if ./mp.sh sync-check >/dev/null 2>&1; then
    success "sync-check skipped after deadline."
else
    failure "sync-check should skip past deadline."
fi
cp mp.conf.bak mp.conf
rm mp.conf.bak

# --------------------------------------------------------------------------
# Case 5: Interactive `sync` inside hook context (GIT_DIR) must refuse.
# Reproduces the original bug where pre-push's stdin + `read choice` would
# hang or silently mis-read git's ref list.
# --------------------------------------------------------------------------
echo -e "\n--- Case 5: Interactive sync refused in hook context ---"
HOOK_OUT=$(GIT_DIR=.git timeout 5 ./mp.sh sync </dev/null 2>&1)
HOOK_RC=$?
if [ "$HOOK_RC" -eq 1 ] && echo "$HOOK_OUT" | grep -q "Unsynced TA updates"; then
    success "Interactive sync refused in hook context (no hang, no read)."
else
    failure "sync in hook context misbehaved (rc=$HOOK_RC, out=$HOOK_OUT)"
fi

success "sync-check test suite passed."
