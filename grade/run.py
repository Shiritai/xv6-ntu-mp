#!/usr/bin/env python3

import sys
import os
import glob
import importlib.util
import json
import argparse
import datetime
import re
import gradelib
from gradelib import *
import fnmatch

# Configuration
TEST_DIR = os.environ.get("TEST_DIR", "tests")
CONF_PATH = os.path.join(os.path.dirname(__file__), "../mp.conf")
GRADING_CONF_PATH = os.path.join(os.path.dirname(__file__), "../tests/grading.conf")
TARGET_COMMIT_PATH = "target_commit.json"
STUDENT_CONF_PATH = os.path.join(os.path.dirname(__file__), "../student.conf")

def load_grading_config():
    patterns = []
    if os.path.exists(GRADING_CONF_PATH):
        with open(GRADING_CONF_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    # Default to match everything if no config found (for robustness)
    if not patterns:
        patterns = ["*.py", "*.txt"]
    return patterns

def matches_grading_conf(filename, patterns):
    basename = os.path.basename(filename)
    for p in patterns:
        if fnmatch.fnmatch(basename, p):
            return True
    return False

def run_script_test(test_name, script_path, points=10, timeout=30):
    @test(points, test_name)
    def test_case():
        with open(script_path, "r") as f:
            script = [line.strip() for line in f.readlines()]
        
        output_file = f"out/{test_name}.out"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        r = Runner(save(output_file))
        r.run_qemu(shell_script(script), timeout=timeout)
        
    return test_case

def get_test_rank(filename):
    name = os.path.basename(filename).lower()
    if 'public' in name: return 0
    if 'private' in name: return 2
    return 1

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def load_python_tests(test_dir, patterns):
    # grading.conf is the single whitelist: files not matched are not loaded
    # at all (not merely unscored). This prevents student-authored .py in
    # tests/ from executing arbitrary code at import time and tampering with
    # gradelib globals, test registrations, or scoring accumulators.
    py_files = glob.glob(os.path.join(test_dir, "*.py"))
    py_files = [f for f in py_files if matches_grading_conf(f, patterns)]
    py_files = sorted(py_files, key=lambda p: (get_test_rank(p), natural_sort_key(p)))
    for py_file in py_files:
        if os.path.basename(py_file) == "setup.py":
            continue

        # Namespaced module name to avoid sys.modules collisions with stdlib
        # or gradelib itself (e.g. a file named gradelib.py in tests/).
        module_name = "_mp_test_" + os.path.basename(py_file)[:-3]
        spec = importlib.util.spec_from_file_location(module_name, py_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

def load_script_tests(test_dir, patterns):
    txt_files = glob.glob(os.path.join(test_dir, "*.txt"))
    txt_files = [f for f in txt_files if matches_grading_conf(f, patterns)]
    txt_files = sorted(txt_files, key=lambda p: (get_test_rank(p), natural_sort_key(p)))
    for txt_file in txt_files:
        test_name = os.path.basename(txt_file)[:-4]
        run_script_test(test_name, txt_file)

def parse_mp_conf():
    config = {}
    if os.path.exists(CONF_PATH):
        with open(CONF_PATH, "r") as f:
            for line in f:
                key_match = re.search(r'^([A-Z_]+)="(.*)"', line.strip())
                if key_match:
                    config[key_match.group(1)] = key_match.group(2)
    return config

def parse_student_conf():
    config = {
        "STUDENT_ID": "unknown",
        "STUDENT_NAME": "unknown",
        "GITHUB_USERNAME": "unknown"
    }
    if os.path.exists(STUDENT_CONF_PATH):
        with open(STUDENT_CONF_PATH, "r") as f:
            for line in f:
                key_match = re.search(r'^([A-Z_]+)\s*=\s*"?([^"]*)"?', line.strip())
                if key_match:
                    config[key_match.group(1)] = key_match.group(2)
    return config

def validate_student_conf(student_conf):
    invalid_strs = ["", "b00000000", "your name", "your-github-id", "unknown"]
    id_valid = student_conf.get("STUDENT_ID", "").lower() not in invalid_strs
    name_valid = student_conf.get("STUDENT_NAME", "").lower() not in invalid_strs
    github_valid = student_conf.get("GITHUB_USERNAME", "").lower() not in invalid_strs
    return id_valid and name_valid and github_valid

def validate_checklist(path):
    if not os.path.exists(path):
        return True
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("- [ ] "):
                return False
    return True

def load_target_commit():
    if os.path.exists(TARGET_COMMIT_PATH):
        with open(TARGET_COMMIT_PATH, "r") as f:
            return json.load(f)
    return None

def calculate_lateness(deadline_iso, commit_timestamp):
    if not deadline_iso or not commit_timestamp:
        return 0
    
    # Simple ISO parse (assuming Z or simple offset)
    # Python 3.11+ `fromisoformat` handles Z, but older versions might not.
    try:
        deadline_dt = datetime.datetime.fromisoformat(deadline_iso.replace("Z", "+00:00"))
        commit_dt = datetime.datetime.fromtimestamp(int(commit_timestamp), datetime.timezone.utc)
        
        if commit_dt <= deadline_dt:
            return 0
        
        delta = commit_dt - deadline_dt
        return max(0, delta.days + (1 if delta.seconds > 0 else 0))
    except Exception as e:
        print(f"Warning: Date parsing error: {e}", file=sys.stderr)
        return 0

def gather_verdict():
    conf = parse_mp_conf()
    target_commit = load_target_commit()
    commit_ts = target_commit.get("timestamp") if target_commit else 0
    deadline = conf.get("DEADLINE", "")
    late_days = calculate_lateness(deadline, commit_ts)
    # Penalty Policy: 20% per day.
    penalty_ratio = min(1.0, late_days * 0.2)
    student_conf = parse_student_conf()
    is_identity_valid = validate_student_conf(student_conf)
    
    checklist_path = os.path.join(os.path.dirname(__file__), "../checklist.md")
    is_checklist_valid = validate_checklist(checklist_path)

    if not is_identity_valid or not is_checklist_valid:
        penalty_ratio = 1.0 # Force zero score if identity or checklist is invalid
    return {
        "conf": conf,
        "target_commit": target_commit,
        "commit_ts": commit_ts,
        "deadline": deadline,
        "late_days": late_days,
        "penalty_ratio": penalty_ratio,
        "student_conf": student_conf,
        "is_identity_valid": is_identity_valid,
        "is_checklist_valid": is_checklist_valid,
    }

def generate_markdown(total_score, max_score, details, md_path, verdict):
    penalty_ratio = verdict["penalty_ratio"]
    student_conf = verdict["student_conf"]
    is_identity_valid = verdict["is_identity_valid"]

    lines = []

    # Part 1: Information
    lines.append("## Information")
    lines.append("")
    if not verdict["is_identity_valid"]:
        lines.append("# ⚠️ Identity Configuration Missing!")
        lines.append("Your `student.conf` contains default or missing values.")
        lines.append("Please configure it before your final submission.")
    elif not verdict["is_checklist_valid"]:
        lines.append("# ⚠️ Submission Checklist Incomplete!")
        lines.append("You have unchecked items in your `checklist.md`.")
        lines.append("Please complete all required tasks before your final submission.")
    else:
        lines.append(f"- **Student ID**: {student_conf.get('STUDENT_ID')}")
        lines.append(f"- **Name**: {student_conf.get('STUDENT_NAME')}")
        lines.append(f"- **GitHub Username**: {student_conf.get('GITHUB_USERNAME')}")
    lines.append("")

    # Part 2: Grades (mermaid xychart)
    lines.append("## Grades")
    lines.append("")

    test_details = [d for d in details if d.get("max_score", 0) > 0]

    if test_details:
        test_names = [d["test_case"] for d in test_details]
        multiplier = 1.0 - penalty_ratio
        max_scores_list = [d["max_score"] * multiplier for d in test_details]
        actual_scores_list = [d["score"] * multiplier for d in test_details]
        y_max = max(max_scores_list)

        x_labels = ", ".join(f'"{name}"' for name in test_names)
        bar_max = ", ".join(str(s) for s in max_scores_list)
        bar_actual = ", ".join(str(s) for s in actual_scores_list)

        lines.append("```mermaid")
        lines.append("xychart-beta horizontal")
        lines.append(f'    x-axis [{x_labels}]')
        lines.append(f'    y-axis "Score" 0 --> {y_max}')
        lines.append(f'    bar [{bar_max}]')
        lines.append(f'    bar [{bar_actual}]')
        lines.append("```")
    lines.append("")

    with open(md_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Markdown report generated at {md_path}")

def generate_json(total_score, max_score, details, json_path, verdict):
    conf = verdict["conf"]
    target_commit = verdict["target_commit"]
    commit_ts = verdict["commit_ts"]
    deadline = verdict["deadline"]
    late_days = verdict["late_days"]
    penalty_ratio = verdict["penalty_ratio"]
    student_conf = verdict["student_conf"]
    is_identity_valid = verdict["is_identity_valid"]

    final_score = total_score * (1.0 - penalty_ratio)

    is_private_str = os.environ.get("REPO_IS_PRIVATE", "true").lower()
    is_private = is_private_str == "true"
    
    if not verdict["is_identity_valid"]:
        details.insert(0, {
            "test_case": "Identity Validation (student.conf)",
            "status": "FAIL",
            "score": 0,
            "max_score": 0,
            "output": "CRITICAL: Default identity detected in student.conf. Score forced to 0."
        })
    elif not verdict["is_checklist_valid"]:
        details.insert(0, {
            "test_case": "Checklist Validation (checklist.md)",
            "status": "FAIL",
            "score": 0,
            "max_score": 0,
            "output": "CRITICAL: Unchecked items found in checklist.md. Score forced to 0."
        })
    else:
        details.insert(0, {
            "test_case": "Identity Validation (student.conf)",
            "status": "PASS",
            "score": 0,
            "max_score": 0,
            "output": f"Validated: {student_conf.get('STUDENT_ID')} ({student_conf.get('GITHUB_USERNAME')})"
        })
    
    report = {
        "$schema": "http://ntu-os.org/schemas/v1/report",
        "meta": {
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "grader_image": conf.get("DOCKER_IMAGE", "ntuos/mp_grader"),
            "assignment": conf.get("ASSIGNMENT", "unknown")
        },
        "target_commit": {
            "sha": target_commit.get("sha", "unknown") if target_commit else "unknown",
            "author": target_commit.get("author", "unknown") if target_commit else "unknown",
            "timestamp": datetime.datetime.fromtimestamp(commit_ts).isoformat() if commit_ts else "",
            "is_late": late_days > 0
        },
        "student_info": {
            "student_id": student_conf.get("STUDENT_ID"),
            "name": student_conf.get("STUDENT_NAME"),
            "github_username": student_conf.get("GITHUB_USERNAME"),
            "is_valid": is_identity_valid
        },
        "grading": {
            "deadline": deadline,
            "is_late": late_days > 0,
            "late_days": late_days,
            "penalty_policy": "20% per day",
            "penalty_ratio": penalty_ratio,
            "identity_failed": not is_identity_valid,
            "is_private": is_private
        },
        "scores": {
            "raw_total": total_score,
            "max_total": max_score,
            "final_score": final_score,
            "details": details
        }
    }
    
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report generated at {json_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", help="Path to output report.json")
    parser.add_argument("--markdown", help="Path to output report.md")
    args, unknown = parser.parse_known_args()

    # Ensure test directory exists
    if not os.path.isdir(TEST_DIR):
        print(f"Warning: Test directory '{TEST_DIR}' not found.")
        sys.exit(0)

    # Load tests
    patterns = load_grading_config()
    load_script_tests(TEST_DIR, patterns)
    load_python_tests(TEST_DIR, patterns)

    # Initialize options for gradelib since we bypass run_tests()
    gradelib.options = argparse.Namespace(color="auto", verbose=False)

    # Run tests via gradelib
    # gradelib.run_tests() calls sys.exit? No, checks `no_error`.
    # But it calculates TOTAL/POSSIBLE global vars.
    try:
        gradelib.make() # We assume gradelib handles make
        gradelib.reset_fs()
        
        # Execute tests
        # We manually iterate because we want to capture details
        details = []
        
        # Determine which tests to run based on command line arguments
        tests_to_run = []
        if unknown:
            for test_pattern in unknown:
                for test_func in gradelib.TESTS:
                    title = getattr(test_func, "title", test_func.__name__)
                    if fnmatch.fnmatch(title, test_pattern) or test_pattern in title:
                        if test_func not in tests_to_run:
                            tests_to_run.append(test_func)
        else:
            tests_to_run = gradelib.TESTS

        no_error = True
        for test_func in tests_to_run:
            try:
                ok = test_func()
            except Exception as e:
                print(f"Test {test_func.__name__} crashed: {e}")
                ok = False
            
            no_error = ok and no_error
            
            # Capture result
            details.append({
                "test_case": getattr(test_func, "title", test_func.__name__),
                "status": "PASS" if ok else "FAIL",
                "score": getattr(test_func, "score", 0),
                "max_score": getattr(test_func, "points", 0),
            })

    except BaseException as e:
        print(f"Execution/Compilation Error: {e}")
        # If compilation failed, we still want a report
        gradelib.TOTAL = 0
        details = [{
            "test_case": "Build/Setup",
            "status": "FAIL",
            "score": 0,
            "max_score": 0,
            "output": str(e)
        }]
        no_error = False

    # Calculate Penalties & Final Score
    verdict = gather_verdict()
    penalty_ratio = verdict["penalty_ratio"]
    is_valid = verdict["is_identity_valid"]
    late_days = verdict["late_days"]
    
    total = gradelib.TOTAL
    possible = gradelib.POSSIBLE
    final_score = total * (1.0 - penalty_ratio)
    
    # 1. Identity/Checklist/Late Warnings
    if not is_valid:
        print("\n" + "="*50)
        print(f"{color('red', '[WARN] Identity Configuration Missing!')}")
        print("Your student.conf contains default or missing values.")
        print("Please configure it before your final submission.")
        print("="*50 + "\n")
    elif not verdict["is_checklist_valid"]:
        print("\n" + "="*50)
        print(f"{color('red', '[WARN] Submission Checklist Incomplete!')}")
        print("You have unchecked items in your checklist.md.")
        print("Please complete all required tasks before your final submission.")
        print("="*50 + "\n")
    elif penalty_ratio > 0:
        print("\n" + "="*50)
        print(f"{color('yellow', '[WARN] Late Submission Penalty')}: {int(penalty_ratio * 100)}%")
        print(f"Late Days: {late_days}")
        print("="*50 + "\n")
    
    # 2. Final Score Output
    print(f"Final Score: {color('green' if is_valid and penalty_ratio == 0 else 'yellow', str(final_score))}/{possible}")
    
    # 3. Report Generation
    if args.markdown:
        generate_markdown(total, possible, details, args.markdown, verdict)

    if args.json:
        generate_json(total, possible, details, args.json, verdict)

    sys.exit(0 if no_error else 1)
