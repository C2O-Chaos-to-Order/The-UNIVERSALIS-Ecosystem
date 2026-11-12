# Love and Care Contract Validation

**Inventory:** 26th owner-supplied inventory  
**Status:** Source committed; validator execution pending. No passing test claim is made.

## Shared artifacts
- LOVE_CARE_ARCHITECTURE.md
- schemas/love-care/love-care-contracts.v1.schema.json
- examples/love-care/love-care-fixtures.v1.json
- .github/scripts/love_care_contract.py

The portable contract has six record families: love-anchor, conditional reciprocity, empathy evaluation, care continuity, non-instrumentality attestation and evidence receipt. All records state authority_effect = none.

The standard-library validator defines 15 negative semantic cases, including subjective-love claims, engagement/payment-conditioned care, asymmetric or coercive exit terms, invalid Synthesis checker semantics, identity-continuity overclaims, unsupported non-instrumentality verdicts and unverified signature claims.

Run from repository root:

    python .github/scripts/love_care_contract.py --fixture examples/love-care/love-care-fixtures.v1.json

Preserve stdout/stderr, Python version, commit SHA and file digests. No GitHub Actions workflow is added or dispatched.

A passing fixture check validates only authored synthetic records. It does not prove sincerity, felt love, identity continuity, relationship authenticity, therapeutic effectiveness, consent or overall safety.

## C2O-only authorization

The C2O private authorization schema, denied fixture and authorization validator are maintained only in the private C2O Ecosystem repository. Its validator uses an otherwise-authorizable synthetic positive-control request followed by independent negative mutations. Execution remains pending.
