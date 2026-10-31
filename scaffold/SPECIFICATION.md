# Programme package contract

This document is the contract for one programme package. The scaffold checks whether a package obeys the contract. A passing check is a statement about records, hashes, and claims inside that package. It is not a research finding, a scientific validation, a security certification, a production validation, or a release authorization.

Clause text stays outside this repository. A package may cite a clause by identifier only. Requirement ids use the form `ULC-<tablet>-<clause>`. Shape examples are `ULC-18-10`, `ULC-00-01`, and `ULC-26-05`. `ULC-00-01` in the templates is an example placeholder, not a corpus clause. These ids are not the separate collection-level register `UNI-001`…`UNI-015`.

The evidence-record field names are the governing Plan's names. See [PLAN_SCHEMA_CONFORMANCE.md](PLAN_SCHEMA_CONFORMANCE.md). `evidence_status` and `authorization_status` are separate columns. `authorization_status` defaults to `NOT_AUTHORIZED`. Nothing in the tooling copies `evidence_status` into `authorization_status`.

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

`metadata/classifications.json` maps every file, including the manifest, to a release classification. The only value this package may contain is `PUBLICLY_CLEARED`.

## Record types

A research record is one assessment. Its JSON object and its `ledgers/research_ledger.csv` row carry the 22 Plan fields, plus `simulation_link`, `programme_credit`, `clause_ids`, and `release_classification`. `pass_type` is `research`. `record_id` looks like `RES-001`. The research activity is not the simulation run. `raw_evidence_location` points at the simulation result file. `simulation_link` names the one case and the one result.

A simulation case, in `simulations/scenarios.json`, is the input and the expected outcome written before execution. It is not itself an execution record.

A simulation result is one executed pass. It carries the 22 Plan fields plus `protocol_version`, `configuration`, and `environment`, and the execution fields: actual output, expectation flag, exit code, timestamps, environment description, and code and fixture hashes. `pass_type` is `simulation`. `record_id` looks like `SIM-001` and matches the case id. The runner records `authorization_status` as `NOT_AUTHORIZED`.

A requirement record resolves to exactly one research record and one declared clause reference. One research card has at most one requirement. `requirement_id` matches `ULC-<tablet>-<clause>`. The `classification` column on a requirement is its disposition, not its release classification.

A clause reference is an identifier. It has no clause title and no clause body. A placeholder must say that it is an example placeholder.

A source-register entry has a `review_scope`. When `commit` or `blob_sha` is present, each is a 40-character hexadecimal SHA.

A decision file in `decisions/*.json` cites an owner or reviewer. An evidence decision sets `state` to `reviewed`, `accepted`, or `authorized`. An authorization record sets `authorization_status` to `AUTHORIZED`. One file may do both only when both fields are written. An evidence `state` does not authorize by itself.

Programme status holds counts and claims. `evidence_status` and `authorization_status` are both present. Counts that are zero stay zero. `owner_acceptance` stays `PENDING` until a decision cites the programme. `production_validation` stays `NOT_PERFORMED` unless a decision records it, and even then the scaffold does not define a certified or production-ready value.

## Evidence ladder

`planned`, `executed`, `failed`, `incomplete`, `reproduced`, `reviewed`, `accepted`, `authorized`.

Tooling may set only `planned`, `executed`, `failed`, `incomplete`, and `reproduced`. The legal edges are:

- `planned` → `executed`, `failed`, or `incomplete`
- `executed` → `reproduced`
- `failed` → `planned`
- `incomplete` → `planned` or `executed`
- `reproduced` → `reviewed` only with a decision record
- `reviewed` → `accepted` only with a decision record
- `accepted` → `authorized` only with a decision record

`authorization_status` is not a step on this ladder. Its default is `NOT_AUTHORIZED`. `AUTHORIZED` requires a decision whose own `authorization_status` is `AUTHORIZED` and which cites the target. Programme credit `AWARDED` likewise requires a decision that sets `programme_credit` to `AWARDED`. Candidate credit (`CANDIDATE_PENDING_OWNER_REVIEW`) is not an award.

## Invariants the validator checks

1. **Manifest integrity.** Every package file except the manifest is listed with a matching SHA-256. The manifest has no extra path and no absolute path.
2. **Traceability.** Identifiers are unique across record types. Each research record links to exactly one simulation case and one simulation result, and each of those links back. Each requirement resolves to an existing research record and a declared clause reference, and each research card has at most one requirement. Result paths exist.
3. **Execution evidence.** Each result has an integer exit code that matches `results/execution_log.json`, timestamps with timezones, an environment description, a code hash that matches `code_path`, and a fixture hash field. The log carries stdout and stderr. The validator does not re-run the case.
4. **Expectation discipline.** The expected outcome stored on the result equals the expected outcome in `simulations/scenarios.json`. The result's `fixtures_sha256` matches the current bytes of that case file.
5. **Count arithmetic.** Status totals match the records and the ledgers. Checkpoint recorded counts match the records that name that checkpoint. A simulation id appears at most once in each coverage ledger (reports, dimensions, levels, phases, relationships). Coverage across those ledgers does not multiply the status totals.
6. **Honest status.** The status object and the records do not claim acceptance, review, programme credit, production validation, or authorization without a matching decision record. `authorization_status` other than `NOT_AUTHORIZED` fails when no authorization record cites that target.
7. **Classification gate.** Every file and every record carries a release classification, and the only allowed value is `PUBLICLY_CLEARED`. A missing classification is an unclassified artefact.

The validator exits `0` when all seven pass and `1` when any fail. A missing package directory exits `2`.

## What a passing validation proves

- The manifest matches the files that are present.
- Research, simulation, requirement, clause, and source links resolve, and identifiers are not duplicated.
- Result records contain execution fields, and the recorded code hash matches the named file.
- The recorded expected outcome matches the case file, and the case file still has the hash recorded at execution.
- Declared counts match the ledgers, and cases are not listed twice inside a coverage ledger.
- Claims of review, acceptance, programme credit, production validation, and authorization are backed by decision records when they are not the honest empty or pending values.
- Every artefact in the package is marked `PUBLICLY_CLEARED`.

## What a passing validation does not prove

- That any finding is true, or that an expected outcome was the right oracle.
- That the validator, or anyone else, re-executed the simulation. It reads the recorded exit code, timestamps, environment, and hashes.
- That a person reviewed, accepted, or authorized the work. A decision record of the required shape is a citation, not a check that the cited person exists.
- That `evidence_status` of `accepted` or `authorized` authorizes anything. Authorization is only `authorization_status`.
- Scientific validation, security certification, production readiness, implementation acceptance, or permission to release.
- That a clause identifier matches private corpus text. The corpus is outside the package.
- Programme credit. The validator never grants it. `CANDIDATE_PENDING_OWNER_REVIEW` means the credit is not awarded.

## Generalisation notes

An earlier package used evidence-ledger headers such as `id`, `question`, `method`, `finding`, and `status`, and it hardcoded record counts, report counts, and framework-ledger sizes. Those counts are facts of that package, not invariants. This scaffold reconciles whatever totals the package declares. It also does not require a reading PDF. The case-file hash is the hash of `simulations/scenarios.json`, and the code hash is the hash of the result's `code_path`, rather than one fixed model filename. A recorded `FAIL` or `ERROR` can still be real execution evidence. Matching an expectation is not programme credit.
