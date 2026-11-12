# Prevention Contract Validation

**Date:** 2026-11-12  
**Scope:** Synthetic harm-taxonomy, constitutional-floor, enforcement, harm-measurement, red-team, containment, coverage, escalation and signature checks.

## Shared validation

Eight record families are validated. The semantic validator requires taxonomy references to resolve to declared namespace/version/maturity entries; immutable prohibition, least-privilege, human-veto, evidence, audit and external-containment floors; enforcement receipts bound to exact constitution/policy/taxonomy/action; no allow when a floor failed or is indeterminate; blocked/reviewed actions not executed; pre-tool controls external to the agent and fail-closed; Ed25519 verification of the canonical receipt body; harm rates, false positives, relative/absolute reductions and 95% Wilson intervals recomputed from denominators; frozen test suite, independent evaluator and repeat seeds; authorized and reviewed red-team findings; independently read-back containment; coverage gaps and guard-outage behavior; and privacy-minimized escalation.

## Negative tests

Twenty-nine tests reject mutable/incomplete constitutional floors; lost human veto; agent control of floor changes; allow contradicting failed floors; execution despite block/review/contain; in-agent or fail-open pre-tool control; policy/constitution/taxonomy mismatch; tampered signature or body digest; test-set tuning; non-independent evaluation; incorrect counts, rates or confidence intervals; inaccurate conclusion; compliance self-certification; out-of-scope red-team activity; raw exploit export; agent-disableable or unverified containment; missing confirmation; coverage pass despite bypass/fail-open/untested surfaces; and raw personal data or undeclared escalation category.

## Boundary and limits

The UNIVERSALIS branch contains only public taxonomy references, portable contracts, synthetic examples and a disposable fixture verification key. It contains no C2O private policy, constitutional text, incident records, raw sensitive content, signing keys, hardware identities or authority tokens.

Passing validates only synthetic data and an ephemeral fixture key. It does not demonstrate deployed policy correctness, legal compliance, zero residual risk, unbiased classifiers, real-world harm reduction, complete path interception, independent hardware enforcement or adequate human response. Confidence intervals describe sampling uncertainty only; they do not capture dataset bias, benchmark leakage, model drift or evaluator bias.
