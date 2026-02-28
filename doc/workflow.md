# 🔄 Submission & Grading Workflow Guide

Understand the cycle of development, testing, and official evaluation.

---

## 1. Local Testing & Customization

### The Grader Logic
When you run `./mp.sh grade`, the system scans the `tests/` directory for any `.py` (Python) or `.txt` (Shell Script) test cases.
- **Execution**: The grader **executes ALL tests** found in the directory.
- **Official Status**: Only tests that match the patterns in `tests/grading.conf` are considered "Official".
- **The Score**: Only "Official" tests contribute to the `TOTAL/POSSIBLE` score displayed at the end of the run.

### Creating Your Own Tests
We highly recommend creating your own test cases for edge cases:
- **How to add**: Simply place a new file in the `tests/` folder (e.g., `.py` using the `@test` decorator or `.txt` shell commands).
- **Isolation**: Your custom tests will show up in the output as `FAIL` or `OK`, allowing you to debug, but they will not affect the official percentage score unless you add them to `grading.conf`.
- **Note**: During official grading, the TAs will use a verified version of `grading.conf`, so your local changes to that specific file will be ignored.

---

## 2. Save and Upload (Git Commit & Push)

Unlike pressing `Ctrl+S` in a text editor, Git requires a strict 3-step process to save and upload your code: "Stage (add)", "Save (commit)", and "Upload (push)".

1.  **Stage modified files (`git add`)**
    This tells Git which modified files you want to include in this submission.
    ```bash
    git add xv6/user/mp0.c xv6/Makefile student.conf
    ```
    > *Tip: You can use `git add .` to stage all modifications, but please be careful not to accidentally include garbage files (like compiled binaries e.g., `a.out`).*

2.  **Save with a descriptive message (`git commit`)**
    Attach a brief explanation to this version, like "finished core requirements" or "fixed a recursive bug".
    ```bash
    git commit -m "feat: complete basic requirements and configure student.conf"
    ```

3.  **Upload to the cloud (`git push`)**
    Now, push this saved version to your Private repository on GitHub! This step is equivalent to "handing in your homework".
    ```bash
    git push origin <branch_name>
    ```
    *(Note: `origin` represents the remote server, and `<branch_name>` is your current branch, e.g., `mp0`. Please ensure you are pushing to the correct branch specified by the MP).*

---

## 3. GitHub Actions: Cloud Verification

We have designed a **Dual-Layer CI/CD Grading Architecture** to let you track your progress while ensuring grading fairness. 
*(Note: You do NOT need to manually click or enable anything in the Actions tab. The workflow runs automatically upon push.)*

### Tracking Progress (Public Test Pre-check) 🔍
Every time you `git push` to your repository, a cloud grading run is triggered.
Immediately after pushing:
1.  Navigate to the **Actions** tab on your GitHub repo.
2.  Click on the most recent workflow (likely named **Grading System**).
3.  Under the **Jobs** section on the left, click **✅ grade**.
4.  Expand the **Execute Tests (Grading)** step to see a live console output of your code being built and tested in the cloud.
5.  **Projected Score** 📈: The result shown in Actions mirrors your current progress on the **Public Tests**.
6.  **Grade Summary** 📋: You can also find a formal grading report in the **Summary** tab of the Action run (look for "grade summary").
> 💡 You can push as many times as you want to verify your code against public tests. Remember, however, that your actual final grade will be determined by the TA's automated system after the deadline.

---

## 4. Official Grading Policy

### 🔒 Privacy is Mandatory
Your repository must remain **Private** throughout the semester. If a repository containing solution code is found in the public domain, it is considered a severe violation of academic integrity.

### 📅 The Deadline and Final Run (TA Final Evaluation)
Once the deadline passes, you must not push any more changes.
At this time, the TA automated system will inject hidden Private Testcases and final strict scoring scripts into your Private Repo by triggering a specific CI run.

1.  TAs will initiate the final grading CI.
2.  **Private Tests** will be injected into your repo and executed. This run evaluates both public and previously hidden conditions.
3.  These tests will become part of your Git history, allowing you to see exactly where your logic succeeded or failed.
4.  **Value**: Use these post-deadline tests to identify subtle race conditions or memory leaks and perfect your understanding of xv6.
5.  The system generates the ultimate grade report artifact: `report.json`. The TAs will extract this artifact directly from your GitHub Actions to record your true final score. Ensuring your code compiles flawlessly in a headless container environment is key!

### 📊 Grading Procedure

All submissions are evaluated in an isolated grading environment according to this rubric:

| Category               | Points / Penalty | Description                                                   |
| :--------------------- | :--------------- | :------------------------------------------------------------ |
| **Public Testcases**   | *Varies by MP*   | Tests visible in `tests/` and runnable via `./mp.sh grade`.   |
| **Private Testcases**  | *Varies by MP*   | Hidden testcases evaluated after the deadline.                |
| **Late Penalty**       | -20% per day     | Lateness is calculated from the TA's evaluation timestamp.    |
| **Identity Violation** | **0 Points**     | Missing or default `student.conf` values.                     |
| **Security/Publicity** | **0 Points**     | Repository set to public or tampering with grading isolation. |

### 🆔 Identity and Lateness
- **Late Penalty**: **-20% per day**. This is calculated automatically based on your last commit timestamp.
- **Identity Failure**: If `student.conf` is invalid, your local commit and push will be blocked. Even if you bypass these checks, the final scoring logic will force your grade to **0**.
