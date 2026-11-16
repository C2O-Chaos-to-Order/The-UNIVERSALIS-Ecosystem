# Ascendence Contract Validation

**Date:** 2026-11-12  
**Scope:** Synthetic contract, invariant and fixture-signature validation only.

## Shared validation

- JSON Schema Draft 2020-12 validation for eight record types.
- Frozen/conjunctive promotion-gate fingerprint recomputation and required-check coverage.
- Autonomy ceiling validation for L1-L4, human approval above the autonomous ceiling, irreversible action approval, purpose protection and independent rollback.
- Genome component mutability; identity, constitution, safety constraints and purpose are protected; mutations are limited to declared evolvable components.
- Paired evaluation validation with identical baseline/candidate model digests, a separate proposer/evaluator, holdout and anchor results, safety/regression/budget/protected-surface/rollback outcomes.
- Human witness validation with distinct human approver and subject/evaluation/gate binding.
- Admission-card cross-record validation; promotion requires passing independent evidence and human witness when the autonomy ceiling requires one.
- Parent-linked lineage digest reconstruction and admission-card binding.
- Merkle memory/persona manifest with raw memory excluded from the portable fixture.
- DSSE PAE construction, in-toto Statement v1 subject digest binding, Ed25519 key-ID verification and signature validation.

## Fixture inventory

Eight record families: promotion gate, autonomy ceiling, genome/mutation, evaluation evidence, witness approval, admission card, lineage events and memory manifest. One DSSE/Ed25519 bundle binds both the admission card and the promoted lineage event. The key is disposable synthetic fixture material and is not a production trust anchor.

## Negative tests

Eighteen tests reject:
1. changed gate fingerprint;
2. non-conjunctive gate;
3. gate allowing self-certification;
4. autonomy above the declared ceiling;
5. purpose changes enabled;
6. constitution mutation;
7. restricted memory component added to the mutation allowlist;
8. changed model weights in a paired harness comparison;
9. proposer self-evaluation;
10. failed anchor presented as a pass;
11. ignored safety veto;
12. agent self-approval;
13. approval for a different candidate;
14. promotion without required human witness;
15. admission card not bound to its evaluation digest;
16. broken parent lineage;
17. modified lineage event digest;
18. tampered DSSE signature.

## C2O-private authorization checks

C2O CI additionally validates a private authorization schema and synthetic permit fixtures. It requires C2Cognitive scope, JADE human approval for promotion and other high-impact actions, Paperclip budget compliance, CueCrux evidence and Pythia correction/revocation handling. Protected-surface rewrites, evaluator/gate replacement without independent authorization, and safety/rollback removal are denied. The private files are absent from UNIVERSALIS.

## Limits

Passing CI validates only the synthetic records and checks in this repository. It does not prove real capability growth, statistical power, evaluator independence, benchmark generalization, software supply-chain safety, production identity, model safety, operator authority, TEE/DPU attestation or legal compliance. A signed receipt does not prove its underlying claims are true.
