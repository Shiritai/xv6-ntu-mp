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

def create_mp2_test(test_name: str, script_file: str, points: int, sub_dir = "TestMeta", timeout=60):
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
        create_mp2_test(f"public/{basename}", script_file, 3, sub_dir="public")

    for script_file in sorted(private_tests, key=natural_sort_key):
        basename = os.path.basename(script_file)
        create_mp2_test(f"private/{basename}", script_file, 3, sub_dir="private")

    # Only load custom tests if explicitly requested via command line arguments
    if len(sys.argv) > 1:
        for script_file in sorted(custom_tests, key=natural_sort_key):
            basename = os.path.basename(script_file)
            create_mp2_test(f"custom/{basename}", script_file, 0, sub_dir="custom") # Custom tests carry 0 points

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

@test(5, "Linux styled List API (Bonus)")
def test_list_check():
    if gradelib.TOTAL < 70:
        print("Skip bonus test since the public score < 70")
        return 0
    return 5 if analyze_slab_files() else 0

@test(5, "In-cache objs (Bonus)")
def test_cache_bonus_check():
    if gradelib.TOTAL < 70:
        print("Skip bonus test since the public score < 70")
        return 0
    r = Runner(stop_on_line(r".*panic:.*"), stop_on_line(r".*[MP2] <FAILED>.*"))
    r.run_qemu(shell_script(["mp2"]), timeout=60)
    return check_cache_bonus(r.qemu.output)

def extract_addrs(output_lines):
    """Extract object address sequence from [SLAB] print_kmem_cache output."""
    addrs = []
    for line in output_lines:
        if "[idx" in line and "addr:" in line:
            # Match addr: 0x...
            match = re.search(r"addr:\s+(0x[0-9a-fA-F]+)", line)
            if match:
                addrs.append(int(match.group(1), 16))
    return addrs

def calculate_inversions(indices):
    """Calculate the number of inversions in a sequence."""
    inversions = 0
    n = len(indices)
    for i in range(n):
        for j in range(i + 1, n):
            if indices[i] > indices[j]:
                inversions += 1
    return inversions

@test(5, "Randomized Freelist (Non-linear) (Bonus)")
def test_rand_nonlinear():
    if gradelib.TOTAL < 70:
        print("Skip bonus test since the public score < 70")
        return 0
    # Trigger a run that prints the cache status
    r = Runner(stop_on_line(r".*panic:.*"), stop_on_line(r".*[MP2] <FAILED>.*"))
    # We use a simple script that creates a cache and then prints it
    # This assumes the kernel test code 'mp2' or similar does this.
    r.run_qemu(shell_script(["mp2"]), timeout=60)
    
    addrs = extract_addrs(r.qemu.output.splitlines())
    if len(addrs) < 2:
        return 0
    
    # Check if ascending or descending
    is_ascending = all(addrs[i] < addrs[i+1] for i in range(len(addrs)-1))
    is_descending = all(addrs[i] > addrs[i+1] for i in range(len(addrs)-1))
    
    if not (is_ascending or is_descending):
        return 5
    return 0

@test(5, "Randomized Freelist (Entropy) (Bonus)")
def test_rand_entropy():
    if gradelib.TOTAL < 70:
        print("Skip bonus test since the public score < 70")
        return 0
    r = Runner(stop_on_line(r".*panic:.*"), stop_on_line(r".*[MP2] <FAILED>.*"))
    r.run_qemu(shell_script(["mp2"]), timeout=60)
    
    addrs = extract_addrs(r.qemu.output.splitlines())
    if len(addrs) < 4: # Too few samples to judge entropy
        return 0
    
    # Map addresses to sorted ranks (0, 1, 2, ...) to get relative order
    sorted_addrs = sorted(addrs)
    indices = [sorted_addrs.index(a) for a in addrs]
    
    inv_count = calculate_inversions(indices)
    
    # Threshold for N=8: Inversions >= 8
    # For different N, we could scale, but struct file is typically around 8
    if inv_count >= 8:
        return 5
    return 0

@test(10, "Spinlock Correctness Bonus (Bonus)")
def test_spinlock_bonus():
    if gradelib.TOTAL < 70:
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
