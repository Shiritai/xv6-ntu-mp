import os
import sys
import glob
import re

# Ensure tests/ directory is in path for Cython modules
if os.path.dirname(__file__):
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
else:
    sys.path.append(os.path.abspath("tests"))

import gradelib
from gradelib import *
from pseudo_fslab import interpreter
from check_cache import check_cache_public
from check_cache_bonus import check_cache_bonus
from check_list import analyze_slab_files
from check_rand import check_rand_nonlinear as check_nl, check_rand_entropy as check_et

REPEAT_TIMES = 5
try:
    with open("mp.conf", "r") as f:
        for line in f:
            if line.startswith("REPEAT_TIMES="):
                REPEAT_TIMES = int(line.strip().split("=")[1])
                break
except Exception:
    pass

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

# Global dictionary to store pass counts for bonus evaluation
GRADES_HISTORY = {}
SKIP_BONUS = False

def create_mp2_test(test_name: str, script_file: str, points: int, sub_dir = "TestMeta", timeout=120):
    @test(points, test_name)
    def test_case():
        script = []
        try:
            with open(script_file, "r") as f:
                script = [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            raise AssertionError(f"Script file {script_file} not found")

        pass_count = 0
        last_error = None
        
        # Run REPEAT_TIMES times for stability and bonus tracking
        os.makedirs(f"out/{sub_dir}", exist_ok=True)
        for i in range(1, REPEAT_TIMES + 1):
            reset_fs()
            # We want to capture output for each run
            output_file = f"out/{sub_dir}/{test_name.replace('/', '_').replace(' ', '_').replace(':', '')}.run{i}.log"
            r = Runner(save(output_file), stop_on_line(r".*panic:.*"), stop_on_line(r".*[MP2] <FAILED>.*"))
            try:
                r.run_qemu(shell_script(script), timeout=timeout)
                # Interpret the QEMU output
                interpreter(r.qemu.output.splitlines())
                pass_count += 1
            except AssertionError as e:
                last_error = e
                continue
        
        # Record history for spinlock bonus
        GRADES_HISTORY[test_name] = pass_count
        
        # Binary scoring: Pass 1 or more times -> full points
        if pass_count < 1:
            raise last_error or AssertionError(f"Failed all {REPEAT_TIMES} attempts")
            
    return test_case

def discover_tests():
    public_tests = glob.glob("tests/public/mp2-*.txt")
    private_tests = glob.glob("tests/private/mp2-*.txt")
    custom_tests = glob.glob("tests/custom/*.txt")

    for script_file in sorted(public_tests, key=natural_sort_key):
        basename = os.path.basename(script_file)
        create_mp2_test(f"public/{basename}", script_file, 3, sub_dir="public", timeout=120)

    for script_file in sorted(private_tests, key=natural_sort_key):
        basename = os.path.basename(script_file)
        create_mp2_test(f"private/{basename}", script_file, 5, sub_dir="private", timeout=4800)

    # Only load custom tests if explicitly requested via command line arguments
    if len(sys.argv) > 1:
        for script_file in sorted(custom_tests, key=natural_sort_key):
            basename = os.path.basename(script_file)
            create_mp2_test(f"custom/{basename}", script_file, 0, sub_dir="custom", timeout=1200) # Custom tests carry 0 points

@test(10, "Power on check (10% public)")
def test_power_on_check():
    r = Runner(stop_on_line(r".*panic:.*"), stop_on_line(r".*[MP2] <FAILED>.*"))
    r.run_qemu(shell_script(["echo Ok"]), timeout=60)
    return 10

discover_tests()

@test(10, "In-cache objs check (Public)")
def test_cache_check():
    r = Runner(stop_on_line(r".*panic:.*"), stop_on_line(r".*[MP2] <FAILED>.*"))
    r.run_qemu(shell_script(["mp2"]), timeout=60)
    return check_cache_public(r.qemu.output)

@test(0, "Bonus threshold check")
def test_bonus_threshold():
    if gradelib.TOTAL < 70:
        global SKIP_BONUS
        SKIP_BONUS = True
    return 0

@test(5, "Linux styled List API (Bonus)")
def test_list_check():
    if SKIP_BONUS:
        print("Skip bonus test since the public score < 70")
        return 0
    return 5 if analyze_slab_files() else 0

@test(5, "In-cache objs (Bonus)")
def test_cache_bonus_check():
    if SKIP_BONUS:
        print("Skip bonus test since the public score < 70")
        return 0
    r = Runner(stop_on_line(r".*panic:.*"), stop_on_line(r".*[MP2] <FAILED>.*"))
    r.run_qemu(shell_script(["mp2"]), timeout=60)
    return check_cache_bonus(r.qemu.output)

@test(5, "Randomized Freelist (Non-linear) (Bonus)")
def test_rand_nonlinear():
    if SKIP_BONUS:
        print("Skip bonus test since the public score < 70")
        return 0
    r = Runner(stop_on_line(r".*panic:.*"), stop_on_line(r".*[MP2] <FAILED>.*"))
    r.run_qemu(shell_script(["echo Ok | gah . 16 | oak end > ok", "mp2"]), timeout=60)
    return check_nl(r.qemu.output.splitlines())

@test(5, "Randomized Freelist (Entropy) (Bonus)")
def test_rand_entropy():
    if SKIP_BONUS:
        print("Skip bonus test since the public score < 70")
        return 0
    trials = 10
    passes = 0
    for i in range(trials):
        reset_fs()
        r = Runner(stop_on_line(r".*panic:.*"), stop_on_line(r".*[MP2] <FAILED>.*"))
        r.run_qemu(shell_script(["echo Ok | gah . 16 | oak end > ok", "mp2"]), timeout=60)
        if check_et(r.qemu.output.splitlines()) == 5:
            passes += 1
    
    # Award 5 points if passes at least 5 times
    print(f"Randomized Freelist (Entropy): {passes}/{trials} trials passed")
    return 5 if passes >= 5 else 0

@test(10, "Spinlock Correctness Bonus (Bonus)")
def test_spinlock_bonus():
    if SKIP_BONUS:
        print("Skip bonus test since the public score < 70")
        return 0
    # Only award if Public test score >= 70 (approx 24 public tests * 3 = 72)
    # AND every public test passed REPEAT_TIMES/REPEAT_TIMES
    public_tests = [n for n in GRADES_HISTORY if n.startswith("public/")]
    if not public_tests:
        return 0
    if all(GRADES_HISTORY[n] == REPEAT_TIMES for n in public_tests):
        return 10
    return 0
