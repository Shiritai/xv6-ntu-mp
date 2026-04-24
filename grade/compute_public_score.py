#!/usr/bin/env python3
"""Compute public score and build grades history from test result JSONs.

Replaces the inline `python3 -c` snippet in the bonus-test CI step.
Usage:
    python3 grade/compute_public_score.py --results-dir results/ --history grades_history.json
"""

import glob
import json
import os
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description="Aggregate public test scores for bonus evaluation")
    parser.add_argument("--results-dir", required=True,
                        help="Directory containing per-test JSON result files")
    parser.add_argument("--history", default="grades_history.json",
                        help="Path to write the grades history JSON (default: grades_history.json)")
    args = parser.parse_args()

    details = []
    for path in sorted(glob.glob(os.path.join(args.results_dir, "**/*.json"), recursive=True)):
        with open(path) as f:
            data = json.load(f)
        if "scores" in data and "details" in data["scores"]:
            details.extend(data["scores"]["details"])
        elif "test_case" in data:
            details.append(data)

    total = sum(d.get("score", 0) for d in details)
    possible = sum(d.get("max_score", 0) for d in details)
    print(f"Public total: {total}/{possible}")

    # Build GRADES_HISTORY from pass_count data
    history = {}
    for d in details:
        if "pass_count" in d:
            history[d["test_case"]] = d["pass_count"]

    with open(args.history, "w") as f:
        json.dump(history, f)

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"total={total}\n")
            f.write(f"possible={possible}\n")


if __name__ == "__main__":
    main()
