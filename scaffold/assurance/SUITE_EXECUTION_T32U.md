# Suite execution evidence

Recorded by the agent that made the corrections. Nothing here is written from
memory: every count and exit code was produced by the commands below, in the
working directory below, and the verbatim output is copied from the captured
streams.

**This is not an independent verification.** The same party wrote the tests and
ran them. It records what happened so someone else can re-run it and disagree.

## Environment

| Item | Value |
|---|---|
| Date of run | 2026-10-31 |
| Interpreter | `3.13.5` |
| Full version | `3.13.5 (main, Aug 10 2026, 12:06:59) [GCC 14.2.0]` |
| Platform | `Linux-6.12.94+-x86_64-with-glibc2.41` |
| Working directory | `/workspace/work/p4-work` |
| Branch | `hf06/record-validator-semantics` |
| Base commit | `c1020a9`, with the corrections committed on top |
| Test runner | stdlib `unittest`; no pytest is installed |

There is no `python` on `PATH` here, so the interpreter is invoked by absolute
path.

## Results

| Suite | Before the corrections | After the corrections | Exit code (after) |
|---|---|---|---|
| `scaffold/tests` | Ran 197 tests, `OK (skipped=1)` | Ran 268 tests, `OK (skipped=1)` | **0** |
| `prototype/tests` | Ran 69 tests, `OK` | Ran 69 tests, `OK` | **0** |

No test failed in either suite at any point, before or after. The one skip is
unchanged by this work and requires a private corpus that is absent here, so it
is a skip and not a pass:

```
test_real_corpus_parses_with_thirteen_clauses_per_file
(test_corpus_probe.RealCorpusIntegrationTests...) ... skipped
'set C2O_CORPUS_ROOT to a private corpus root to run this'
```

## Exact commands

Both run from `/workspace/work/p4-work`.

```
/workspace/work/manuscript-intake/venv/bin/python -m unittest discover -s scaffold/tests
```

```
/workspace/work/manuscript-intake/venv/bin/python -m unittest discover -s prototype/tests
```

## Captured output: scaffold suite, after the corrections

stdout was empty; `unittest` writes its report to stderr. Exit code: 0.

```
.....................................s......................................................................................................................................................................................................................................
----------------------------------------------------------------------
Ran 268 tests in 4.997s

OK (skipped=1)
```

## Captured output: prototype suite, after the corrections

stdout was empty. Exit code: 0. The suite also emits 32 `ResourceWarning:
unclosed database` lines, from `prototype/universalis/store.py` at lines 515
(30 lines) and 805 (2 lines). Counted from the captured stream, and identical
in the run before the corrections, so they pre-date this work and are unrelated
to it. The suite exits 0 with them present.

```
  placeholders = ", ".join("?" for _ in columns)
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/workspace/work/p4-work/prototype/universalis/store.py:515: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x7f3e03990040>
  placeholders = ", ".join("?" for _ in columns)
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/workspace/work/p4-work/prototype/universalis/store.py:515: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x7f3e03990130>
  placeholders = ", ".join("?" for _ in columns)
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/workspace/work/p4-work/prototype/universalis/store.py:515: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x7f3e03990220>
  placeholders = ", ".join("?" for _ in columns)
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/workspace/work/p4-work/prototype/universalis/store.py:515: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x7f3e03a90c70>
  placeholders = ", ".join("?" for _ in columns)
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/workspace/work/p4-work/prototype/universalis/store.py:515: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x7f3e03a90d60>
  placeholders = ", ".join("?" for _ in columns)
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/workspace/work/p4-work/prototype/universalis/store.py:515: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x7f3e03990310>
  placeholders = ", ".join("?" for _ in columns)
ResourceWarning: Enable tracemalloc to get the object allocation traceback
....................................
----------------------------------------------------------------------
Ran 69 tests in 0.068s

OK
```

## Captured output: scaffold suite, before the corrections

Measured on the unmodified tree at `c1020a9`, so the "before" figure is a real
run rather than a recollection. Exit code: 0.

```
.....................................s...............................................................................................................................................................
----------------------------------------------------------------------
Ran 197 tests in 3.986s

OK (skipped=1)
```

## Captured output: prototype suite, before the corrections

Exit code: 0.

```
  placeholders = ", ".join("?" for _ in columns)
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/workspace/work/p4-work/prototype/universalis/store.py:515: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x7fcd79188040>
  placeholders = ", ".join("?" for _ in columns)
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/workspace/work/p4-work/prototype/universalis/store.py:515: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x7fcd79188130>
  placeholders = ", ".join("?" for _ in columns)
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/workspace/work/p4-work/prototype/universalis/store.py:515: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x7fcd79188220>
  placeholders = ", ".join("?" for _ in columns)
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/workspace/work/p4-work/prototype/universalis/store.py:515: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x7fcd79284c70>
  placeholders = ", ".join("?" for _ in columns)
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/workspace/work/p4-work/prototype/universalis/store.py:515: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x7fcd79284d60>
  placeholders = ", ".join("?" for _ in columns)
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/workspace/work/p4-work/prototype/universalis/store.py:515: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x7fcd79188310>
  placeholders = ", ".join("?" for _ in columns)
ResourceWarning: Enable tracemalloc to get the object allocation traceback
....................................
----------------------------------------------------------------------
Ran 69 tests in 0.068s

OK
```

## What these runs establish, and what they do not

They establish that, on this interpreter and platform, every non-skipped test
case in both suites passed and each runner exited 0.

They do not establish that the software is correct, that a requirement is
accepted, that a finding is true, or that anything is authorized. A passing
test shows that the tested behaviour matches its test case, nothing more.
Nothing here has been independently reproduced.
