# Programme package contract

This document is the contract for one programme package. The scaffold checks whether a package obeys the contract. A passing check is a statement about records, hashes, and claims inside that package. It is not a research finding, a scientific validation, a security certification, a production validation, or a release authorization.

Clause text stays outside this repository. A package may cite a clause by identifier only. Requirement ids use the form `ULC-<tablet>-<clause>`. Shape examples are `ULC-18-10`, `ULC-00-01`, and `ULC-26-05`. `ULC-00-01` in the templates is an example placeholder, not a corpus clause. These ids are not the separate collection-level register `UNI-001`…`UNI-015`.

The evidence-record field names are the governing Plan's names. See [PLAN_SCHEMA_CONFORMANCE.md](PLAN_SCHEMA_CONFORMANCE.md).

Three fields describe three different things and are never collapsed into each other:

| Field | Question it answers | Values |
| --- | --- | --- |
| `evidence_status` | How far has the *evidence* for this claim been established? | The Plan's eight states (§ Evidence ladder) |
| `execution_outcome` | What did the *run* actually do? | `not_executed`, `executed`, `failed`, `incomplete` |
| `authorization_status` | Has someone *authorized* this? | `NOT_AUTHORIZED` (default), `AUTHORIZED` |

`authorization_status` defaults to `NOT_AUTHORIZED`. Nothing in the tooling copies `evidence_status` into `authorization_status`, and an `evidence_status` of `authorized` does not set and does not imply `authorization_status` of `AUTHORIZED`. The validator refuses either value on another field's axis.

## Package layout

```text
README.md
metadata/programme_status.json
metadata/sha256_manifest.json
metadata/classifications.json
metadata/environment.json
sources/source_register.json
clauses/clause_references.json
research/research_records.json
research/<record_id>.md
simulations/scenarios.json
simulations/model.py
simulations/run_one.py
simulations/run_all.py
results/execution_log.json
results/<simulation_record_id>.json
requirements/requirements.json
ledgers/research_ledger.csv
ledgers/simulation_ledger.csv
ledgers/checkpoint_schedule.csv
ledgers/requirements.csv
ledgers/dimensions.csv
ledgers/levels.csv
ledgers/phases.csv
ledgers/relationships.csv
ledgers/model_family_summary.csv
ledgers/report_index.csv
reports/
decisions/
```

`metadata/sha256_manifest.json` maps every other file's relative path to a lowercase SHA-256 of its bytes. Paths are package-relative. The manifest does not list itself, and it does not list absolute paths or `..`.

`metadata/classifications.json` maps every file, including the manifest, to a release classification. The default and public-release profiles require `PUBLICLY_CLEARED`. The internal-candidate profile also admits `INTERNAL_CANDIDATE`, but such packages must be stored in a private repository or private workspace and are never release-ready.

## Classification profiles and release authorization

The default profile preserves the historical `PUBLICLY_CLEARED`-only gate and always reports `release_ready: false`. The `internal-candidate` profile admits `INTERNAL_CANDIDATE` and `PUBLICLY_CLEARED`, but refuses package paths inside this public repository and never reports release readiness. The `public-release` profile requires every file and record to be `PUBLICLY_CLEARED`, a cited owner decision with `authority: owner`, `authorization_status: AUTHORIZED`, and the programme ID in `target_ids`, and the public-source-repository check described below. A classification label is not release authorization. The validator checks the decision citation's shape; it cannot authenticate the owner or prove the decision was genuinely made.

## Public-source-repository check

The `public-release` profile adds a `public_source_repository` check. A source with any Git locator field (`repository`, `path`, `commit`, or `blob_sha`) must satisfy the complete four-field D09 locator contract and identify the same repository as `metadata/programme_status.json` `repository`. A source that points to another repository is refused unless an owner exception record in `decisions/` names that source and has `authority: owner`, `authorization_status: AUTHORIZED`, a nonempty `decided_by` and `citation`, and the source id in `target_ids`. Exceptions that are missing, pending, or `NOT_AUTHORIZED` do not bypass the rule. The validator checks the record shape; it cannot authenticate the owner or prove the exception was genuinely granted.

This is a provenance boundary for public-release only. The default and `internal-candidate` profiles do not apply it. Internal research can retain private cross-repository provenance without falsely rewriting its origin, but it remains an internal candidate and is not release-ready.

## Record types

A research record is one assessment. Its JSON object and its `ledgers/research_ledger.csv` row carry the 22 Plan fields, plus `execution_outcome`, `simulation_link`, `programme_credit`, `clause_ids`, and `release_classification`. `pass_type` is `research`. `record_id` looks like `RES-001`. The research activity is not the simulation run. `raw_evidence_location` points at the simulation result file. `simulation_link` names the one case and the one result.

