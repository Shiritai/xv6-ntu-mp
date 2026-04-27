#!/bin/bash
# module_isolation_test.sh — proves that importing a test file never shadows
# a real module in sys.modules.
#
# Historically load_python_tests registered modules under their bare basename,
# and appended tests/ to sys.path. A student could drop tests/gradelib.py to
# replace the real grader. The fix namespaces every test module under the
# `_mp_test_` prefix and removes the sys.path mutation.

LIB_DIR=$(realpath "$(dirname "$(readlink -f "$0")")/../lib")
source "$LIB_DIR/test_utils.sh"

setup_sandbox "module_isolation"

REPO="$SANDBOX_DIR/repo"
mkdir -p "$REPO"
inject_grade "$REPO"

cat > "$REPO/mp.conf" <<EOF
DOCKER_IMAGE="ntuos/mp2"
ASSIGNMENT="mp0"
EOF
cat > "$REPO/student.conf" <<EOF
STUDENT_ID="b11111111"
STUDENT_NAME="Tester"
GITHUB_USERNAME="tester"
EOF

# A hostile file that, if loaded under the bare name `gradelib`, would replace
# the real grader in sys.modules and likely crash subsequent imports.
cat > "$REPO/tests/gradelib.py" <<'PYEOF'
import sys
# If this file shadows the real gradelib, anything importing `gradelib` after
# us will get this broken stub instead. Record our module name to verify the
# namespacing fix.
with open("loaded_as.txt", "w") as f:
    f.write(__name__)
# Poison the would-be shadow: no `test` symbol means `from gradelib import *`
# in any later file would fail noisily if we had taken over sys.modules.
PYEOF

# A harmless official test so there is a real @test registration to compare.
cat > "$REPO/tests/public_simple.py" <<'PYEOF'
from gradelib import test
@test(10, "simple")
def test_simple():
    return 10
PYEOF

# Match both files via grading.conf so they are both eligible for loading.
cat > "$REPO/tests/grading.conf" <<'EOF'
public_*.py
gradelib.py
EOF

echo -e "\n--- Running grader in sandbox ---"
(cd "$REPO" && python3 grade/run.py >/dev/null 2>&1)

# Assertion 1: the shadow file was imported under the namespaced name.
if [ ! -f "$REPO/loaded_as.txt" ]; then
    failure "tests/gradelib.py was never imported (filter may be too strict)."
fi
LOADED_AS=$(cat "$REPO/loaded_as.txt")
if [ "$LOADED_AS" != "_mp_test_gradelib" ]; then
    failure "tests/gradelib.py loaded as '$LOADED_AS' — expected '_mp_test_gradelib'. The namespacing fix is not in effect."
fi
success "tests/gradelib.py correctly loaded under namespaced module name."

# Assertion 2: directly confirm that a process importing `gradelib` from the
# sandbox root still resolves to the REAL gradelib (not the student's file).
# We point PYTHONPATH at grade/ so `import gradelib` finds the real one.
REAL_CHECK=$(cd "$REPO" && PYTHONPATH=grade python3 -c "
import gradelib
print('OK' if hasattr(gradelib, 'test') else 'SHADOWED')
" 2>&1)
if [ "$REAL_CHECK" != "OK" ]; then
    failure "Real gradelib was shadowed or broken: $REAL_CHECK"
fi
success "Real gradelib remains resolvable; no sys.modules pollution."

success "module isolation suite passed."
