#!/bin/bash
# hook_stdin_test.sh — the critical regression test for Issue 1.
#
# Git feeds pre-push's stdin with a ref list. The old code ran an interactive
# `./mp.sh sync` here, whose `read -r choice` would consume git's data and
# either bypass update detection or leave the hook's own `while read` loop
# starved (silently breaking protected-file checks).
#
# This test invokes the real pre-push hook with a realistic stdin payload
# and asserts:
#   (a) hook exits 1 when TA updates are pending,
#   (b) the hook's output references TA updates (sync-check fired),
#   (c) the hook's own ref-reading loop NEVER sees the stdin if sync-check
#       is doing its job correctly (sync-check exits 1 first, so the push
#       is rejected before protected-file checks — that's fine).

LIB_DIR=$(realpath "$(dirname "$(readlink -f "$0")")/../lib")
source "$LIB_DIR/test_utils.sh"

setup_sandbox "hook_stdin"
export SIMULATION_MODE=1

ORIGIN_URL=$(create_mock_origin)

# --- Template ---
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

# --- Student clone + install hooks ---
git clone "$ORIGIN_URL" student_repo >/dev/null 2>&1
cd student_repo || exit 1
git config user.email "student@ntu.edu.tw"
git config user.name "Student"
./mp.sh init >/dev/null 2>&1
[ -x .git/hooks/pre-push ] || failure "pre-push hook not installed"

# --- TA pushes update ---
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
# Case 1: pre-push hook fed ref list on stdin — must block, must not hang.
#
# This is the exact scenario the old code broke under. `timeout` guards
# against a regression where sync attempts `read` and blocks forever on a
# closed stdin.
# --------------------------------------------------------------------------
echo -e "\n--- Case 1: pre-push with ref stdin blocks on TA update ---"
LOCAL_SHA=$(git rev-parse HEAD)
STDIN_PAYLOAD="refs/heads/main $LOCAL_SHA refs/heads/main 0000000000000000000000000000000000000000"

HOOK_OUT=$(printf '%s\n' "$STDIN_PAYLOAD" | timeout 8 .git/hooks/pre-push origin "$ORIGIN_URL" 2>&1)
HOOK_RC=$?

if [ "$HOOK_RC" -eq 124 ]; then
    failure "pre-push HUNG (timeout) — sync-check likely tried to read stdin!"
fi
if [ "$HOOK_RC" -ne 1 ]; then
    failure "pre-push should exit 1 on TA update, got rc=$HOOK_RC. Output: $HOOK_OUT"
fi
if ! echo "$HOOK_OUT" | grep -q "Unsynced TA updates"; then
    failure "pre-push did not surface sync-check error. Output: $HOOK_OUT"
fi
success "pre-push blocks on TA update without hanging."

# --------------------------------------------------------------------------
# Case 2: Real `git push` invocation — end-to-end.
# --------------------------------------------------------------------------
echo -e "\n--- Case 2: git push end-to-end is rejected ---"
echo "student work" > some_file.c
git add some_file.c
git -c core.hooksPath=/dev/null commit -m "student edit" >/dev/null 2>&1

PUSH_OUT=$(timeout 15 git push origin main 2>&1)
PUSH_RC=$?
if [ "$PUSH_RC" -eq 0 ]; then
    failure "git push should have been rejected by pre-push hook. Output: $PUSH_OUT"
fi
if ! echo "$PUSH_OUT" | grep -q "Unsynced TA updates"; then
    failure "git push failure message lacks sync-check context. Output: $PUSH_OUT"
fi
success "git push is cleanly rejected with actionable message."

# --------------------------------------------------------------------------
# Case 3: pre-commit with GUI-like non-TTY stdin — must not hang.
# --------------------------------------------------------------------------
echo -e "\n--- Case 3: pre-commit with closed stdin does not hang ---"
echo "x" > commit_target.c
git add commit_target.c
COMMIT_OUT=$(timeout 8 git commit -m "try" </dev/null 2>&1)
COMMIT_RC=$?
if [ "$COMMIT_RC" -eq 124 ]; then
    failure "pre-commit HUNG on closed stdin!"
fi
if [ "$COMMIT_RC" -eq 0 ]; then
    failure "pre-commit should reject when TA updates pending."
fi
if ! echo "$COMMIT_OUT" | grep -q "Unsynced TA updates"; then
    failure "pre-commit lacks actionable error. Output: $COMMIT_OUT"
fi
success "pre-commit rejects without hanging on closed stdin."

success "Hook stdin integrity suite passed."
