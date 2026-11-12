# Convergence Contract Validation

**Date:** 2026-11-12  
**Scope:** Synthetic contract and cryptographic-fixture validation only.

## Implemented checks

- JSON Schema Draft 2020-12 validation for seven portable record types.
- Shared-intent participant coverage, unique term definitions and locked-state completeness.
- Consensus certificate satisfaction-bar consistency and preservation of no-agreement outcomes.
- Negotiation move ordering, party identity, unanimous acceptance and independently checked BATNA claims.
- Merge-plan operation uniqueness, review approval, conflict closure and target-digest freshness before application.
- Ontology-alignment reviewer, evidence and round-trip requirements; no invented target for an unmapped concept.
- Argumentation graph reference integrity and declared attack-confidence threshold.
- Dispute allocation arithmetic and prohibition on portable receipts granting enforcement authority.
- DSSE PAE construction, in-toto Statement subject digest binding, Ed25519 key-ID validation and signature verification.

## Fixture inventory

Seven synthetic convergence records cover shared intent, consensus, negotiation, merge planning, ontology alignment, argumentation and dispute outcome. One DSSE bundle binds the consensus certificate digest. The fixture private key is not included; the embedded public key is disposable and is not a production trust anchor.

## Negative tests

Fourteen negative tests reject:
1. a converged outcome with a participant below its satisfaction bar;
2. a score below its declared bar;
3. a locked intent omitting a participant's reading;
4. duplicate term definitions;
5. agreement without every party's acceptance;
6. a BATNA-safe claim with an unverified party;
7. merge application without approval;
8. merge application with an open conflict;
9. merge application against a stale target digest;
10. accepted ontology alignment without an independent reviewer;
11. accepted alignment without passing round-trip validation;
12. settlement allocations not totaling 100%;
13. a portable dispute record claiming enforcement authority;
14. a tampered DSSE signature.

## C2O-private authorization checks

The C2O workflow additionally validates a separate private authorization schema and synthetic fixtures. High-consequence merge, ontology-commit and dispute-enforcement operations require an approved human permit distinct from the initiating agent. Denials cannot be marked as executed. These private artifacts are not present in UNIVERSALIS.

## Limits

A passing CI run validates only the records and synthetic assertions in this repository. It does not establish the correctness of a negotiated answer, legal capacity, fairness, truth of evidence, Pareto optimality, real-world principal identity, production key custody, or actual tool interoperability. No actual merge, ontology commit, settlement or dispute enforcement occurred.
