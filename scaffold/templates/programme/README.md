# {{PROGRAMME_ID}}

Edition {{EDITION}}. Empty programme package instantiated from the public scaffold.

## Status

Evidence status: proposed. Execution outcome: not_executed. Authorization status: NOT_AUTHORIZED. These are three separate fields. Authorization is not inferred from evidence, and an evidence_status of `authorized` does not set or imply authorization_status `AUTHORIZED`.

Owner acceptance: PENDING. Independent reviews: 0. Independent reproductions: 0. Owner-accepted research credits: 0. Owner-accepted simulation credits: 0. Production validation: NOT_PERFORMED. Release authorized: false.

Research records, simulation cases, simulation results, requirements, and reports are zero until they are actually added. A file in this package is not a result.

## What belongs here

- Research evidence records use the Plan field names in `research/research_records.json` and `ledgers/research_ledger.csv`.
- Simulation cases in `simulations/scenarios.json` state inputs and expected outcomes before execution.
- `simulations/run_one.py` runs one case in a subprocess and writes a simulation evidence record. It sets `authorization_status` to `NOT_AUTHORIZED` and does not award programme credit.
- Requirement ids use `ULC-<tablet>-<clause>`. An example placeholder is `ULC-00-01`. That placeholder is not a registered requirement in this empty package, and it is not an entry in the separate collection-level register.

## Limits

This README does not record a finding. It does not accept the programme, authorize release, or claim scientific validation, security certification, or production readiness.
