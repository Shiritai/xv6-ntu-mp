# 🔄 Submission & Grading Workflow Guide

Understand the cycle of development, testing, and official evaluation.

## 1. Local Testing: The Grader Logic

The `./mp.sh grade` command is your primary tool for verification. Here is how it works under the hood:

- **Automatic Scanning**: The grader scans the `tests/` directory for any `.py` (Python) or `.txt` (Shell script) files.
- **Unified Execution**: It identifies tests using decorators (like `@test`) or filename patterns.
- **Isolated Environment**: All tests are executed inside a Docker container, mounting your `xv6/` source code to ensure a clean build every time.

## 2. Creating Your Own Tests (The Sandbox)

We encourage you to create custom tests to catch edge cases. The `tests/` directory is your personal playground.

### How to Add a Test

You can create a simple shell-based test by adding a `.txt` file to `tests/`:

```bash
# tests/my_test.txt
# This script runs inside the xv6 shell
ls
echo "Testing my program..."
mp0 /
```

Or a Python-based test for complex logic:

```python
# tests/my_custom_test.py
from gradelib import *

@test(0, "my custom test description")
def test_my_logic():
    r.run_command("mp0 /")
    r.match("expected output")
```

### 🛠️ Troubleshooting Custom Tests

- **Hanging (Infinite Loops)**: If your test never finishes, check if your xv6 program is stuck in a loop. You can terminate the grader with `Ctrl+C`.
- **Garbage Output**: If your test produces massive amounts of text, it might slow down the grader. Try to keep outputs concise.
- **Binary Files**: Never put compiled binaries in the `tests/` folder; only source scripts.

## 3. Save and Upload (Git Commit & Push)

Git requires a 3-step process to save and upload your code. Before you start, you should always check your current state.

1. **Check your progress (`git status`)**

   Use this command to see which files you have modified and which are ready to be staged.

   ```bash
   git status
   ```

2. **Stage modified files (`git add`)**

   ```bash
   git add xv6/user/mp0.c xv6/Makefile student.conf
   ```

   > *Tip: Use `git add .` to stage all modifications, but ensure no temporary or compiled files (like `fs.img`) are included.*

3. **Save with a descriptive message (`git commit`)**

   ```bash
   git commit -m "feat: complete basic requirements and configure student.conf"
   ```

4. **Upload to the cloud (`git push`)**

   ```bash
   git push origin <branch_name>
   ```

   *(e.g., `git push origin mp0`. Ensure you are pushing to the correct MP branch).*

## 4. GitHub Actions: Cloud Verification

Every time you `git push`, a cloud grading run is triggered automatically.

1. **Navigate** to the **Actions** tab on your GitHub repo.
2. **Click** on the most recent workflow (likely named **Grading System**).
3. Under **Jobs** on the left, **click ✅ grade**.
4. **Expand Execute Tests (Grading)** to see the live console and detailed test results.
5. **Projected Score** 📈: The result shown in Actions mirrors your current progress on the **Public Tests**.
6. **Grade Summary** 📋: A formal report is also available in the workflow's **Summary** tab.

## 5. Official Grading & Academic Integrity

The most important thing to remember: **You cannot "break" the official grading by experimenting**.

- **The TA Sandbox**: TAs run final evaluations in a **pristine** environment, completely ignoring your custom tests or local configuration changes.
- **Safe to Mess Up**: Feel free to use the `tests/` directory for any debugging. It belongs to you, and it will not affect your grade.
- **Mandatory Privacy**: Your repository must remain **Private**. Public solution code is a severe violation of academic integrity and will result in a zero score.

### 📊 Grading Rubric

| Category               | Points       | Description                                                 |
| :--------------------- | :----------- | :---------------------------------------------------------- |
| **Public Testcases**   | *Varies*     | Visible in `tests/`, runnable via `./mp.sh grade`.          |
| **Private Testcases**  | *Varies*     | Hidden tests injected by TAs after the deadline.            |
| **Late Penalty**       | -20% / day   | Calculated from the TA's evaluation timestamp.              |
| **Identity Violation** | **0 Points** | Missing or default `student.conf` values.                   |
| **Security/Publicity** | **0 Points** | Repository set to public or tampering with grade isolation. |

### 🆔 Identity & Lateness

- **Lateness**: This is calculated automatically based on your **last commit timestamp** on GitHub.
- **Identity**: If `student.conf` is invalid, your grade will be forced to **0** even if tests pass.
