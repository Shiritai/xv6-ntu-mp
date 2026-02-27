# xv6-ntu-mp

This is the repository for the Operating Systems course (CSIE 3310) at National Taiwan University, Spring 2026. It contains the source code for the machine problems (MPs).

## Machine Problem 0 (MP0)

**Goal:** Setup the xv6 environment and implement a simple directory traversal command `mp0`.

*   **Specification:** [doc/mp0.md](doc/mp0.md)
*   **Environment & Architecture:** [doc/environment.md](doc/environment.md)
*   **Homework Submission Guide:** [doc/submit-guide.md](doc/submit-guide.md)
*   **Original xv6 README:** [README](https://github.com/mit-pdos/xv6-riscv/blob/riscv/README)

## Quick Start

We provide a script `mp.sh` to help you build and run xv6 using Docker. This ensures a consistent environment across different platforms.

### 1. Build and Run xv6 (QEMU)

```bash
./mp.sh qemu
```

### 2. Run Tests

```bash
./mp.sh grade
```

### 3. Clean Build Artifacts

```bash
./mp.sh clean
```

### 4. Grading System
Our grading system uses a **Late-Release Plaintext Test** model:
1.  **Development Phase**: Running `./mp.sh grade` or pushing to your repository will only execute the **Public Tests**.
2.  **Grading Phase**: After the deadline and late submission period, the TA will release the **Private Tests** (as plaintext `.py` files) directly to your repository and trigger the official grading CI.
3.  **Sanitization**: The official grading environment is automatically managed to ensure a clean and fair evaluation.

### 5. File Protection System
To prevent accidental changes to critical files (like `mp.sh`, `Makefile`, or grading scripts) that will be overwritten during official grading, we include a protection system:
- **Protected List**: See `doc/protected_list.txt` for the list of files that you should NOT modify.
- **Git Hooks**: We provide `pre-commit` and `pre-push` hooks to detect and block illegal modifications.
- **Setup**: Run `./mp.sh init` once to install these hooks into your local repository.

---

## Original xv6-riscv Introduction

xv6 is a re-implementation of Dennis Ritchie's and Ken Thompson's Unix Version 6 (v6). xv6 loosely follows the structure and style of v6, but is implemented for a modern RISC-V multiprocessor using ANSI C.

ACKNOWLEDGMENTS

xv6 is inspired by John Lions's Commentary on UNIX 6th Edition (Peer to Peer Communications; ISBN: 1-57398-013-7; 1st edition (June 14, 2000)). See also https://pdos.csail.mit.edu/6.828/, which provides pointers to on-line resources for v6.

The following people have made contributions: Russ Cox (context switching, locking), Cliff Frey (MP), Xiao Yu (MP), Nickolai Zeldovich, and Austin Clements.

We are also grateful for the bug reports and patches contributed by many others.
