# Plan schema conformance

The evidence-record contract is the governing Plan's field list. A structural package can
keep research cards, simulation cases, execution logs, and ledgers apart, and still use
different column names. This scaffold does not. The columns below use the Plan names.

Three fields describe three different things and are never collapsed:
`evidence_status` (how far the evidence is established), `execution_outcome` (what the run
did), and `authorization_status` (whether anyone authorized it). None is derived from
another.

Requirement identifiers in this scaffold use `ULC-<tablet>-<clause>` (shape examples:
`ULC-18-10`, `ULC-00-01`, `ULC-26-05`). `ULC-00-01` in the templates is an example
placeholder, not a registered clause. Those ids are not the separate collection-level
register `UNI-001`…`UNI-015`.

## The 22 Plan fields

Governed by `The C2O Research Plan/Working Research Framework/Evidence_Record_Schema.md`,
minimum-fields table. Field names match exactly; no Plan field is renamed, dropped, or
added to this set.

| # | Plan field | Column here | Where it is carried | Required |
| --- | --- | --- | --- | --- |
| 1 | record_id | record_id | Research record, simulation result, both evidence ledgers | Required |
| 2 | programme_unit_id | programme_unit_id | Research record, simulation result, both evidence ledgers | Required |
| 3 | pass_type | pass_type | Research record (`research`), simulation result (`executed_simulation`), both evidence ledgers | Required |
| 4 | checkpoint_id | checkpoint_id | Research record, simulation result, both evidence ledgers | Required |
| 5 | objective_question | objective_question | Research record, simulation result, both evidence ledgers | Required |
| 6 | claim_class | claim_class | Research record, simulation result, both evidence ledgers | Required |
| 7 | relevant_dimensions | relevant_dimensions | Research record, simulation result, both evidence ledgers | Required column; may be empty when none apply |
| 8 | phase | phase | Research record, simulation result, both evidence ledgers | Required |
| 9 | level | level | Research record, simulation result, both evidence ledgers | Required |
| 10 | method_summary | method_summary | Research record, simulation result, both evidence ledgers | Required |
| 11 | sources_or_inputs | sources_or_inputs | Research record, simulation result, both evidence ledgers | Required |
| 12 | assumptions | assumptions | Research record, simulation result, both evidence ledgers | Required |
| 13 | acceptance_or_falsification_criteria | acceptance_or_falsification_criteria | Research record, simulation result, both evidence ledgers | Required |
| 14 | actual_conditions | actual_conditions | Research record, simulation result, both evidence ledgers | Required |
| 15 | outcome_summary | outcome_summary | Research record, simulation result, both evidence ledgers | Required |
| 16 | raw_evidence_location | raw_evidence_location | Research record, simulation result, both evidence ledgers | Required |
| 17 | uncertainty_and_limitations | uncertainty_and_limitations | Research record, simulation result, both evidence ledgers | Required |
| 18 | review_note | review_note | Research record, simulation result, both evidence ledgers | Required |
| 19 | evidence_status | evidence_status | Research record, simulation result, both evidence ledgers, programme status | Required. Values are the Plan's eight evidence states (Plan §7). Not an authorization. Not an execution outcome. |
| 20 | authorization_status | authorization_status | Research record, simulation result, both evidence ledgers, requirement records, programme status | Required. Default `NOT_AUTHORIZED`. `AUTHORIZED` only with an authorization record. Never inferred from `evidence_status`, including `evidence_status: authorized`. |
| 21 | regression_links | regression_links | Research record, simulation result, both evidence ledgers | Required column; may be empty when none apply |
| 22 | open_obligations | open_obligations | Research record, simulation result, both evidence ledgers | Required column; may be empty when none apply |

JSON Schemas: `schemas/research_record.schema.json` and
`schemas/simulation_result.schema.json`. Ledger headers:
`templates/programme/ledgers/research_ledger.csv` and
`templates/programme/ledgers/simulation_ledger.csv`.

## Plan simulation-pass fields

From the same source, the "Additional fields for executed simulation passes" table. These
are additional to the 22 fields and are not research-record columns.

| # | Plan field | Column here | Carried by | Required |
| --- | --- | --- | --- | --- |
| S1 | protocol_version | protocol_version | Result JSON; simulation ledger | Required on every simulation pass |
| S2 | configuration | configuration | Result JSON; simulation ledger | Required on every simulation pass |
| S3 | environment | environment | Result JSON object with `python` and `platform`; ledger cell rendered `python=<...>;platform=<...>` | Required on every simulation pass |
| S4 | execution_timestamp | execution_timestamp | Result JSON; simulation ledger | Required. ISO 8601 with an explicit numeric offset or `Z`. Naive timestamps refused. Must fall inside `started_at`..`ended_at` when both are present. |
| S5 | failure_policy | failure_policy | Result JSON; simulation ledger | Required. Non-empty: what is recorded on a crash or non-convergence. |
| S6 | known_answer_check | known_answer_check | Result JSON object `{included, case_id, detail}`; ledger cell as compact JSON | Required. When `included` is false, `detail` must say why no known-answer or negative-control case applies. When true, `case_id` must be non-empty. |
| S7 | mcse_or_precision_note | mcse_or_precision_note | Result JSON; simulation ledger | Required. Non-empty. A deterministic or single-run model must say so explicitly. |

`started_at`, `ended_at`, `duration_seconds` and `exit_code` remain on the result as extra
execution detail. They do not replace `execution_timestamp`.

## Plan status vocabulary

Plan §7 ("Evidence and status language") lists the states that must be kept distinct:
proposed, documented, implemented, tested, verified, independently reproduced, validated,
and authorized. These eight, as snake_case slugs in that order, are `evidence_status`:

`proposed`, `documented`, `implemented`, `tested`, `verified`, `independently_reproduced`,
`validated`, `authorized`.

Plan §13.6 uses a different and longer set for general status reporting: proposed, scoped,
researched, audited, executed, reproduced, verified, independently reviewed, validated,
owner-accepted, authorized, implemented, monitored, closed. **That set is not the
evidence-record ladder and is not imported into `evidence_status`.** The two lists overlap
by name only in a few places, and the §7 list governs a record.

## Execution outcomes are not evidence states

`execution_outcome` carries `not_executed`, `executed`, `failed`, `incomplete`. It answers
what the run did. It is not on the evidence ladder and is never read as though it were.

This separation is why `failed` and `incomplete` left `evidence_status` entirely when the
vocabulary was reconciled. A failed run is recorded with `execution_outcome: failed` and an
`evidence_status` that reflects what the record actually establishes — commonly
`documented`, because what is documented is that the run failed.

## Columns that are not Plan fields

The package carries discipline columns so a file is not mistaken for a result:
`execution_outcome` (see above), `simulation_link`, `programme_credit`, `clause_ids`,
`release_classification`, and the execution columns on the simulation ledger (`exit_code`,
timestamps, code and fixture hashes, and the captured outcome). Those columns do not rename
or replace the 22 Plan fields.
