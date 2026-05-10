# 🛠️ Onboarding: Environment Initialization

Follow these steps to create your private workspace and initialize the development tools.

## Prerequisites: Install Docker

We use Docker to provide a standardized environment. Please follow the official instructions to install Docker on your operating system:

- **Windows**: Install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/).
  > **Important**: You must use **WSL 2** (Windows Subsystem for Linux) as the backend (a.k.a. run git/mp.sh inside WSL). For detailed setup tips, see [**Tips for Windows Users**](./tips-windows.md).
- **macOS**: Install [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/). Choose the correct version for your chip (Intel or Apple Silicon).
- **Linux**: Install Docker Engine using the official instructions for your distribution (e.g., [Ubuntu](https://docs.docker.com/engine/install/ubuntu/)). Follow the [Linux post-installation steps](https://docs.docker.com/engine/install/linux-postinstall/) to configure Docker to run without `sudo`.

---

## Step 1: Create Your Private Repository

The TAs provide a **Template Repository** as the starting point for every MP.

1. **Get the Link**: Access **NTU COOL** and find the latest assignment announcement to get the official Template Repository link.
2. **Use Template**: On the GitHub page, click the green **`Use this template`** button and select **`Create a new repository`**.
3. **📛 Repository Name**: Name your new repository `ntuos2026-mpX` (replace `X` with the current assignment number, e.g., `ntuos2026-mp0`).
4. **🔒 [CRITICAL] Private Visibility**: Change the visibility from Public to **`Private`**.
    > [!CAUTION]
    > Public repositories containing homework code are strictly prohibited and will result in a **zero score**.
    > **Academic Integrity Warning**: If you set your repository containing homework solutions to `Public`, allowing anyone to copy your code, it will be considered a severe violation of academic integrity and plagiarism. You will face strict disciplinary actions. Please double-check that it is `Private`.
5. **Create**: Click **`Create repository from template`**.

## Step 2: Invite TA Collaborators

Since the new repository is `Private`, TAs cannot see your code without an invitation. Therefore, you need to invite TAs to get the grade:

1. Navigate to your repository's **Settings** tab.
2. Select **Collaborators** from the left-hand sidebar.
3. Click the green **Add people** button.
4. Search for the **Official TA Account** (see the NTU COOL announcement for the exact ID) and send the invite.
5. Once added, the system is authorized to grade your work.

## Step 3: Local Setup & Cloning

Now, bring the code to your local machine.

> [!NOTE]
> **Windows Users**: Please clone the repository and run all commands **inside your WSL environment** (e.g., Ubuntu terminal), NOT in Windows PowerShell or Command Prompt. Using Windows tools to clone might corrupt the script format (CRLF vs LF). See [Detailed Windows Setup](./tips-windows.md) for a safe workflow.

1. **Clone**:

   ```bash
   git clone https://github.com/YourUsername/ntuos2026-mpX.git
   cd ntuos2026-mpX
   ```

2. **Identify Yourself**: configure your local Git identity:

   ```bash
   git config user.name "Your Name"
   git config user.email "your-email@example.com"
   ```

## Step 4: System Initialization

We use a unified script `./mp.sh` to manage all dependencies and configurations.

> [!IMPORTANT]
> **macOS & Windows Users**: Before running any `./mp.sh` commands, make sure the **Docker Desktop application is open and running** in the background.

Run the one-time initialization:

```bash
./mp.sh init
```

**This command installs essential Git Hooks** that help you follow the course policies and protect you from accidental file loss.

## Step 5: Identity Binding (`student.conf`)

Open `student.conf` in the project root and fill in your real information.

```ini
# student.conf
STUDENT_ID="b12345678"          # Use lowercase
STUDENT_NAME="Your Real Name"   # As it appears on your student ID
GITHUB_USERNAME="YourUsername"  # Your EXACT GitHub username
```

> [!IMPORTANT]
> Submitting with default or invalid values will block your commits while developing, and also lead to a **score of 0** during local/Github CI grading.

## Step 6: Verify with QEMU ✅

Check if everything is working by launching the xv6 environment:

```bash
./mp.sh qemu
```

- If you see the `$` prompt, you are ready to code!
- **To Exit**: Press `Ctrl + a`, release, then press `x`.
