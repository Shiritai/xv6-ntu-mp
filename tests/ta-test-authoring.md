# TA Guide: Authoring `test_mpx.py`

Reference for writing a grading test file for a new machine problem.
The `test_mp2.py` in the mp2 repo is the canonical example throughout.

---

## 1. The `@test` Decorator

```python
from gradelib import *

@test(points, title=None, needs=None, enable_on=None)
def test_foo():
    ...
```

| Parameter  | Type       | Meaning |
| :--------- | :--------- | :------ |
| `points`   | `int`      | Maximum points this test can award. |
| `title`    | `str`      | Display name and lookup key. Defaults to the function name with `test_` stripped and `_` -> space. Always set it explicitly for readability. |
| `needs`    | `list[str]`| Titles of tests this test depends on. Controls CI wave placement (see section 3). |
| `enable_on`| `int`      | Score threshold: sum of scores for all `needs` titles must reach this value before the test body runs. |

A test function may return an `int <= points` for partial credit, or raise `AssertionError` to fail.

---

## 2. Scoring Modes

### Binary (most tests)

Raise `AssertionError` on failure; return nothing (or return the full point value).

### Partial credit

Return an integer between 0 and `points`. The runner treats any return value `r` where `0 <= r <= points` as the actual score.

### Score-gated bonus

Call `gradelib.is_enabled_on_score()` at the top of the body and return 0 immediately when it is `False`. This guard is a no-op locally (where `GRADES_HISTORY` is empty) so the test always runs during development.

```python
@test(5, "In-cache objs (Bonus)", needs=_PUBLIC_TESTS, enable_on=70)
def test_cache_bonus_check():
    if not gradelib.is_enabled_on_score(): return 0 # early exit for not eligible score
    ...
```

---

## 3. Wave System and `needs`

The CI pipeline places tests into execution waves based on the `needs` graph:

| Wave | Depth | How to declare |
| :--- | :---- | :------------- |
| **wave-0** | 0 - no dependencies | `needs` omitted or `needs=[]` (default) |
| **wave-1** | 1 - depends only on wave-0 tests | `needs=<list of wave-0 titles>` |
| **wave-seq** | >= 2 - sequential overflow, depends at least on one of wave-1 tests | automatically assigned |

wave-1 jobs download all wave-0 artifacts, compute a score snapshot, then run.
Declaring `needs` does not skip a test locally -- it only controls CI ordering and `enable_on` evaluation.

### Capturing wave-0 titles

Call `gradelib.registered_titles()` after all regular tests are registered and before defining bonus tests. This returns a snapshot of titles in registration order.
> [!WARNING]
> Private Tests are also considered in `WAVE_0`, the `enable_on` might act differently.

```python
# After all wave-0 tests are registered:
_WAVE_0_TESTS = gradelib.registered_titles()

# Subset for a tighter threshold:
_PUBLIC_TESTS = [t for t in _WAVE_0_TESTS if t.startswith("public/")]

@test(10, "Spinlock Correctness Bonus (Bonus)", needs=_PUBLIC_TESTS, enable_on=60)
def test_spinlock_bonus():
    if not gradelib.is_enabled_on_score(): return 0
    ...
```

### Accessing prior scores

`gradelib.GRADES_HISTORY` is a `dict[str, int]` mapping test title to actual score. In CI it is populated from the wave-0 artifact before wave-1 runs. Locally it accumulates as tests execute in order.

```python
public_scores = {t: gradelib.GRADES_HISTORY.get(t, 0) for t in _PUBLIC_TESTS}
if all(public_scores[t] > 0 for t in _PUBLIC_TESTS):
    return 10
```

---

## 4. Runner and QEMU

```python
r = Runner(stop_on_line(r".*panic:.*"), stop_on_line(r".*\[MP2\] <FAILED>.*"))
r.run_qemu(shell_script(["echo Ok"]), timeout=60)
# r.qemu.output -- full captured stdout as a string
```

### Common monitors

| Monitor | Effect |
| :------ | :----- |
| `stop_on_line(regexp)` | Terminate QEMU when a line matches the regexp. |
| `shell_script(lines)` | Feed `lines` to the xv6 shell one at a time, stop when the script finishes. |
| `save(path)` | Write QEMU output to `path`; copy to `path.failed` on test failure. |

Call `reset_fs()` before a run that needs a clean filesystem state.

---

## 5. Dynamic Test Generation

For script-driven tests, generate `@test` wrappers at module load time so `discover.py` sees them:

```python
def create_mpx_test(test_name, script_file, points, sub_dir="TestMeta", timeout=120):
    @test(points, test_name)
    def test_case():
        ...
    return test_case

def discover_tests():
    for script_file in sorted(glob.glob("tests/public/mpx-*.txt"), key=natural_sort_key):
        basename = os.path.basename(script_file)
        create_mpx_test(f"public/{basename}", script_file, 3, sub_dir="public")
    ...

discover_tests()
```

Call `discover_tests()` before defining bonus tests so that `registered_titles()` captures the dynamically registered titles.

---

## 6. Registration Order and Report Stability

`aggregate_results.py` sorts collected results by the `order` field, which `discover.py` sets to the index in `gradelib.TESTS` at discovery time. Registration order therefore controls the report order. Define tests top-to-bottom in the order you want them to appear in the grade report.

---

## 7. Local vs CI Behavior

| Concern | Local (`./mp.sh grade`) | CI (GitHub Actions) |
| :------ | :---------------------- | :------------------ |
| `GRADES_HISTORY` | Populated as tests run in order | Injected from prior wave artifacts via `--inject-history` |
| `is_enabled_on_score()` | Always returns `True` (empty history) | Returns `True` only when threshold is met |
| Wave ordering | All tests run sequentially | wave-0 -> wave-1 -> wave-seq in parallel/parallel/sequential stages |
| Dependency cycle | No effect (tests still run) | `discover.py` detects cycle and aborts workflow before any test runs |

---

## 8. Checklist for a New MP

1. Create `tests/test_mpx.py` with `from gradelib import *`.
2. Register all regular (non-bonus) tests, including dynamic ones via `discover_tests()`.
3. Call `_WAVE_0_TESTS = gradelib.registered_titles()` as a divider.
4. Define bonus tests with `needs=_WAVE_0_TESTS` (or a subset) and an `enable_on` threshold.
5. Guard each bonus body with `if not gradelib.is_enabled_on_score(): return 0`.
6. Run `python3 grade/discover.py --stdout` locally and verify the emitted `waves` and `overflow` lists look correct.
