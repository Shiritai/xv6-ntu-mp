# MP2 Testing Commands Guide (`./mp.sh test`)

This project uses a highly encapsulated `./mp.sh test` command for xv6 assignment testing. In addition to running all tests by default, the script supports "substring matching", allowing you to precisely execute desired combinations.

## Basic Usage

| Command | Description |
| --- | --- |
| `./mp.sh test` | Run all test cases, including Public and Bonus challenges. |
| `./mp.sh test custom` | Run all custom test scripts under `tests/custom/`. |

## Advanced Path Targeting (Precise Testing)

Thanks to internal namespace expansion, you can now directly provide the **relative path** of a test script to execute it individually.

### 1. Run a Single Public Test

```bash
./mp.sh test public/mp2-0.txt
```

> **Effect**: Only executes the `tests/public/mp2-0.txt` test.
> **Best Practice**: Use this to save time when debugging a specific test case instead of waiting for all tests to finish.

### 2. Run a Single Custom Test

```bash
./mp.sh test custom/my-test.txt
```

- **Effect**: Executes your custom script located at [`tests/custom/my-test.txt`](../tests/custom/my-test.txt).
- **Best Practice**: You can create multiple custom test scenarios without modifying the same file repeatedly for debugging.

## Creating Custom Tests (`tests/custom/`)

Creating your own test scenarios is highly recommended for identifying specific bugs and verifying edge cases.

### 1. Create the Test Script

Create a new `.txt` file in the `tests/custom/` directory (e.g., `tests/custom/my-stress.txt`).

### 2. Add Commands

The file should contain a sequence of commands that you want to execute sequentially in the xv6 shell.

**Example `tests/custom/my-stress.txt`:**

```text
echo custom_stress_test
mp2
echo Ok
```

### 3. Execution Mechanism

When you run `./mp.sh test custom/my-stress.txt`, the following happens:

1. **Compilation**: The system checks if the kernel and user programs are up to date.
2. **Boot**: A new instance of QEMU is launched.
3. **Execution**: The content of your `.txt` file is sent to the xv6 serial console as if you typed it.
4. **Capture**: The entire console output is captured and saved to a log file. Also, the test system will report whether the test passed or failed.

### 4. Analyzing Results

Since custom tests don't have a pre-defined "expected output" (`.out` file), the test system will generally report them as "passed" if the commands finish. You should **visually inspect the logs** to verify correctness:

- Path: `out/custom/custom_my-stress.txt.run1.log`

Check these logs for `[SLAB]` outputs, kernel panics, or any unexpected behavior.

## Substring Matching Features

The arguments for the test system utilize "**substring matching**" internally. You can take advantage of this to achieve various testing scenarios:

- `./mp.sh test 0`
  Runs all tests containing `0` in their name (e.g., `public/mp2-0.txt` and potentially `private/mp2-0.txt`).
- `./mp.sh test mp2-`
  Runs all tests with "mp2-" in their name.
- `./mp.sh test public`
  Runs all tests in the `public` directory, skipping `custom` and the other tests such as the power on check and bonus tests.

## Viewing Test Outputs (Logs)

Every time you run a test, the detailed execution log is saved in the `out/` directory. This is extremely useful for debugging specific failures without re-running the entire suite.

### Directory Structure

| Path | Description |
| --- | --- |
| `out/public/` | Contains logs for all public integrated tests. |
| `out/custom/` | Contains logs for your own custom test scripts. |

### Log File Naming Convention

The logs are named based on the test type, script filename, and run attempt (since each test is repeated 5 times for stability):

Format: `<test_type>_<script_name>.run<N>.log`

- **Example**: `out/public/public_mp2-3.txt.run1.log`
- **Failures**: If a test run fails, a `.failed` suffix might be appended or the log will contain the error details.

### How to Debug

1. **Locate the failed test**: Check the output of `./mp.sh test` to see which test and which run (e.g., `run3`) failed.
2. **Open the log**: Open the corresponding `.log` file in VS Code or use `cat`/`less` in the terminal.
3. **Analyze the output**: Look for `[SLAB]` prefixes or kernel panics to understand where your implementation diverged from the expectations.

## Targeting Specific Challenges

Want to focus on power-on check, in-cache fragmentation, or List API bonus validation? You can pass a substring of the test's long name:

- `./mp.sh test "Power on check"` (Only runs the power-on check)
- `./mp.sh test "Linux"` (Only runs the Linux list API bonus items)
- `./mp.sh test "In-cache"` (Only runs In-cache bonus items)
- `./mp.sh test "Randomized Freelist"` (Runs all freelist randomization bonus items)
