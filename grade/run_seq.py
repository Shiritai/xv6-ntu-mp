#!/usr/bin/env python3
"""Run stage-seq tests sequentially with rolling score updates.

Reads WAVE_SEQ_MATRIX, SCORE_TOTAL, SCORE_POSSIBLE from the environment.
After each test, reads the output JSON to update running totals and
rewrites grades_history.json so the next test sees the current state.
"""

import json
import os
import subprocess
import sys

tests = json.loads(os.environ["WAVE_SEQ_MATRIX"])

running_total    = int(os.environ["SCORE_TOTAL"])
running_possible = int(os.environ["SCORE_POSSIBLE"])

history_path = "grades_history.json"
try:
    with open(history_path) as f:
        history = json.load(f)
except (IOError, json.JSONDecodeError):
    history = {}

for t in tests:
    result_path = f"results/{t['slug']}.json"
    subprocess.run([
        sys.executable, "grade/run.py",
        "--inject-total",    str(running_total),
        "--inject-possible", str(running_possible),
        "--inject-history",  history_path,
        "--json", result_path,
        t["pattern"],
    ], check=False)

    try:
        with open(result_path) as f:
            result = json.load(f)
        scores = result.get("scores", {})
        running_total    = scores.get("raw_total",   running_total)
        running_possible = scores.get("max_total",   running_possible)
        for detail in scores.get("details", []):
            tc = detail.get("test_case", "")
            if tc:
                history[tc] = detail.get("score", 0)
    except (IOError, json.JSONDecodeError, KeyError):
        pass  # carry previous totals forward on failure

    with open(history_path, "w") as f:
        json.dump(history, f)
