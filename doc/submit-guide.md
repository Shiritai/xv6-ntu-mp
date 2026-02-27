# 📖 Homework Submission Guide

Welcome to the homework submission guide! This course uses a **GitHub Template** and **GitHub Actions (CI/CD)** for homework grading. This workflow allows you to track your code progress in your own private cloud repository and continuously verify your implementation against public testcases before the deadline.

⚠️ **Please Note:** We do not use NTU COOL for code submission. All code submissions and grading will be based **strictly** on the version history in your GitHub Repository. Do not upload `.zip` archives of your code to NTU COOL.

If you are new to Git and GitHub, don't worry! Please read and follow the steps below carefully to set up your personal submission environment.

---

## Step 1: Create Your Private Repository from the Template

To ensure everyone starts with the exact same foundation, the TAs provide an official **Template repository**. You must duplicate this template to begin your assignment.

1. Click the **Official MP Template Link** provided on NTU COOL to navigate to GitHub.
2. Click the green **`Use this template`** button in the top right corner, then select **`Create a new repository`**.
3. **Set Repository Name**: Name your repository `ntuos-2026-mpX` (replace `X` with the assignment number, e.g., `ntuos-2026-mp0`).
4. 🛑 **[CRITICALLY IMPORTANT] Set Visibility to Private**: You MUST set the repository visibility to **`Private`**!
   > **Academic Integrity Warning**: If you set your repository containing homework solutions to `Public`, allowing anyone to copy your code, it will be considered a severe violation of academic integrity and plagiarism. You will face strict disciplinary actions. Please double-check that it is `Private`.
5. Click **`Create repository from template`**. Congratulations! You now have your own private workspace for the assignment.

---

## Step 2: Add TAs as Collaborators

Because your repository is Private, the TA grading system cannot see your code by default, which means we cannot grade it. You must explicitly invite the official TA account.

1. Go to your newly created repository page on GitHub and click the **`Settings`** gear icon at the top.
2. In the left sidebar, select **`Collaborators`**.
3. Click the green **`Add people`** button.
4. Enter the **Official TA GitHub Account** (Please refer to the latest announcement on NTU COOL) and add them to the repository.
5. Once added, our system will be authorized to access your private repository for grading.

---

## Step 3: Clone Your Code to Your Local Machine

Now that your cloud repository is ready, you need to download it to your local computer to start coding.

1. Open your Terminal (or Command Prompt / PowerShell / WSL).
2. First, configure your Git identity (this attaches your "name tag" to every save you make):
   ```bash
   git config --global user.name "Your GitHub Username"
   git config --global user.email "Any Email You Prefer"
   ```
   *Note: Your `user.name` should match your GitHub username for clarity. You can use any email for `user.email`; it does not affect grading.*
3. On your GitHub repository homepage, click the bright green **`<> Code`** button and copy the HTTPS URL (e.g., `https://github.com/YourUsername/ntuos-2026-mpX.git`).
4. In your terminal, enter the clone command:
   ```bash
   git clone <the URL you just copied>
   cd ntuos-2026-mpX
   ```

---

## Step 4: Identity Binding (CRITICAL!) ⛔ Missing this results in 0 points

Since GitHub usernames can be anything (like `SuperHacker2000`), the TAs cannot magically know which student owns which repository. To ensure your score is correctly recorded, you **MUST** configure your identity file!

1. Open `student.conf` at the root of the repository using your code editor.
2. Replace the placeholder data with your actual Student ID, your real Name, and the exact GitHub Username you just used to create the repository.
   ```ini
   # student.conf
   STUDENT_ID="b00000000"                <-- Replace with your Student ID (lowercase)
   STUDENT_NAME="Your Real Name"         <-- Replace with your real name
   GITHUB_USERNAME="SuperHacker2000"     <-- Replace with the EXACT GitHub account you are using
   ```
3. ⚠️ **[Identity Verification Penalty]**: If you submit your homework with default values in `student.conf`, your local **commit and push will be blocked**. Even if you bypass these checks, the grading system will detect the invalid identity and **force your score to 0 points**. Please configure this file correctly on day one.

---

## Step 5: Start Coding and Local Testing

You are now ready to modify `mpX.c` or any other specified files to solve the machine problem! When you want to verify if your code is working correctly, you can run:

```bash
./mp.sh grade
```

This command uses an isolated Docker environment on your local machine to simulate the grading process and prints your score for the Public Testcases.

### Adding Your Own Tests
You are encouraged to create your own test cases in the `tests/` directory:
- **How to add**: Create a `.py` file (using the `@test` decorator) or a `.txt` file (shell commands) in the `tests/` folder.
- **Scoring Isolation**: To ensure your official score correctly reflects only TA-provided tests, we use `tests/grading.conf`.
- **How it works**: 
  - This file defines which tests are "Official". While you can modify it locally, the **TA will overwrite it during official grading**.
  - Any test file NOT in the official list will still run, but its result will not affect the final official total score.

---

## Step 6: Save and Upload (Git Commit & Push)

Unlike pressing `Ctrl+S` in a text editor, Git requires a strict 3-step process to save and upload your code: "Stage (add)", "Save (commit)", and "Upload (push)".

1. **Stage modified files (`git add`)**
   This tells Git which modified files you want to include in this submission.
   ```bash
   git add xv6/user/mp0.c xv6/Makefile student.conf
   ```
   > *Tip: You can use `git add .` to stage all modifications, but please be careful not to accidentally include garbage files (like compiled binaries e.g., `a.out`).*

2. **Save with a descriptive message (`git commit`)**
   Attach a brief explanation to this version, like "finished core requirements" or "fixed a recursive bug".
   ```bash
   git commit -m "feat: complete basic requirements and configure student.conf"
   ```

3. **Upload to the cloud (`git push`)**
   Now, push this saved version to your Private repository on GitHub! This step is equivalent to "handing in your homework".
   ```bash
   git push origin main
   ```
   *(Note: `origin` represents the remote server, and `main` or `mp0` is your branch name. Please ensure you are pushing to the correct branch specified by the MP).*

---

## Step 7: Verify Cloud Grading and Final Score

We have designed a **Dual-Layer CI/CD Grading Architecture** to let you track your progress while ensuring grading fairness. 
*(Note: You do NOT need to manually click or enable anything in the Actions tab. The workflow runs automatically upon push.)*

### 1. Before Deadline: Public Test Pre-check (CI)
Immediately after you type `git push` on your terminal, go to your GitHub repository webpage and click the **`Actions`** tab at the top.
You will see our cloud system automatically grading the code you just submitted! If it passes, you will see a green checkmark ✅. Click on the workflow run to see exactly how many points you earned on the Public Testcases.
> 💡 You can push as many times as you want to verify your code against public tests. Remember, however, that your actual final grade will be determined by the TA's automated system after the deadline.

### 2. After Deadline: TA Final Evaluation (Private Test & Report Artifact)
Once the deadline passes, you must not push any more changes.
At this time, the TA automated system will inject hidden Private Testcases and final strict scoring scripts into your Private Repo by triggering a specific CI run.

This automated TA push will trigger one final, unforgiving `Actions` run. This run evaluates both public and previously hidden conditions. Most importantly, it generates the ultimate grade report artifact: `report.json`.

The TAs will extract this artifact directly from your GitHub Actions to record your true final score. Therefore, ensuring your code compiles flawlessly in a headless Linux environment and that your `student.conf` is perfectly correct and your repository is kept private is the key to earning your grade!

Good luck and happy coding! 🚀
