#!/bin/bash
# scripts/mp-test/run_all.sh - Master Test Runner

PROJECT_ROOT=$(realpath "$(dirname "$(readlink -f "$0")")/../../")
TEST_DIR="$PROJECT_ROOT/scripts/mp-test"
source "$TEST_DIR/lib/test_utils.sh"

echo -e "${BOLD}=== xv6-ntu-mp Management Script Test Suite ===${NC}\n"

TOTAL_TESTS=0
FAILED_TESTS=0

run_test() {
    local test_script="$1"
    echo -e "${BLUE}Running: $(basename "$test_script")${NC}"
    if bash "$test_script"; then
        echo -e "${GREEN}Result: SUCCESS${NC}\n"
    else
        echo -e "${RED}Result: FAILED${NC}\n"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

# Discover every *_test.sh under TEST_DIR (one level deep, any subdir).
# New categories (e.g. grade/) are picked up automatically — no edit needed.
while IFS= read -r -d '' t; do
    run_test "$t"
done < <(find "$TEST_DIR" -mindepth 2 -name '*_test.sh' -type f -print0 | sort -z)

echo -e "${BOLD}--- Test Summary ---${NC}"
echo "Total Suites: $TOTAL_TESTS"
if [ "$FAILED_TESTS" -eq 0 ]; then
    echo -e "${GREEN}Status: ALL TESTS PASSED${NC}"
    exit 0
else
    echo -e "${RED}Status: $FAILED_TESTS SUITE(S) FAILED${NC}"
    exit 1
fi
