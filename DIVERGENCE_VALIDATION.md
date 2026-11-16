# Divergence Contract Validation — UNIVERSALIS

**Date:** 2026-11-12  
**Branch:** implementation/repository-foundation-2026-11-12

## Shared contract set
- schemas/divergence/divergence-contracts.v1.schema.json
- examples/divergence/divergence-fixtures.v1.json
- .github/scripts/divergence_contract.py
- .github/workflows/divergence-contract.yml

## Expected validation

Nine proposed behavioral-axis definitions, eight sanitized reports spanning behavior, configuration, schema, policy, semantics, identity/federation, embedding/RAG and resolution, and one DSSE Ed25519 attribution receipt are validated. Twelve negative tests cover normalized ranges, axis references, confidence intervals, report status, identity quorum/claim quality, report-digest binding, canonical payload equality, signature integrity and key/timestamp consistency.

## Public boundary

All identities and references are synthetic opaque values. The shared fixture contains no C2O private baselines, traces, incidents, cloud account IDs, private policy clauses, registry keys, production signer identities, authority tokens, permits or deployment secrets. The fixture public key is test-only and is not a production trust anchor.

## Limitations

CI validates portable synthetic contracts and a test signature. It is not a production attestation service, baseline store, identity resolver, SIEM, drift engine or remediation authority. No live product, baseline, trace, database, cloud configuration, ontology, policy or vector index is accessed. Product claims require separate source/version/license/deployment review and independent testing.
