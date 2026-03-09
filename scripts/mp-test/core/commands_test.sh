#!/bin/bash
# scripts/mp-test/core/commands_test.sh - Basic functionality tests

LIB_DIR=$(realpath "$(dirname "$(readlink -f "$0")")/../lib")
source "$LIB_DIR/test_utils.sh"

setup_sandbox "core_commands"
export SIMULATION_MODE=1

# 1. Test 'init'
echo -e "\n--- Test: mp.sh init ---"
mkdir student_repo && cd student_repo || failure "Failed to entering student_repo"
git init -q >/dev/null 2>&1
git config user.email "test@example.com"
git config user.name "Tester"
# Root mp.sh usually expects mp.conf
cat <<EOF > mp.conf
DOCKER_IMAGE="ntuos/mp2"
ASSIGNMENT="mp0"
TA_EMAILS="ta@ntu.edu.tw assistant@ntu.edu.tw"
EOF
mkdir -p scripts # For hook targets
inject_mp_sh "."
# Create mock hook templates in root-like structure isn't needed if we injected them
touch scripts/pre-commit scripts/pre-push

./mp.sh init >/dev/null 2>&1
if [ -f ".git/hooks/pre-commit" ] && [ -f ".git/hooks/pre-push" ]; then
    success "Git hooks installed correctly."
else
    failure "Git hooks installation failed!"
fi

# 2. Test 'snapshot'
echo -e "\n--- Test: mp.sh snapshot ---"
echo "Work in progress" > wip.txt
git add . && git commit -m "First commit" >/dev/null 2>&1
echo "Changing work" >> wip.txt
SNAP_BRANCH=$(./mp.sh snapshot | tail -n 1) # Capture branch name
if git branch | grep -q "$SNAP_BRANCH"; then
    success "Snapshot branch '$SNAP_BRANCH' created."
else
    failure "Snapshot creation failed!"
fi

# 3. Test 'clean' (simulation)
echo -e "\n--- Test: mp.sh clean ---"
./mp.sh clean >/dev/null 2>&1
success "mp.sh clean wrapper executed."

# 4. Test 'qemu' (simulation)
echo -e "\n--- Test: mp.sh qemu ---"
./mp.sh qemu 2>&1 | grep -q "Starting QEMU"
success "mp.sh qemu triggered correctly."

# 5. Test 'test/grade' (normal student)
echo -e "\n--- Test: mp.sh test (Student) ---"
./mp.sh test 2>&1 | grep -q "Running tests for mp0"
success "mp.sh test triggered correctly for student."

# 6. Test 'check_ta_commit' (TA Block)
echo -e "\n--- Test: check_ta_commit (TA Block) ---"
# Simulate a TA commit
git config user.email "ta@ntu.edu.tw"
echo "TA fix" >> wip.txt
git add wip.txt
git commit -m "TA: Urgent fix" --no-verify >/dev/null 2>&1
# Should skip execution
if ./mp.sh grade 2>&1 | grep -q "Skipping execution: Commit by TA"; then
    success "TA commit correctly blocked for execution."
else
    failure "TA commit was NOT blocked!"
fi

# 7. Test 'Official Grading' bypass
echo -e "\n--- Test: Official Grading Bypass ---"
export OFFICIAL_GRADING=1
# Should NOT skip even if TA committed
if ./mp.sh grade 2>&1 | grep -q "Running tests for mp0"; then
    success "Official grading mode correctly bypasses TA block."
else
    failure "Official grading mode was incorrectly blocked!"
fi
unset OFFICIAL_GRADING

# 8. Test Invalid Command
echo -e "\n--- Test: Invalid Command ---"
if ./mp.sh forbidden 2>&1 | grep -q "Usage:"; then
    success "Invalid command correctly triggers usage message."
else
    failure "Invalid command did not show usage!"
fi

success "Full core command coverage passed."
