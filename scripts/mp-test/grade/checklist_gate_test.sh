#!/bin/bash
# checklist_gate_test.sh — validate_checklist fails closed on absence.
#
# The template ships checklist.md.template. TAs must rename and edit it.
# If checklist.md is missing, it must NOT count as completed. Earlier the function returned
# True when the file was absent, silently bypassing the gate (audit C2).

LIB_DIR=$(realpath "$(dirname "$(readlink -f "$0")")/../lib")
source "$LIB_DIR/test_utils.sh"

setup_sandbox "checklist_gate"

REPO="$SANDBOX_DIR/repo"
mkdir -p "$REPO"
inject_grade "$REPO"

run_validate() {
    # $1: the test name to print; $2: the path to test (or "" to test missing).
    local label="$1" path="$2"
    cd "$REPO"
    python3 -c "
import sys
sys.path.insert(0, 'grade')
import run
print(run.validate_checklist('$path'))
"
}

# Case 1: missing file -> False
out=$(run_validate "missing" "/no/such/file.md")
[ "$out" = "False" ] && success "missing checklist.md is rejected (fail-closed)" \
    || failure "missing checklist.md returned $out, expected False"

# Case 2: unticked items -> False
cat > "$REPO/cl_unticked.md" <<EOF
# Checklist
- [ ] item one
- [x] item two
EOF
out=$(run_validate "unticked" "$REPO/cl_unticked.md")
[ "$out" = "False" ] && success "unticked checklist is rejected" \
    || failure "unticked checklist returned $out, expected False"

# Case 3: all ticked -> True
cat > "$REPO/cl_ticked.md" <<EOF
# Checklist
- [x] item one
- [x] item two
EOF
out=$(run_validate "ticked" "$REPO/cl_ticked.md")
[ "$out" = "True" ] && success "fully ticked checklist passes" \
    || failure "ticked checklist returned $out, expected True"

# Case 4: empty file -> True (no unticked items)
: > "$REPO/cl_empty.md"
out=$(run_validate "empty" "$REPO/cl_empty.md")
[ "$out" = "True" ] && success "empty checklist passes (no unticked items)" \
    || failure "empty checklist returned $out, expected True"

success "validate_checklist gate test suite passed."
