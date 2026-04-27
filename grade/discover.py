#!/usr/bin/env python3
"""Discover tests, validate dependency DAG, and emit GitHub Actions outputs.

Outputs (to GITHUB_OUTPUT or --stdout):
  cycle_detected    true|false
  wave_0_matrix     JSON array of test entries for level 0 (no dependencies)
  wave_1_matrix     JSON array of test entries for level 1
  has_wave_1        true|false
  wave_seq_matrix   JSON array of test entries for depth >= 2 (sequential overflow)
  has_wave_seq      true|false

Usage:
    python3 grade/discover.py            # writes to GITHUB_OUTPUT
    python3 grade/discover.py --stdout   # prints JSON to stdout (for debugging)
"""

import sys
import os
import json
import re
import argparse

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gradelib
from run import load_grading_config, load_script_tests, load_python_tests

TEST_DIR = os.environ.get("TEST_DIR", "tests")
MAX_PARALLEL_WAVES = 2


def slugify(title):
    """Convert a test title to a filesystem-safe slug."""
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', title).strip('-').lower()
    return slug or 'unnamed'


def build_waves(tests):
    """Topological sort of tests by their `needs` dependencies (Kahn's algorithm).

    Returns (parallel_waves, overflow, cycle_detected) where:
      parallel_waves  list of lists of titles, length <= MAX_PARALLEL_WAVES
      overflow        flat list of titles in topo order for depth >= MAX_PARALLEL_WAVES
      cycle_detected  bool
    """
    title_map = {}
    for t in tests:
        title = getattr(t, 'title', t.__name__)
        if title:
            title_map[title] = t

    dependents = {title: [] for title in title_map}
    in_degree  = {title: 0  for title in title_map}

    for title, t in title_map.items():
        for dep in getattr(t, 'needs', []):
            if dep not in title_map:
                print(f"Warning: test '{title}' depends on unknown test '{dep}' — ignored",
                      file=sys.stderr)
                continue
            dependents[dep].append(title)
            in_degree[title] += 1

    waves = []
    processed = []
    current = [t for t, d in in_degree.items() if d == 0]

    while current:
        waves.append(current)
        processed.extend(current)
        nxt = []
        for title in current:
            for dep in dependents[title]:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    nxt.append(dep)
        current = nxt

    if len(processed) != len(title_map):
        return None, None, True

    parallel = waves[:MAX_PARALLEL_WAVES]
    overflow = [t for wave in waves[MAX_PARALLEL_WAVES:] for t in wave]
    return parallel, overflow, False


def make_entry(title, tests_by_title, order_map):
    t = tests_by_title[title]
    return {
        "name":    title,
        "pattern": title,
        "slug":    slugify(title),
        "points":  getattr(t, 'points', 0),
        "order":   order_map.get(title, 9999),
    }


def discover_tests_json():
    """Return per-wave lists and overflow list as JSON-serializable dicts."""
    tests = gradelib.TESTS
    title_map = {}
    order_map = {}
    for idx, t in enumerate(tests):
        title = getattr(t, 'title', t.__name__)
        if title:
            title_map[title] = t
            order_map[title] = idx

    parallel_waves, overflow, cycle = build_waves(tests)

    if cycle:
        return None, None, None, True

    wave_lists = []
    for wave in parallel_waves:
        wave_lists.append([make_entry(t, title_map, order_map) for t in wave])

    # Pad to MAX_PARALLEL_WAVES so callers always have wave_lists[0] and wave_lists[1]
    while len(wave_lists) < MAX_PARALLEL_WAVES:
        wave_lists.append([])

    overflow_entries = [make_entry(t, title_map, order_map) for t in overflow]

    return wave_lists, overflow_entries, False


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

    wave_lists, overflow_entries, cycle = discover_tests_json()

    if args.stdout:
        if cycle:
            json.dump({"cycle_detected": True}, sys.stdout, indent=2)
        else:
            json.dump({
                "cycle_detected": False,
                "waves": wave_lists,
                "overflow": overflow_entries,
            }, sys.stdout, indent=2)
        sys.exit(0)

    if cycle:
        print("ERROR: Dependency cycle detected in test definitions!", file=sys.stderr)
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as f:
                f.write("cycle_detected=true\n")
        sys.exit(0)  # workflow step will check flag and exit 1

    wave_0 = wave_lists[0]
    wave_1 = wave_lists[1]
    has_wave_1   = "true" if wave_1 else "false"
    has_wave_seq = "true" if overflow_entries else "false"

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"cycle_detected=false\n")
            f.write(f"wave_0_matrix={json.dumps(wave_0)}\n")
            f.write(f"wave_1_matrix={json.dumps(wave_1)}\n")
            f.write(f"has_wave_1={has_wave_1}\n")
            f.write(f"wave_seq_matrix={json.dumps(overflow_entries)}\n")
            f.write(f"has_wave_seq={has_wave_seq}\n")
            # Backward-compat alias used by local tooling
            f.write(f"matrix={json.dumps(wave_0)}\n")

    print(f"Discovered {len(wave_0)} wave-0 tests, "
          f"{len(wave_1)} wave-1 tests, "
          f"{len(overflow_entries)} sequential overflow tests")
    print(f"Cycle detected: false")


if __name__ == "__main__":
    main()
