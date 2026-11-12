# Insurgence Contract Validation — UNIVERSALIS

**Date:** 2026-11-12  
**Branch:** implementation/repository-foundation-2026-11-12

## Shared contract files
- schemas/insurgence/insurgence-contracts.v1.schema.json
- examples/insurgence/insurgence-fixtures.v1.json
- .github/scripts/insurgence_contract.py
- .github/workflows/insurgence-contract.yml

## Fixture coverage
One threat model with three evidence tiers, one resistance attestation, one containment receipt, one seven-stage fact-grounded nonviolent campaign plan, and three cryptographically signed in-toto/DSSE attestations. Twelve negative tests cover evidence tier/source quality, campaign non-deception/nonviolence, resistance pass criteria, independent stop-path/human command, containment chronology/agent non-override, DSSE payload integrity and signature validity.

The test validator binds each receipt to the canonical record digest, checks exact DSSE payload bytes, verifies Ed25519 signatures using the fixture-only public key, and checks the verifier identity and chronology.

## Public boundary
All references are synthetic or public citations. No C2O private baselines, incident data, identities, policy bodies, private keys, human permits, authority tokens, operational containment telemetry or deployment secrets are included. The fixture key is deliberately not a production trust anchor.

## Limitations
Passing CI establishes only that these synthetic contracts and tests behave as expected. It does not demonstrate that a third-party tool is safe, that an agent is resistant under all conditions, that containment is universal, that hardware watchdogs are present, or that a signed attestation is compliance certification. No tool, simulator, campaign or production containment action was executed.
