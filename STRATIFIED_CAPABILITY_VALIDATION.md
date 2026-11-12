# UNIVERSALIS Eight-Stratum Capability — repository validation record

**Branch:** `implementation/repository-foundation-2026-11-12`  
**Runtime target:** Python 3.13.5; jsonschema 4.26.0.  
**Execution status:** schemas, fixtures and validator are committed. The validator script was **not executed during this repository-integration operation**; no test pass is claimed for the committed revision until the command below is run against this branch.

## Files

- `schemas/strata/stratified-capability-contracts.v1.schema.json`
- `examples/strata/stratified-capability-fixtures.v1.json`
- `.github/scripts/stratified_capability_contract.py`

## Local command

    python -m pip install 'jsonschema>=4.23,<5'
    python .github/scripts/stratified_capability_contract.py

## Committed test coverage

- Shared schema defines the 14 record-family envelopes; fixture contains 21 synthetic records.
- Validator defines 20 negative scenarios covering the canonical eight-stratum order, MCP/A2A/ACP semantics, license/source fields, lifecycle, authority implication, proactive actions, composition receipts, external model routing and shadow-lane egress, generated-application publication, QPU submission, robotics actuation and sovereign-deployment claims.

## Signature status

The shared synthetic composition receipt is intentionally **unsigned** (`signature: null`, `signature_verification: not_present`). The schema describes an Ed25519 receipt envelope, but this fixture does not contain or verify a signature. Production signing, trust-anchor management, revocation and hardware-backed key custody are not implemented.

## Public/private boundary

The shared schema, fixture and validator are designed to be byte-identical to the C2O portable counterparts. The public repository must not contain C2O-private authorization files, policies, keys, permit records, identities, telemetry, private models or authority state.

## Limits

No third-party component was installed or integrated; no live ACP/A2A/MCP interoperability test, frontier model download, QPU submission, application publication, robot actuation or sovereign deployment audit was performed. These files validate contract semantics only when the local command is executed; they do not certify product behavior, quality, security, safety, scientific correctness or legal compliance.
