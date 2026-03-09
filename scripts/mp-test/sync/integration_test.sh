#!/bin/bash
# scripts/mp-test/sync/integration_test.sh - V7 logic as a formal test

LIB_DIR=$(realpath "$(dirname "$(readlink -f "$0")")/../lib")
source "$LIB_DIR/test_utils.sh"

setup_sandbox "sync_integration"
export SIMULATION_MODE=1

# 1. Setup Mock Upstream
ORIGIN_URL=$(create_mock_origin)

# 2. Push Initial Template
git clone "$ORIGIN_URL" template_repo >/dev/null 2>&1
cd template_repo || exit 1
git checkout -b main >/dev/null 2>&1
inject_mp_sh "."
mkdir -p doc && echo "kernel/main.c" > doc/protected_list.txt
cat <<EOF > mp.conf
DOCKER_IMAGE="ntuos/mp2"
ASSIGNMENT="mp0"
DEADLINE="2026-12-31 23:59:59"
TA_EMAILS="ta@ntu.edu.tw assistant@ntu.edu.tw"
EOF
mkdir -p kernel && echo "Original kernel code" > kernel/main.c
git add . && git commit -m "Initial template" >/dev/null 2>&1
git push origin main >/dev/null 2>&1
cd .. || exit 1

# 3. Student Repo
git clone "$ORIGIN_URL" student_repo >/dev/null 2>&1
cd student_repo || exit 1
git config user.email "student@ntu.edu.tw"
git config user.name "Student"
./mp.sh init >/dev/null 2>&1
echo "Student logic" > student_work.c
git add . && git commit -m "Student work" >/dev/null 2>&1

# 4. TA Update
cd .. || exit 1
git clone "$ORIGIN_URL" ta_repo >/dev/null 2>&1
cd ta_repo || exit 1
git config user.email "ta@ntu.edu.tw"
echo "TA: Bug fix" >> kernel/main.c
git add . && git commit -m "TA update" >/dev/null 2>&1
git push origin main >/dev/null 2>&1
cd .. || exit 1

# ------------------------------------------------------------------------------
# Integration Scenarios
# ------------------------------------------------------------------------------
cd student_repo || exit 1

# Scenario 1: Intercept Command
echo -e "\n--- Scenario 1: Command Blocking ---"
if ./mp.sh grade 2>&1 | grep -q "Unsynced TA updates detected"; then
    success "Command blocked in Non-TTY correctly."
else
    failure "Command was NOT blocked!"
fi

# Scenario 2: Full Sync
echo -e "\n--- Scenario 2: Successful Sync ---"
echo "Dirty student fix" >> student_work.c
export IGNORE_TTY_CHECK=1
if echo "y" | ./mp.sh sync 2>&1 | grep -q "Update applied"; then
    success "Sync command completed."
else
    failure "Sync command failed!"
fi

# Scenario 3: Work Restored
echo -e "\n--- Scenario 3: Data Integrity ---"
if grep -q "TA: Bug fix" kernel/main.c && grep -q "Dirty student fix" student_work.c; then
    success "TA changes merged and student dirty work restored."
else
    failure "Data lost after sync!"
fi

success "Sync integration tests passed."
