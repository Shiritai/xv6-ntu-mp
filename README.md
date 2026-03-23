# 💻 xv6-ntu-mp: Operating Systems CSIE 3310

Welcome to the official repository for the Operating Systems course at National Taiwan University. This platform provides a modern, automated development environment for xv6 assignments.

## 🌟 Why This New System?

In the past, students often struggled with complex, manual toolchain setups that varied across operating systems, leading to "it works on my machine" frustrations. The **xv6-ntu-mp** system replaces this with a modern, integrated approach:

- **Unified & Transparent Environment**: We leverage **Docker** and **GitHub Actions** to provide a strictly identical development and grading environment for everyone—from your local laptop to the cloud.
- **Instant Professional Feedback**: No more waiting for manual TA checks. Automated cloud grading provides immediate scores and detailed logs as soon as you push your code.
- **Human-Centric Guidance**: Instead of simple "blocking" errors, our system includes Git hooks and protective scripts that act as a development assistant, catching common mistakes (like missing identity or accidental file overwrites) before they become grading issues.
- **Continuous Learning Loop**: Even after the deadline, private tests are released into your repository. This allows you to identify subtle concurrency bugs or edge cases and continue refining your skills long after the assignment is over.

## 📂 Project Structure

A quick guide to navigating this repository:

- **`xv6/`**: The core source code of the operating system.
  - **`user/`**: Where you add and modify user programs.
  - **`kernel/`**: The core kernel logic (process management, traps, etc.).
  - **`Makefile`**: Standard build configuration for the xv6 kernel.
- **`doc/`**: Comprehensive documentation module.
- **`grade/`**: Internal grading engine logic (Do not modify).
- **`tests/`**: Contains both official public tests and your custom debug tests.
- **`checklist.md`**: Self-check list for submission.
- **`mp.sh`**: The centralized assignment management script—your primary interface.
- **`student.conf`**: Your identity binding configuration.

## ⚡ Documentation Guide

For a tailored onboarding experience, explore our modular guides:

### 1. [Onboarding & Initialization (doc/setup.md)](doc/setup.md)

> **🆕 Start Here.** Learn how to fork the template, invite TAs, and initialize your local workspace.

### 2. [Developer Handbook (doc/handbook.md)](doc/handbook.md)

> **🛠️ Technical Reference.** Dive into `mp.sh` commands, QEMU shortcuts, and the system architecture diagram.

### 3. [Submission & Grading Workflow (doc/workflow.md)](doc/workflow.md)

> **🔄 Mastering the Cycle.** Understand how to create custom tests, interpret GitHub Actions results, and the rules of the grading cycle.

### 4. Assignment Specification

- [`doc/mp2.md`](doc/mp2.md): MP2 Specification
- [`doc/mp2-test.md`](doc/mp2-test.md): MP2 Testing guide
- [`doc/mp2-guide.md`](doc/mp2-guide.md): Slab allocator Technical guide

> **📋 Task Requirements.** Detailed technical specifications and goals for the current Machine Problem.

## 📚 References

- **[xv6: A Simple Unix-like OS (PDF)](https://pdos.csail.mit.edu/6.828/2020/xv6/book-riscv-rev1.pdf)**: The primary textbook for the course.
- **[GitHub: xv6-riscv Upstream](https://github.com/mit-pdos/xv6-riscv)**: Original MIT source code.
- **[RISC-V ISA Reference](https://riscv.org/technical/specifications/)**: For deep-dives into the architecture.
