# UNIVERSALIS prototype

A local, read-only continuity and research prototype. It stores assertions in SQLite, answers questions about them, and refuses a result that would hide a failure, a conflict, or a gap.

This is a bounded prototype. A passing test does not make a requirement accepted, reviewed, or sufficient. Nothing here is a security certification, an accessibility conformance claim, or a statement that the capability is safe, correct, or complete.

## What it does

Stages P0, P1, P2, P3, P5, P6, and P7 from the prototype plan, with requirement identifiers in the `ULC-<tablet>-<clause>` form:

| Stage | What the code does | Requirements the plan assigns |
|---|---|---|
| P0 | Append-only records, typed references, separate provenance fields, four clocks, offset timestamps | ULC-00-02, ULC-00-05, ULC-00-06, ULC-00-10, ULC-18-02, ULC-18-03, ULC-18-04, ULC-18-05, ULC-18-06 |
| P1 | Evidence states kept apart from transport outcomes; conflicts, retention, and readiness | ULC-00-01, ULC-00-09, ULC-00-12, ULC-18-01, ULC-18-07, ULC-18-08, ULC-21-08 |
| P2 | Coverage that must reconcile, and views that disclose filters and generation | ULC-16-02, ULC-18-10, ULC-21-02, ULC-21-05, ULC-21-10, ULC-21-11 |
| P3 | Six distinguishable route outcomes; a failed route is not an empty corpus | ULC-16-07, ULC-16-12, ULC-21-06 |
| P4 | No close list under the corrected mapping | none |
| P5 | Invalidation reopens transitive dependents and keeps the prior decision | ULC-21-07, together with P1 and P2 |
| P6 | Status text plus a machine value; claim rendering | ULC-21-01, ULC-21-03, ULC-21-09 |
| P7 | In-memory authorization stub | ULC-00-11, ULC-00-12 (partial), ULC-16-05, ULC-16-11, ULC-26-03, ULC-26-05 |

P5 is not claimed to close anything besides ULC-21-07. P6 and P7 are not claimed to close anything besides the identifiers in those rows.

The corrected mapping does not assign a close list to P4. Invalidation is P5, presentation is P6, and the authorization stub is P7.

## Reciprocal stewardship policy prototype

`universalis/stewardship.py` is an isolated advisory policy prototype described in [`STEWARDSHIP.md`](STEWARDSHIP.md). It never grants execution authority, changes permissions, performs containment, restores capabilities, or starts delegated systems. Its caller-supplied identity, evidence, and prohibition references are not authenticated by the module. It is not wired into the store or authorization stub and is not a governing policy.

## What it deliberately is not

- No network, no model inference, no credentials, and no third-party packages. The Python standard library is the only dependency.
- No write outside the process-local SQLite store.
- The authorization type is an in-memory stub. It proves nothing about a real identity provider. It is not an identity provider, and a permit it returns is not evidence that anyone was authenticated.
- ULC-16-05 is only the checks this code can make: an explicit analogy or metaphor kind is rejected, and a source without a scoped origin is rejected. Wording that is figurative but well-formed as an origin is not detected.
- ULC-00-12 is partial on P7. Readiness has four distinct states, and tooling is refused `reviewed`, `accepted`, and `authorized`. A reviewer transition is not implemented.
- The separate evidence-package tool (research cases, executed result files, ledgers, and a validator that re-runs these tests) is not built.
- Requirement identifiers here are tablet identifiers of the form `ULC-<tablet>-<clause>`. They are not the collection-level `UNI-001`…`UNI-015` map, which is a different register and is not cited as a requirement of this prototype.

`REQUIREMENT_TRACE.md` lists every register identifier. Thirty-one are not implemented, and the trace says so. A passing test is not acceptance.

## How to run the tests

From the repository root:

```bash
python -m unittest discover -s prototype/tests -v
```

A throwaway demonstration of the guards:

```bash
python prototype/demonstrate_guards.py
```

Import without site packages:

```bash
python -S -c "import sys; sys.path.insert(0, 'prototype'); import universalis"
```

## Resolutions recorded while building

- Evidence states are `supported`, `disputed`, `missing`, `stale`, `corrupted`, `pending_review`, and `unknown`. Transport outcomes are `ok`, `empty`, `failed_request`, `truncated`, `denied`, and `unavailable`. Route outcomes add `missing` for an absent record. `missing` as a route outcome and `missing` as an evidence state are different types. `failed_request` is not an evidence state, and it is not stored as `missing` or as `empty`.
- A conflict uses evidence state `disputed` plus an explicit contradiction record. The vocabulary has no separate `conflicted` value. A newer witness does not select an account. A resolution is an appended decision; it does not delete witnesses and it does not crown the newest account.
- Coverage refuses a report whose counts do not reconcile. The residual is an investigation item on the exception. It is not rounded and it is not printed as a footnote on a report. The coverage identity is `declared_population = resolved + unresolved + excluded`, `in_scope_total = resolved + unresolved`, `unresolved = missing + unavailable + unresolved_other`, and `in_scope_total = shown + filtered`. The denominator is the declared population. Exclusions are reported beside it. `reconcile_boundary` uses `sources = sinks + exclusions + observed` and refuses a non-zero residual, including when the caller asks for that residual to be rounded.
- The only column on a stored account that a later write may change is `superseded_by`. A database trigger aborts every other update and every delete. That column points at the successor. It is not a change to the prior account.
- The uploaded plan file still uses a different stage numbering and a different identifier prefix. This tree follows the corrected `ULC-` identifiers and the corrected P5, P6, and P7 close lists.
