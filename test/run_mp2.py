#!/usr/bin/env python

from gradelib import *
from pseudo_fslab import interpreter
import os
import sys
from typing import List

def run_mp2_test(test_name: str, script_file: str, points: int) -> None:
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

        # Clean previous build artifacts silently
        os.system("make clean > /dev/null 2>&1")

        # Run QEMU with the script
        output_file = f"out/{test_name}.out"
        r = Runner(save(output_file))
        r.run_qemu(shell_script(script), tg_base='qemu', timeout=150)

        # Interpret the QEMU output
        # interpreter(r.qemu.output.splitlines(), True)
        interpreter(r.qemu.output.splitlines())

    return test_case

def main(rng):
    """Define and run MP2 test cases."""
    os.makedirs(f"out/public", exist_ok=True)
    os.makedirs(f"out/private", exist_ok=True)
    tests = list(rng)
    tests = [run_mp2_test(f"public/mp2-{t}", f"test/public/mp2-{t}.txt", 3) for t in tests]
    run_tests()

if __name__ == "__main__":
    _from, _to = 0, 25
    if len(sys.argv) >= 2:
        _from = int(sys.argv[1])
    if len(sys.argv) >= 3:
        _to = int(sys.argv[2])
    main(range(_from, _to))
