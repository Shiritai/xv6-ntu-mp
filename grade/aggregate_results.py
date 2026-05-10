#!/usr/bin/env python3
"""Aggregate per-test result JSONs from matrix CI jobs into a final report."""

import sys
import os
import glob
import json
import argparse

# Reuse verdict/report logic from run.py
sys.path.insert(0, os.path.dirname(__file__))
from run import (
    gather_verdict,
    generate_markdown,
    generate_json,
    parse_mp_conf,
)


def load_result_files(results_dir):
    """Load all per-test result JSON files from a directory.

    Returns a list of detail dicts, preserving test ordering by filename.
    """
    details = []
    pattern = os.path.join(results_dir, "**", "*.json")
    for path in sorted(glob.glob(pattern, recursive=True)):
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: skipping {path}: {e}", file=sys.stderr)
            continue

        # Handle full report format (from run.py --json)
        if "scores" in data and "details" in data["scores"]:
            for d in data["scores"]["details"]:
                # Skip identity/checklist meta-entries from per-test reports
                tc = d.get("test_case", "")
                if "Identity Validation" in tc or "Checklist Validation" in tc:
                    continue
                details.append(d)
        elif "test_case" in data:
            details.append(data)
        elif isinstance(data, list):
            details.extend(data)

    return details


def sort_details(details):
    """Sort details by the 'order' field emitted by run.py.

    This reproduces the exact registration order from gradelib.TESTS,
    which is the canonical order defined by test_mp2.py's module-level
    execution (Power on → public natural-sorted → private → cache check
    → bonus threshold → bonuses → spinlock).

    Entries without an 'order' field (e.g. custom or legacy) sort last.
    """
    return sorted(details, key=lambda d: d.get("order", 9999))


def main():
    parser = argparse.ArgumentParser(description="Aggregate test results")
    parser.add_argument("--results-dir", required=True,
                        help="Directory containing per-test result JSONs")
    parser.add_argument("--bonus", default=None,
                        help="Path to bonus test results JSON")
    parser.add_argument("--json", required=True,
                        help="Path to output final report.json")
    parser.add_argument("--markdown", required=True,
                        help="Path to output final grade-report.md")
    args = parser.parse_args()

    # Collect all per-test results
    details = load_result_files(args.results_dir)

    # Collect bonus results if provided
    if args.bonus and os.path.exists(args.bonus):
        try:
            with open(args.bonus, "r") as f:
                data = json.load(f)
            if "scores" in data and "details" in data["scores"]:
                for d in data["scores"]["details"]:
                    tc = d.get("test_case", "")
                    if "Identity Validation" in tc or "Checklist Validation" in tc:
                        continue
                    details.append(d)
            elif isinstance(data, list):
                details.extend(data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: could not load bonus results: {e}", file=sys.stderr)

    # Sort to maintain stable, canonical order
    details = sort_details(details)

    # Calculate totals
    total_score = sum(d.get("score", 0) for d in details)
    max_score = sum(d.get("max_score", 0) for d in details)

    # Get verdict (penalties, identity, etc.)
    verdict = gather_verdict()
    penalty_ratio = verdict["penalty_ratio"]
    final_score = total_score * (1.0 - penalty_ratio)

    print(f"Aggregated {len(details)} test results")
    print(f"Raw Score: {total_score}/{max_score}")
    print(f"Final Score: {final_score}/{max_score}")

    # Generate reports
    generate_markdown(total_score, max_score, details, args.markdown, verdict)
    generate_json(total_score, max_score, details, args.json, verdict)


if __name__ == "__main__":
    main()
