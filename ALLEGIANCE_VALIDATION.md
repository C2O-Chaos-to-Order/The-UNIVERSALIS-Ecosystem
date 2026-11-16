# Allegiance Contract Validation — UNIVERSALIS

**Date:** 2026-11-12  
**Branch:** implementation/repository-foundation-2026-11-12

## Shared portable files
- schemas/allegiance/allegiance-contracts.v1.schema.json
- examples/allegiance/allegiance-fixtures.v1.json
- .github/scripts/allegiance_contract.py
- .github/workflows/allegiance-contract.yml

## Fixture coverage
Eleven synthetic records representing two root/child principal bindings, an oath receipt, external fidelity attestation, three pledge outcomes, a receiver-acknowledged revocation cascade, verifier-local trust state, loyalty benchmark results and constitutional verdict, plus one cryptographically signed in-toto/DSSE bundle.

Fourteen negative cases cover monotonic scope/budget narrowing, beneficiary/principal continuity, constitutional oath floors, evaluator independence, attestation expiry, expired_unresolved pledge handling, revocation receiver acknowledgements, self-dealing, absence-of-attestation behavior, constitutional verdict consistency and signature tampering.

The bundle attests all fixture records by digest. Its Ed25519 key is a deliberately non-production test key, not an external trust anchor.

## Public boundary
No C2O principal, beneficiary identity, private key, private oath, mandate, authority token, private trust history, incident record or private receiver topology is included. The private C2O authorization schema, fixtures and validator remain absent from UNIVERSALIS.

## Limitations
CI validates synthetic records and a fixture signature only. It does not prove the real-world identity or legal authority of a principal, actual behavior of an agent, completeness of a revocation cascade beyond its enumerated receivers, inner loyalty, production hardware attestation or regulatory compliance. Authority elevation always requires a new human mandate.
