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
      <td>Wed. 13:00-14:00, Thr. 12:30-13:30</td>
    </tr>
  </table>
</div>

<hr />

## 📋 Table of Contents

- [💬 Discussion Policy](#-discussion-policy)
- [📝 Summary](#-summary)
- [💻 MP0: xv6 Directory Traversal (`mp0`)](#-mp0-xv6-directory-traversal-mp0)
  - [1. Task Description](#1-task-description)
  - [2. Output Specification](#2-output-specification)
  - [3. Example Execution](#3-example-execution)
  - [4. Technical Constraints](#4-technical-constraints)
  - [5. Development Tips](#5-development-tips)
  - [6. Local Verification](#6-local-verification)
- [📂 Appendix: Manual Setup & Troubleshooting](#-appendix-manual-setup--troubleshooting)

---

## 💬 Discussion Policy

If you have any questions about this machine problem, please post them on the corresponding NTU COOL discussion board. We have opened a discussion dedicated to MP0. For special requests, you can email [ntuos@googlegroups.com](mailto:ntuos@googlegroups.com).

## 📝 Summary

**xv6** is an example kernel created by MIT for pedagogical purposes. We will study xv6 to get familiar with the main concepts of operating systems. The reference book for xv6 is [xv6: a simple, Unix-like teaching operating system](https://pdos.csail.mit.edu/6.828/2020/xv6/book-riscv-rev1.pdf). You will learn to set up the environment for xv6 and develop a custom `mp0` command in this MP.

### 🛠️ Environment Setup

Before starting this machine problem, you **must** complete the initial environment setup. Please refer to the **[Setup Guide](setup.md)** for detailed installation steps, including Docker and repository initialization.

---

## 💻 MP0: xv6 Directory Traversal (`mp0`)

The goal of this assignment is to understand the core concepts of xv6 process creation (`fork`), inter-process communication (`pipe`), and filesystem navigation. You will implement a directory traversal tool that mimics the depth-first traversing behavior of the Linux `tree` command but with custom counting logic.

### 1. Task Description

Implement a user-space command `mp0 <root_directory> <key>` that traverses the filesystem tree starting from `<root_directory>`. For every file and directory encountered, it must count how many times the character `<key>` appears in its relative path from the root.

#### Technical Requirements

1. **Multi-processing (`fork`)**:
    - The main (parent) process must `fork()` a child process.
    - The **child process** is responsible for the actual recursive traversal of the filesystem.
    - The **parent process** must wait for the child to finish and then print the final summary.

2. **Inter-Process Communication (`pipe`)**:
    - The child process must count the **total number of directories** and **total number of files** it successfully visited *under* the root.
    - At the end of its traversal, the child must send these two integer counts back to the parent using a **Pipe**.
    - If the child fails to use a pipe for communication, the assignment will be graded as **0 points**.

3. **Recursive Traversal**:
    - You must visit every file and sub-directory reachable from the `<root_directory>`.
    - **Order**: Within any directory, the entries must be visited in the order they appear in the directory (matching the output of the xv6 `ls` command).
    - **Self-inclusion**: The `<root_directory>` itself is the first entry to be printed but **does not** count toward the final directory tally.

### 2. Output Specification

#### Real-time Trace

For every entry (directory or file), print a line for its traversal:

```text
<path> <count>
```

- `<path>`: The relative path from the root.
- `<count>`: The number of times the character `<key>` appears in the `<path>` string.

> [!IMPORTANT]
> **Path Concatenation Rule (Trailing Slashes)**:
> You must separate the `<root_directory>` and its sub-entries with a `/`.
>
> - If `<root_directory>` **already ends** with one or more `/`, you must keep them **and** still append exactly one `/` before the sub-entry name. (e.g., `dir/` + `file` becomes `dir//file`).

#### Summary (Parent Process)

After the child exits, the parent reads the pipe and prints:

```text
<dir_count> directories, <file_count> files
```

> [!NOTE]
> **Formatting Requirement**: You must separate the child's trace output and the parent's summary output with a **blank line** (printed by either process).

#### Error Handling

If the `<root_directory>` cannot be opened, does not exist, or is a file, the child should print:

```text
<path> [error opening dir]
```

Do not traverse into directories that failed to open. The parent should still print the summary (0 directories, 0 files) after the error message and the required blank line.

### 3. Example Execution

Assume a directory structure:

```text
.
└── d1
    ├── a.txt
    └── d2
        └── b.txt
```

Running `mp0 d1 d`:

```bash
$ mp0 d1 d
d1 1
d1/a.txt 1
d1/d2 2
d1/d2/b.txt 2

1 directories, 2 files
```

Running `mp0 d1/ d`:

```bash
$ mp0 d1/ d
d1/ 1
d1//a.txt 1
d1//d2 2
d1//d2/b.txt 2

1 directories, 2 files
```

### 4. Technical Constraints

- **Single Character Key**: The second argument `<key>` is always a single character (a-z).
- **Buffer & Path**: Path length will not exceed 128 characters. Filenames will not exceed 12 characters.
- **Complexity**: Maximum traversal depth is 16. Total files/dirs in a testcase will not exceed 64.
- **Pipe Protocol**: The child should write exactly two integers (or a struct) to the pipe. The parent must read them correspondingly.

> [!CAUTION]
> **Strict Compliance**
>
> - **Must use `fork()`**: Doing everything in a single process is invalid.
> - **Must use `pipe()`**: Using global variables (which aren't shared across processes) or files for communication is invalid.
> - **Zero Score**: Failure to follow these architectural requirements results in 0 points regardless of output correctness.

### 5. Development Tips

- **Starting Point**: Study `xv6/user/ls.c` to understand how to read a directory and use `fstat` to distinguish between files and directories.
- **Recursion**: When you find a directory (that is not `.` or `..`), construct the new path and call your traversal function recursively.
- **Pipe Handling**: Remember to close the unused ends of the pipe in both the parent and child processes to avoid hangs or resource leaks.

### 6. Local Verification

To run the automated public tests:

```bash
./mp.sh grade
```

For more information on reading grades and logs, refer to the [Workflow Guide](workflow.md).

---

## 📂 Appendix: Manual Setup & Troubleshooting

### Why Docker?

We leverage containerization to standardize the homework environment, making problems independent of your machine's hardware or OS architecture. For a deep dive into our virtualization strategy, see the **[Developer Handbook](handbook.md)**.

### Manual Setup (Manual Docker Pull/Run)

If you prefer not to use `mp.sh`, you can manually interact with Docker:

```bash
docker pull ntuos/mp0
docker run -it -v $(pwd):/home/student/xv6 -w /home/student/xv6 ntuos/mp0
```

### Troubleshooting QEMU

- If QEMU hangs, try `make clean` and verify your Docker setup.
- Remember the exit shortcut: `Ctrl-a` then `x`.

### References

1. [xv6: A Simple Unix-like OS](https://pdos.csail.mit.edu/6.828/2020/xv6/book-riscv-rev1.pdf)
2. [RISC-V ISA](https://riscv.org/)
3. [QEMU Emulator](https://www.qemu.org/)