A simulation case, in `simulations/scenarios.json`, is the input and the expected outcome written before execution. It is not itself an execution record.

A simulation result is one simulation pass. It carries the 22 Plan fields plus the four Plan simulation-pass fields (`protocol_version`, `configuration`, `environment`, `execution_timestamp`, `failure_policy`, `known_answer_check`, `mcse_or_precision_note`), `execution_outcome`, and the execution fields: actual output, expectation flag, exit code, timestamps, environment description, and code and fixture hashes. `pass_type` is `executed_simulation`. `record_id` looks like `SIM-001` and matches the case id. The runner records `authorization_status` as `NOT_AUTHORIZED`.

`execution_timestamp` is ISO 8601 with an explicit numeric offset or `Z`; a naive timestamp is refused, and when `started_at` and `ended_at` are also present the validator requires `execution_timestamp` to fall inside that closed interval. `started_at`, `ended_at`, `duration_seconds` and `exit_code` are extra execution detail. They do not replace `execution_timestamp`.

A requirement record resolves to exactly one research record and one declared clause reference. One research card has at most one requirement. `requirement_id` matches `ULC-<tablet>-<clause>`. The `classification` column on a requirement is its disposition, not its release classification.

A clause reference is an identifier. It has no clause title and no clause body. A placeholder must say that it is an example placeholder.

A source-register entry has a `review_scope`. When the source is a git object, the entry declares `repository`, a repository-relative `path`, `commit`, and `blob_sha` together. `commit` and `blob_sha` are 40-character hexadecimal SHAs. A commit from one repository must not be paired with a path that exists only in another. Sources that are not git objects omit those fields.

A decision file in `decisions/*.json` cites an owner or reviewer. An evidence decision sets `state` to one of `verified`, `independently_reproduced`, `validated`, `authorized`. An authorization record sets `authorization_status` to `AUTHORIZED`. One file may do both only when both fields are written. An evidence `state` does not authorize by itself, and a decision whose `state` is `authorized` does not authorize anything unless it also sets the authorization column.

Programme status holds counts and claims. `evidence_status`, `execution_outcome` and `authorization_status` are all present and all separate. Counts that are zero stay zero. `owner_acceptance` stays `PENDING` until a decision cites the programme. `production_validation` stays `NOT_PERFORMED` unless a decision records it, and even then the scaffold does not define a certified or production-ready value.

## Evidence ladder

The ladder is the governing Plan's eight evidence states, in Plan order, as snake_case
slugs:

`proposed`, `documented`, `implemented`, `tested`, `verified`, `independently_reproduced`,
`validated`, `authorized`.

A state records how far the evidence for a claim has been established. It does not record
what a run did; that is `execution_outcome` (see below).

Tooling may set only `proposed`, `documented`, `implemented` and `tested`. The edges are
forward only, one step at a time:

- `proposed` → `documented`
- `documented` → `implemented`
- `implemented` → `tested`
- `tested` → `verified` only with a decision record
- `verified` → `independently_reproduced` only with a decision record
- `independently_reproduced` → `validated` only with a decision record
- `validated` → `authorized` only with a decision record

There is no demotion edge. A later state never rewrites an earlier one, so a record that
reached `tested` cannot be moved back to `implemented`. If a run turns out to have been
flawed, record that as a new record and an open obligation, not by lowering the state of
the existing one.

`verified`, `independently_reproduced`, `validated` and `authorized` are refused to tooling
even when a decision record is supplied through the wrong route. They are entered through
`transition` in `tools/evidence_states.py`, which requires an owner or reviewer decision
that cites the target id.

## Execution outcomes

`not_executed`, `executed`, `failed`, `incomplete`. Default `not_executed`.

This is a separate axis. It records what the run actually did. It is **not** an evidence
state, and the validator refuses a value from one vocabulary on the other's field in both
directions. A run that failed is not thereby un-evidenced: a failed run can legitimately sit
at `evidence_status: documented`, because what is documented is that the run failed.

The validator also refuses `execution_outcome: executed` when the result carries no
execution evidence: for a simulation, no `exit_code`, no `code_sha256`, or no
`raw_evidence_location`.

`evidence_status: authorized` does not set and does not imply `authorization_status:
AUTHORIZED`. `authorization_status` is not a step on this ladder or on the evidence ladder.
Its default is `NOT_AUTHORIZED`. `AUTHORIZED` requires a decision whose own
`authorization_status` is `AUTHORIZED` and which cites the target. Programme credit
`AWARDED` likewise requires a decision that sets `programme_credit` to `AWARDED`. Candidate
credit (`CANDIDATE_PENDING_OWNER_REVIEW`) is not an award.

