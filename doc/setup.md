# 🛠️ Onboarding: Environment Setup

Follow these steps to create your private workspace and initialize the development tools.

---

## Step 1: Create Your Private Repository

The TAs provide a **Template Repository** as the starting point for every MP.

1.  **Get the Link**: Access **NTU COOL** and find the latest assignment announcement to get the official Template Repository link.
2.  **Use Template**: On the GitHub page, click the green **`Use this template`** button and select **`Create a new repository`**.
3.  **📛 Repository Name**: Name your new repository `ntuos2026-mpX` (replace `X` with the current assignment number, e.g., `ntuos2026-mp0`).
4.  **🔒 [CRITICAL] Private Visibility**: Change the visibility from Public to **`Private`**. 
    > [!CAUTION]
    > Public repositories containing homework code are strictly prohibited and will result in a **zero score**.
    > **Academic Integrity Warning**: If you set your repository containing homework solutions to `Public`, allowing anyone to copy your code, it will be considered a severe violation of academic integrity and plagiarism. You will face strict disciplinary actions. Please double-check that it is `Private`.
5.  **Create**: Click **`Create repository from template`**.

---

## Step 2: Invite TA Collaborators 👥

Since your repository is Private, our automated grading system cannot see your code without an invitation.

1.  Navigate to your repository's **Settings** tab.
2.  Select **Collaborators** from the left-hand sidebar.
3.  Click the green **Add people** button.
4.  Search for the **Official TA Account** (see the NTU COOL announcement for the exact ID) and send the invite.
5.  Once added, the system is authorized to grade your work.

---

## Step 3: Local Setup & Cloning

Now, bring the code to your local machine.

1.  **Clone**:
    ```bash
    git clone https://github.com/YourUsername/ntuos2026-mpX.git
    cd ntuos2026-mpX
    ```
2.  **Identify Yourself**: configure your local Git identity:
    ```bash
    git config user.name "Your Name"
    git config user.email "your-email@example.com"
    ```

---

## Step 4: System Initialization

We use a unified script `./mp.sh` to manage all dependencies and configurations.

Run the one-time initialization:
```bash
./mp.sh init
```
**This command installs essential Git Hooks** that help you follow the course policies and protect you from accidental file loss.

---

## Step 5: Identity Binding (`student.conf`)

Open `student.conf` in the project root and fill in your real information.

```ini
# student.conf
STUDENT_ID="b12345678"          # Use lowercase
STUDENT_NAME="Your Real Name"   # As it appears on your student ID
GITHUB_USERNAME="YourUsername"  # Your EXACT GitHub username
```

> [!IMPORTANT]
> This file is the "name tag" for your grade. Submitting with default or invalid values will block your commits or lead to a **score of 0** during final evaluation.

---

## Step 6: Verify with QEMU ✅

Check if everything is working by launching the xv6 environment:

```bash
./mp.sh qemu
```
- If you see the `$` prompt, you are ready to code!
- **To Exit**: Press `Ctrl + a`, release, then press `x`.
