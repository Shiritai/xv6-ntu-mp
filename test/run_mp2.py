#!/usr/bin/env python

from gradelib import *
from pseudo_fslab import interpreter
import os
import sys
from typing import List

from check_list import analyze_slab_files
from check_slab import check_slab
from check_cache import check_cache

def run_mp2_test(test_name: str, script_file: str, points: int, timeout = 8) -> None:
    """
    Run an MP2 test case with the given script file and evaluate the output.

    Args:
        test_name (str): Name of the test case (e.g., "mp2-1").
        script_file (str): Path to the script file (e.g., "test/mp2-1.txt").
        points (int): Points assigned to the test case.
    """
    @test(points, test_name)
    def test_case():
        # Load script lines from file
        script: List[str] = []
        try:
            with open(script_file, "r") as f:
                script = [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            raise AssertionError(f"Script file {script_file} not found")
        except IOError as e:
            raise AssertionError(f"Failed to read {script_file}: {e}")


        # Run QEMU with the script
        output_file = f"out/{test_name}.out"
        os.makedirs("/".join(output_file.split("/")[:-1]), exist_ok=True)
        r = Runner(save(output_file), stop_on_line(r".*panic:.*"),
                   stop_on_line(r".*[MP2] <FAILED>.*"))
        r.run_qemu(shell_script(script), tg_base='qemu', timeout=timeout)

        # Interpret the QEMU output
        interpreter(r.qemu.output.splitlines())

    return test_case

def run_list_check():
    @test(10, "Linux styled list API (bonus)")
    def test_case():
        # Clean previous build artifacts silently
        os.system("make clean > /dev/null 2>&1")
        if not analyze_slab_files():
            raise AssertionError("Linux-styled list bonus is not implemented")
    return test_case

def run_slab_check():
    @test(10, "Slab check (Max [3(+5): slab structure (with bonus)] + [2: max objects])")
    def test_case():
        output_file = "out/slab_check.out"
        os.makedirs("/".join(output_file.split("/")[:-1]), exist_ok=True)
        r = Runner(save(output_file), stop_on_line(r".*panic:.*"),
                   stop_on_line(r".*[MP2] <FAILED>.*"))
        r.run_qemu(shell_script([""]), tg_base='qemu', timeout=8)
        res = check_slab(r.qemu.output)
        return res
    return test_case

def run_cache_check():
    @test(10, "In-cache fragmentation (bonus)")
    def test_case():
        output_file = "out/cache_check.out"
        os.makedirs("/".join(output_file.split("/")[:-1]), exist_ok=True)
        r = Runner(save(output_file), stop_on_line(r".*panic:.*"),
                   stop_on_line(r".*[MP2] <FAILED>.*"))
        r.run_qemu(shell_script(["mp2"]), tg_base='qemu', timeout=8)
        res = check_cache(r.qemu.output)
        return res
    return test_case

def public_testcases(rng: range):
    """Define and run MP2 test cases."""
    tests = list(rng)
    tests = [run_mp2_test(f"public/mp2-{t}", f"test/public/mp2-{t}.txt", 3, 20) for t in tests]
    return tests

def private_testcases(rng: range):
    """Define and run MP2 test cases."""
    tests = list(rng)
    tests = [run_mp2_test(f"private/mp2-{t}", f"test/private/mp2-{t}.txt", 5, 30) for t in tests]
    return tests

def run_custom_test():
    return run_mp2_test(f"custom/mytest", f"test/custom/mytest.txt", 0)

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == 'custom':
        run_custom_test()
    elif len(sys.argv) == 2 and sys.argv[1] == 'slab':
        run_slab_check()
    elif len(sys.argv) == 2 and sys.argv[1] == 'list':
        run_list_check()
    elif len(sys.argv) == 2 and sys.argv[1] == 'cache':
        run_cache_check()
    elif len(sys.argv) >= 2 and sys.argv[1] == 'private':
        _from, _to = 0, 4
        if len(sys.argv) >= 3:
            _from = int(sys.argv[2])
        if len(sys.argv) >= 4:
            _to = int(sys.argv[3])
        private_testcases(range(_from, _to))
    elif len(sys.argv) == 2 and sys.argv[1] == 'all':
        run_slab_check()
        public_testcases(range(25))
        run_cache_check()
        run_list_check()
        if os.path.exists("test/private"):
            private_testcases(range(len([f for f in os.listdir('test/private') 
                                         if os.path.isfile(os.path.join('test/private', f))
                                         and f.startswith("mp2-") and f.endswith(".txt")])))
    else:
        _from, _to = 0, 25
        if len(sys.argv) >= 2:
            _from = int(sys.argv[1])
        if len(sys.argv) >= 3:
            _to = int(sys.argv[2])
        public_testcases(range(_from, _to))
    # run tests
    os.system("make clean > /dev/null 2>&1")
    run_tests()
