#!/usr/bin/env python3
"""Discover tests and emit GitHub Actions outputs (matrix, has_bonus).

Replaces the inline `python3 -c` snippets in the Discover Tests CI step.
Usage:
    python3 grade/discover.py            # prints to GITHUB_OUTPUT
    python3 grade/discover.py --stdout   # prints JSON to stdout (for debugging)
"""

import sys
import os
import json
import re
import argparse

# Ensure grade/ and project root are importable
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gradelib
from run import load_grading_config, load_script_tests, load_python_tests

TEST_DIR = os.environ.get("TEST_DIR", "tests")


def slugify(title):
    """Convert a test title to a filesystem-safe slug."""
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', title).strip('-').lower()
    return slug or 'unnamed'


def discover_tests_json(bonus_keywords=None):
    """Return two lists: (regular_tests, bonus_tests) as JSON-serializable dicts.

    Each entry carries an 'order' field that reflects the original registration
    order in gradelib.TESTS (set by the @test decorator during module load).
    The aggregate script uses this to reproduce the canonical report order.
    """
    if bonus_keywords is None:
        bonus_keywords = ["bonus", "Bonus"]
    regular = []
    bonus = []
    for idx, t in enumerate(gradelib.TESTS):
        title = getattr(t, "title", t.__name__)
        if not title:  # skip end_part markers
            continue
        points = getattr(t, "points", 0)
        entry = {
            "name": title,
            "pattern": title,
            "slug": slugify(title),
            "points": points,
            "order": idx,
        }
        if any(kw in title for kw in bonus_keywords):
            bonus.append(entry)
        else:
            regular.append(entry)
    return regular, bonus


def main():
    parser = argparse.ArgumentParser(description="Discover tests for CI matrix")
    parser.add_argument("--stdout", action="store_true",
                        help="Print raw JSON to stdout instead of GITHUB_OUTPUT")
    args = parser.parse_args()

    if not os.path.isdir(TEST_DIR):
        print(f"Warning: Test directory '{TEST_DIR}' not found.", file=sys.stderr)
        sys.exit(0)

    patterns = load_grading_config()
    load_script_tests(TEST_DIR, patterns)
    load_python_tests(TEST_DIR, patterns)

    regular, bonus = discover_tests_json()

    if args.stdout:
        json.dump({"regular": regular, "bonus": bonus}, sys.stdout, indent=2)
        sys.exit(0)

    matrix = json.dumps(regular)
    has_bonus = "true" if bonus else "false"

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"matrix={matrix}\n")
            f.write(f"has_bonus={has_bonus}\n")

    print(f"Discovered {len(regular)} regular tests")
    print(f"Has bonus tests: {has_bonus}")


if __name__ == "__main__":
    main()
