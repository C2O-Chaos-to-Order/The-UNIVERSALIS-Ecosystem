# Engineering Doctor v0.1

Status: LIMITED / PUBLIC_CANDIDATE

A pass is not authorization, scientific validation, or independent verification.

Engineering Doctor is a read-only CLI. It inventories operator-configured
repositories, can detect stacked pull requests, README-versus-tree drift, and
conflicting status language, and can run optional public demo unittest
adapters. It writes an immutable JSON run record plus a Markdown brief.

It is not a dashboard, scheduler, model, authorization service, or release
authority.

This core is registered as `tool-001` in the repository-root
[Tool Registry](../registry/tools/tool-001.json). The registry itself is
LIMITED. A pass is not authorization, scientific validation, or independent
verification. Public requirement references `REQ-RUBY-01` and `REQ-ONYX-01`
point at existing tests; they are not a tablet-compliance claim. The default repository allowlist is empty: operators pass `--repo`
and/or `--allowlist-file`. There is no built-in private corpus list.

## What exists

- Package directory: `engineering_doctor/` at the repository root, so the
  command is `python -m engineering_doctor run` from that root.
- A configurable allowlist (empty by default) and optional `--exclude` names.
- Public demo suite adapters for the already-public `prototype/` and
  `scaffold/` unittest suites in this repository, pinned to
  `3c521a82ee1404bd09d219c59ff6a466cb0721d0`.
- Default-branch inventory: SHA, empty or not, open and draft pull-request
  counts, pull-request age, behind-count where the compare API succeeds, and
  stacked pull requests whose base is not the default branch.
- README-versus-tree path checks and status-claim mismatch detection, including
  an `EXA-001` synthetic regression fixture under
  [tests/fixtures](tests/fixtures).
- JSON schema: [schema/run_record.v0.1.json](schema/run_record.v0.1.json).
- Core tests that run with the standard library `unittest` runner, including
  an automated leak test.
- Optional extra: [extras/requirements-extra.txt](extras/requirements-extra.txt)
  pins pytest and Hypothesis with hashes. The extra is not required to run the
  doctor or the core tests.

## How to run

From the repository root, with Python 3.14 or Python 3.11:

```text
python -m engineering_doctor run --output-dir /tmp/engineering-doctor-runs --repo The-UNIVERSALIS-Ecosystem
```

The default output directory is under the system temp directory, outside this
repository. Each run creates a new subdirectory and will not overwrite an
existing record.

GitHub access is GET only. The client uses `GITHUB_TOKEN` or `GH_TOKEN` if
set, otherwise `gh auth token` if that command works, otherwise the
unauthenticated API. Tokens are not written to records or logs.

`--repo NAME` may be repeated to limit inventory. `--allowlist-file PATH`
restricts names to a configured list. `--exclude NAME` refuses a name if it
is requested.

## Core tests

```text
python -m unittest discover -s engineering_doctor/tests -t . -v
```

These tests use only the Python standard library and synthetic fixtures.

## Leak test

The leak test hashes identifiers and sliding word n-grams (length 2-6) from
every public file after UTF-8 lowercase normalization and URL-unquoting. It
compares those SHA-256 digests to
[tests/leak_denylist.sha256](tests/leak_denylist.sha256). The denylist stores
only hex digests, so it does not restate private repository names, collection
names, corpus path fragments, or internal classification words. A match fails
the build. The scan covers this component and other repository files except
the pre-existing `prototype/` and `scaffold/` trees, which have their own
clause-leak tooling and are not rewritten by this component. The scanner and
approach are documented in [tests/leakscan.py](tests/leakscan.py).

## Optional extra tests

```text
python -m pip install --require-hashes -r engineering_doctor/extras/requirements-extra.txt
python -m pytest engineering_doctor/extras/test_properties.py
```

## What this version checks

1. Configured suite adapters, captured as discovered / passed / failed /
   error / skipped / timeout / not-run counts. Public demo adapters may run
   only the already-public prototype and scaffold suites.
2. Inventory of operator-configured repositories.
3. Stacked pull requests whose base is not the default branch, including
   whether checks were visible.
4. README-versus-tree drift on default branches (named paths that do not exist,
   and a "product implementation not yet started" sentence when implementation
   directories exist).
5. Status-claim mismatches such as an artifact header that says Draft or Not
   Ratified while another document calls the same ID Ratified.

Findings use Critical, High, Medium, or Low and always include a written basis.
The tool does not emit a readiness percentage or confidence score.

## What CI does and does not cover

The workflow [engineering-doctor.yml](../.github/workflows/engineering-doctor.yml)
runs the core stdlib unittest suite, including the leak test, on Python 3.11
and Python 3.14 when those interpreters are available. It has read-only
permissions. It does not execute the doctor against live repositories and does
not authorize a release.

## What is not verified

- Authorization, scientific validation, independent review, or programme credit.
- Feature-branch contents that the default-branch API does not return.
- Completeness of GitHub search across every historical ref.
- Security certification, load, or identity enforcement.

A missing repository, API error, unreadable file, parser failure, timeout, or
zero-test run is reported as UNKNOWN or as a finding. Those outcomes are never
treated as a pass.