## Invariants the validator checks

1. **Manifest integrity.** Every package file except the manifest is listed with a matching SHA-256. The manifest has no extra path and no absolute path.
2. **Traceability.** Identifiers are unique across record types. Each research record links to exactly one simulation case and one simulation result, and each of those links back. Each requirement resolves to an existing research record and a declared clause reference, and each research card has at most one requirement. Result paths exist.
3. **Execution evidence.** Each result has an integer exit code that matches `results/execution_log.json`, timestamps with timezones, an environment description, a code hash that matches `code_path`, and a fixture hash field. The log carries stdout and stderr. Each result also carries the four Plan simulation-pass fields: a zoned `execution_timestamp` inside the recorded start and end, a non-empty `failure_policy`, a `known_answer_check` whose `detail` explains an absent known-answer case, and a non-empty `mcse_or_precision_note`. A result claiming `execution_outcome: executed` must carry its exit code, code hash and raw evidence location. The validator does not re-run the case.
4. **Expectation discipline.** The expected outcome stored on the result equals the expected outcome in `simulations/scenarios.json`. The result's `fixtures_sha256` matches the current bytes of that case file.
5. **Count arithmetic.** Status totals match the records and the ledgers. Checkpoint recorded counts match the records that name that checkpoint. A simulation id appears at most once in each coverage ledger (reports, dimensions, levels, phases, relationships). Coverage across those ledgers does not multiply the status totals.
6. **Honest status and axis separation.** The status object and the records do not claim an evidence state above `tested`, programme credit, production validation, or authorization without a matching decision record. `authorization_status` other than `NOT_AUTHORIZED` fails when no authorization record cites that target, and it fails specifically when the record carries `evidence_status: authorized`, because an evidence state is not an authorization record. An `execution_outcome` value that is an evidence state, or an `evidence_status` value that is an execution outcome, is refused.
7. **Classification gate.** Every file and every record carries a release classification. The default and public-release profiles allow only `PUBLICLY_CLEARED`; the internal-candidate profile also allows `INTERNAL_CANDIDATE` but refuses packages located inside this public repository. A missing or malformed classification is an unclassified artefact. The public-release profile additionally requires a cited owner authorization and a complete, same-repository D09 source locator or a source-specific, authorized owner exception.

The validator exits `0` when all seven pass and `1` when any fail. A missing package directory exits `2`.

## What a passing validation proves

- The manifest matches the files that are present.
- Research, simulation, requirement, clause, and source links resolve, and identifiers are not duplicated.
- Result records contain execution fields, and the recorded code hash matches the named file.
- The recorded expected outcome matches the case file, and the case file still has the hash recorded at execution.
- Declared counts match the ledgers, and cases are not listed twice inside a coverage ledger.
- Claims of verification, reproduction, validation, programme credit, production validation and permission to proceed are backed by decision records whenever the honest value would otherwise be empty or pending.
- Evidence state and execution outcome are carried on their own fields, and neither appears where the other belongs.
- Every artefact meets the selected profile's classification gate. The internal-candidate profile never reports release readiness; the public-release profile also requires a cited owner authorization and refuses incomplete or cross-repository Git locators unless a source-specific, authorized owner exception is recorded.

## What a passing validation does not prove

- That any finding is true, or that an expected outcome was the right oracle.
- That the validator, or anyone else, re-executed the simulation. It reads the recorded exit code, timestamps, environment, and hashes.
- That a person reviewed, accepted, or authorized the work. A decision record of the required shape is a citation, not a check that the cited person exists.
- That `evidence_status` of `validated` or `authorized` authorizes anything. Authorization is only `authorization_status`, and an evidence `authorized` is not an authorization.
- That a run succeeded because `evidence_status` is high, or that its evidence is weak because `execution_outcome` is `failed`. The two axes are independent.
- Scientific validation, security certification, production readiness, a judgement that the implementation is acceptable, or leave to release.
- That a clause identifier matches private corpus text. The corpus is outside the package.
- Programme credit. The validator never grants it. `CANDIDATE_PENDING_OWNER_REVIEW` means the credit is not awarded.

## Generalisation notes

An earlier package used evidence-ledger headers such as `id`, `question`, `method`, `finding`, and `status`, and it hardcoded record counts, report counts, and framework-ledger sizes. Those counts are facts of that package, not invariants. This scaffold reconciles whatever totals the package declares. It also does not require a reading PDF. The case-file hash is the hash of `simulations/scenarios.json`, and the code hash is the hash of the result's `code_path`, rather than one fixed model filename. A recorded `FAIL` or `ERROR` can still be real execution evidence: it is an `execution_outcome`, not an `evidence_status`. Matching an expectation is not programme credit.
