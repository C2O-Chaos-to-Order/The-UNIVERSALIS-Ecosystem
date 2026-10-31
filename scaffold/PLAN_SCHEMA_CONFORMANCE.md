# Plan schema conformance

The evidence-record contract is the governing Plan's field list. A structural package can keep research cards, simulation cases, execution logs, and ledgers apart, and still use different column names. This scaffold does not. The columns below use the Plan names. `evidence_status` and `authorization_status` are both required, and neither is derived from the other.

Requirement identifiers in this scaffold use `ULC-<tablet>-<clause>` (shape examples: `ULC-18-10`, `ULC-00-01`, `ULC-26-05`). `ULC-00-01` in the templates is an example placeholder, not a registered clause. Those ids are not the separate collection-level register `UNI-001`…`UNI-015`.

## The 22 Plan fields

| Plan field | Column in this schema | Where it is carried | Required |
| --- | --- | --- | --- |
| record_id | record_id | Research record, simulation result, both evidence ledgers | Required |
| programme_unit_id | programme_unit_id | Research record, simulation result, both evidence ledgers | Required |
| pass_type | pass_type | Research record (`research`), simulation result (`simulation`), both evidence ledgers | Required |
| checkpoint_id | checkpoint_id | Research record, simulation result, both evidence ledgers | Required |
| objective_question | objective_question | Research record, simulation result, both evidence ledgers | Required |
| claim_class | claim_class | Research record, simulation result, both evidence ledgers | Required |
| relevant_dimensions | relevant_dimensions | Research record, simulation result, both evidence ledgers | Required column; may be empty when none apply |
| phase | phase | Research record, simulation result, both evidence ledgers | Required |
| level | level | Research record, simulation result, both evidence ledgers | Required |
| method_summary | method_summary | Research record, simulation result, both evidence ledgers | Required |
| sources_or_inputs | sources_or_inputs | Research record, simulation result, both evidence ledgers | Required |
| assumptions | assumptions | Research record, simulation result, both evidence ledgers | Required |
| acceptance_or_falsification_criteria | acceptance_or_falsification_criteria | Research record, simulation result, both evidence ledgers | Required |
| actual_conditions | actual_conditions | Research record, simulation result, both evidence ledgers | Required |
| outcome_summary | outcome_summary | Research record, simulation result, both evidence ledgers | Required |
| raw_evidence_location | raw_evidence_location | Research record, simulation result, both evidence ledgers | Required |
| uncertainty_and_limitations | uncertainty_and_limitations | Research record, simulation result, both evidence ledgers | Required |
| review_note | review_note | Research record, simulation result, both evidence ledgers | Required |
| evidence_status | evidence_status | Research record, simulation result, both evidence ledgers, and the programme-status object | Required. Values are the evidence ladder. Not an authorization. |
| authorization_status | authorization_status | Research record, simulation result, both evidence ledgers, requirement records, and the programme-status object | Required. Default `NOT_AUTHORIZED`. `AUTHORIZED` only with an authorization record. Never inferred from `evidence_status`. |
| regression_links | regression_links | Research record, simulation result, both evidence ledgers | Required column; may be empty when none apply |
| open_obligations | open_obligations | Research record, simulation result, both evidence ledgers | Required column; may be empty when none apply |

JSON Schemas: `schemas/research_record.schema.json` and `schemas/simulation_result.schema.json`. Ledger headers: `templates/programme/ledgers/research_ledger.csv` and `templates/programme/ledgers/simulation_ledger.csv`.

## Simulation-pass fields

These are added for a simulation pass. They are not research-record columns.

| Plan field | Column in this schema | Where it is carried | Required |
| --- | --- | --- | --- |
| protocol_version | protocol_version | Simulation result and simulation ledger | Required on a simulation pass. Not a research-record column. |
| configuration | configuration | Simulation result and simulation ledger | Required on a simulation pass. Not a research-record column. |
| environment | environment | Simulation result JSON object with `python` and `platform`. Simulation ledger column rendered as `python=<...>;platform=<...>`. | Required on a simulation pass. Not a research-record column. |

## Columns that are not Plan fields

The package also carries discipline columns so a file is not mistaken for a result: `simulation_link`, `programme_credit`, `clause_ids`, `release_classification`, and the execution columns on the simulation ledger (`exit_code`, timestamps, code and fixture hashes, and the captured outcome). Those columns do not rename or replace the 22 Plan fields.
