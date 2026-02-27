<div align="center">
  <h1>💻 Machine Problem 0 - xv6 Setup</h1>
  <h3>CSIE3310 - Operating Systems</h3>
  <h4>National Taiwan University</h4>
</div>

<hr />

<div align="center">
  <table>
    <tr>
      <td><strong>Total Points:</strong></td>
      <td>100</td>
      <td><strong>Release Date:</strong></td>
      <td>March 3</td>
    </tr>
    <tr>
      <td><strong>Due Date:</strong></td>
      <td>March 9, 23:59:59 (UTC+8)</td>
      <td><strong>TA Hours:</strong></td>
      <td>Wed. 13:00-14:00, Thr. 12:30-1:30</td>
    </tr>
  </table>
</div>

<hr />

## 📋 Table of Contents

- [Discussion Policy](#-discussion-policy)
- [Summary](#-summary)
- [Docker Installation](#-docker-installation)
- [Launching xv6](#-launching-xv6)
- [Example MP: `mp0` Command](#-example-mp-mp0-command)
- [Submission](#-submission)
- [References](#-references)

---

## 💬 Discussion Policy

If you have any questions about this machine problem, please post them on the corresponding NTU COOL discussion board. We have opened a discussion dedicated to MP0. For special requests, you can email [ntuos@googlegroups.com](mailto:ntuos@googlegroups.com). _Note that we might not reply if you ask a general problem via email._

## 📝 Summary

**xv6** is an example kernel created by MIT for pedagogical purposes. We will study xv6 to get familiar with the main concepts of operating systems. The reference book for xv6 is [xv6: a simple, Unix-like teaching operating system](https://pdos.csail.mit.edu/6.828/2020/xv6/book-riscv-rev1.pdf). You will learn to set up the environment for xv6 and develop a custom `mp0` command in this MP.

---

## 🐳 Docker Installation

If you have installed Docker in a Unix environment, you can skip to the next step. If your operating system is Windows, we strongly suggest you [install WSL2](https://docs.microsoft.com/zh-tw/windows/wsl/install) and [run Docker in WSL2](https://docs.docker.com/desktop/windows/wsl/).

### Why Docker?

To run an arbitrary OS on your machine, you need virtualization. Virtualization is the process of running a virtual instance of a computer system in a layer abstracted from the actual hardware.

- **Virtual Machine (VM)**: Emulates a computer system that runs on top of another system. It requires a guest OS with virtual access to host resources through a hypervisor, which generally incurs significant overhead.
- **Container**: Runs a discrete process, taking no more memory than any other executable, making it extremely lightweight.

Docker is a platform for you to build and run containers. We leverage this container virtualization to standardize your homework environment, making the problems independent of both your machine's architecture and operating system.

### Supported Platforms

Docker is available on Windows, Mac, and various Linux platforms. Find your preferred OS and follow the installation guide:

- [Docker Desktop for Windows](https://docs.docker.com/docker-for-windows/install/)
- [Docker Desktop for Mac](https://docs.docker.com/docker-for-mac/install/)
- [Docker Engine for Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
- [Docker Engine for Debian](https://docs.docker.com/engine/install/debian/)
- [Docker Engine for CentOS](https://docs.docker.com/engine/install/centos/)
- [Docker Engine for Fedora](https://docs.docker.com/engine/install/fedora/)

> **💡 Suggestion:** We suggest installing Docker on Linux platforms because the Docker scripts we provide are based on Linux. We do not guarantee answers to Docker issues on other platforms.

### Installation Testing

To check whether Docker is installed successfully, run the `hello-world` image:

```bash
docker run hello-world
```

You should see a welcome message indicating your installation appears to be working correctly.

---

## 🚀 Launching xv6

### Launching the Docker Image of MP0

1. **Enter the cloned MP0 directory:**

   ```bash
   cd ntuos-2026-mp0
   ```

2. **Pull the Docker image:**

   ```bash
   docker pull ntuos/mp0
   ```

   > **Note:** The image only supports `x86_64` (or `amd64`) and `arm64` CPU architectures. Run `arch` to check your CPU architecture. If your platform isn't supported, email the TA with the output of your `arch` command.
3. **Run the container interactively:**

   ```bash
   docker run -it -v $(pwd)/xv6:/home/os_mp0/xv6 ntuos/mp0  
   ```

   This command makes the container interactive (`-it`) and mounts the `xv6` directory (`-v`). Volume mounting allows you to code outside the container with your favorite editor while changes seamlessly reflect inside.
4. **Verify the environment:**

   ```bash
   cat /etc/os-release
   ```

### QEMU Introduction

xv6 is implemented in ANSI C for a multi-core RISC-V system, but most machines are not RISC-V. Therefore, we use QEMU to launch xv6 on non-RISC-V architectures. QEMU is an emulator and virtualizer that performs hardware virtualization.

### Launching QEMU

In the `xv6` directory inside the Docker container, build and run xv6 on QEMU:

```bash
make qemu
```

You will see the kernel bootcamp and an interactive shell (`$`). Typing `ls` at the prompt will lists the files included in the initial file system (created by `mkfs`). You have successfully set up xv6!

**Useful QEMU Shortcuts:**

- `Ctrl` + `p` : Print information about each process.
- `Ctrl` + `a`, release, then `x` : Quit QEMU safely.

---

## 💻 Example MP: `mp0` Command

Below we provide an easy example MP. We assume you are proficient in C, familiar with System Programming, and willing to trace source code.

### The `tree` and `mp0` commands

[`tree`](https://linux.die.net/man/1/tree) is a command used to list contents of directories in a tree-like format. In this MP, we will implement `mp0` to mimic the traversing behavior of `tree`. However, you do not need to print in a tree format. Instead, you will count the occurrences of a given key in each traversed path.

### Detailed Steps

1. **Parse Arguments**: The `mp0` process reads two arguments.

   ```bash
   mp0 <root_directory> <key>
   ```

2. **Fork a Child**: The main process must `fork()` a child process.
3. **Traverse the Directory (Child Process)**: The child traverses files and directories under `<root_directory>`, outputting the path and the number of occurrences of the given key, separated by a space.
   - The traversing order must match the `ls` command.
   - Example path occurrence: `aa/a` with key `a` has an occurrence of `3`.

   ```bash
   <path> <occurrence>
   ```

   > **Path Concatenation Rule:**
   > You should separate the `<root_directory>` and its sub-directories with a single `/`. If `<root_directory>` already contains one or more `/` at the end, keep them, append exactly one `/`, and then the sub-directory name.

   **Error Handling:** If the `<root_directory>` does not exist or is not a directory, directly print:

   ```bash
   <root_directory> [error opening dir]
   ```

4. **Communicate via Pipe**: The child process must send two integers, `file_num` and `dir_num` (number of traversed files and directories), back to the parent process using a pipe.
   > `<root_directory>` itself **should not** be counted in `dir_num`.
5. **Print Statistics (Parent Process)**: The parent process reads the integers from the pipe and prints:

   ```bash
   <dir_num> directories, <file_num> files
   ```

   _You must separate the child's output and the parent's output with a blank line (printed by either process)._

> ⚠️ **CHEATING WARNING:** If you do not use a pipe to send `dir_num` and `file_num` to the parent process, you will receive **0 points** for this MP.

### Testcase Specifications

- `<key>` will only contain a single lowercase alphabet (a-z).
- The depth of `<root_directory>` is defined as `0`. The maximum traversed depth will be smaller than `5`.
- The total number of files and directories in a single testcase will not exceed `20`.
- The maximum length of each directory or file name is `10`.
- We will only test against regular files and directories (no device files).
- Testcases are guaranteed to provide valid parameters (no need to handle `< 2` parameter errors).

### Sample Outputs

- **Sample Testcase 1 (Normal Traversal)**

    ```bash
    $ testgen
    $ mp0 os2023 d
    os2023 0
    os2023/d1 1
    os2023/d2 1
    ...
    6 directories, 2 files
    ```

- **Sample Testcase 2 (Trailing Slashes)**

    ```bash
    $ testgen
    $ mp0 os2023/ d
    os2023/ 0
    os2023//d1 1
    os2023//d2 1
    ...
    6 directories, 2 files
    ```

- **Sample Testcase 3 (Error Directory)**

    ```bash
    $ mp0 os2202 d
    os2202 [error opening dir]

    0 directories, 0 files
    ```

### Public Testcases (70 Points)

You can judge your code by running `make grade` (or `./mp.sh grade` from the host template) in the environment. You can get **70 points** (out of 100) if you pass all public testcases. Note that you should only modify `xv6/Makefile` and `xv6/user/mp0.c`.

**Hints:**

1. Remember to close file descriptors when they are no longer needed.
2. Check `xv6/user/grind.c` and `xv6/user/ls.c` for function usage.
3. Set the buffer size to the maximum possible length of a path. Otherwise, recursive functions might cause a stack overflow.

### Grading Procedure

We will grade your submission by running an automated grading process in an isolated environment against your tested public cases, alongside hidden private testcases. 

| Category                | Points / Penalty | Description                                                                                                                                |
| :---------------------- | :--------------- | :----------------------------------------------------------------------------------------------------------------------------------------- |
| **Public Testcases**    | 70 Points        | Evaluated exactly as the tests you run locally with `./mp.sh grade`.                                                                       |
| **Private Testcases**   | 30 Points        | Hidden testcases evaluated after the deadline.                                                                                             |
| **Late Penalty**        | -20% per day     | Late submissions will be penalized by **20% of the maximum score per day late**.                                                           |
| **Public Repo Penalty** | **0 Points**     | If your GitHub repository is found to be `Public` at any time, your final grade will be strictly 0 to enforce academic integrity.          |
| **Identity Binding**    | **0 Points**     | If you fail to configure `student.conf` correctly (or leave default values), we cannot identify your submission, and your grade will be 0. |

---

## 📦 Submission

The submission instructions are identical across all homework assignments. Please strictly follow the comprehensive steps documented in the **[Homework Submission Guide](submit-guide.md)**.


## 📚 References

1. **[xv6](https://pdos.csail.mit.edu/6.828/2012/xv6.html)**: a simple Unix-like teaching operating system.
2. **[Docker](https://docs.docker.com/)**: Empowering App Development for Developers.
3. **[RISC-V](https://riscv.org/)**: The Free and Open RISC Instruction Set Architecture.
4. **[QEMU](https://www.qemu.org/)**: the FAST! processor emulator.
