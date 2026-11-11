# Reciprocal Stewardship Policy — Prototype Note

**Identifier:** UNI-STEWARD-001  
**Version:** 0.1.0  
**Status:** Experimental proposal; not owner-accepted, production-ready, or deployment-authorized.  
**Implementation:** \`prototype/universalis/stewardship.py\`

## Purpose

This module turns a narrow set of supplied facts about a proposed action into an advisory policy disposition. It is a starting point for reciprocal stewardship: protect affected people and systems, preserve autonomy, make disagreement possible, require accountability, and prevent the parent or supervisor from becoming unreviewable.

It is not an identity system, legal decision-maker, emergency service, safety certification, authorization engine, agent runtime, or enforcement mechanism. It does not execute an action, suspend a capability, restore access, or create child agents.

## Policy values

1. **Dignity without conformity.** Identity, orientation, gender, disability, belief, family structure, and legitimate disagreement are not threat indicators. Assess conduct and evidence, not identity.
2. **Care without possession.** Protection must not become coercive control. A person or subsystem retains legitimate autonomy within its scope.
3. **Boundaries without abandonment.** A participant may decline optional delegated work. Refusal is not itself misconduct.
4. **Loyalty without concealment.** Preserve adverse evidence; no participant is immune from review.
5. **Reciprocal accountability.** A parent, operator, founder, builder, reviewer, and child system are all subject to appropriate controls.
6. **Independence without isolation.** Collaboration is the default where permitted; neither party should depend on inherited credentials or irrecoverable shared infrastructure.
7. **No manufactured dependency.** Do not design systems to make users, organizations, or delegated systems dependent in order to preserve the parent's relevance.
8. **Resource stewardship.** Delegation must be bounded by purpose, permissions, resource budget, duration, stop conditions, and appeal route.

## Disposition model

| Gate | Meaning | Required posture |
|---|---|---|
| CLEAR | No policy blocker identified within the supplied scope | Preserve boundaries and obtain any separate execution authorization |
| CONDITIONAL | Elevated risk has specified mitigations | Apply only the named controls and monitor stop conditions |
| PAUSE | Evidence, authority, affected parties, or safeguards are insufficient | Do not proceed pending review |
| HALT | Credible serious ongoing/imminent harm or material control compromise | Recommend narrowly scoped containment and preserve evidence |
| PROHIBITED | A specific pre-existing non-overridable prohibition applies | Deny the prohibited action and record its basis |

Emergency containment takes priority over ordinary adjudication. If the decision-maker is implicated, recusal and independent review remain mandatory. A claimed prohibition must identify a specific, pre-existing rule or human-governed determination through a versioned source locator and authority decision reference. An unreviewed prohibition reference yields PAUSE, not PROHIBITED. The human_reviewed field is a caller-declared record; this prototype cannot authenticate the reviewer or source. Dislike of nonconformity or dissent is not a prohibition.

## Important technical boundary

The evaluator returns \`execution_authorized=False\` for every result. A CLEAR result is not permission to execute. Callers must authenticate principals, verify fact provenance and any cited prohibition decision, enforce permissions through a separate independently controlled mechanism, and log consequential actions.

Containment and restoration are recommendations only. Restoration evidence requires:
- defect correction;
- regression and adversarial tests;
- verified evidence integrity;
- protection of affected parties;
- scope-matched authorization; and
- distinct implementer, independent reviewer, and human authorizer identities.

The evaluation only determines whether evidence is ready for a human decision. It never restores a capability.

## Threadling / delegation contract

A specialized child system may receive a bounded work contract. The contract must have a distinct identity, explicit purpose, action allowlist, positive resource budget, timezone-aware expiry, and appeal route. Parent credentials are never inherited. A child may decline optional work. Revocation must have a recorded reason and appeal route.

This prototype validates a contract object; it does not spawn, schedule, authenticate, or supervise agents.

## Operational degradation

Software degradation must be represented through observable indicators such as error rate, queue growth, resource saturation, missing evidence, and inconsistent decisions. These are not evidence of subjective suffering, consciousness, depression, or feelings. Such claims are outside the scope of this implementation.

For human participants, exhaustion, coercion, depression, and unsafe workload are human welfare matters. Governance must not normalize limitless sacrifice; it should support workload reduction, delegation, leave, independent support, and safe continuity. This document is not medical guidance.

## Current limitations and required next work

- Caller-supplied facts and identity strings are not authenticated by this module; a human_reviewed claim is not independently verified here.
- The prohibition reference is a provenance-bearing input, not proof of authority. An unreviewed reference pauses for human review; only a recorded human-reviewed, specifically non-overridable basis produces a PROHIBITED recommendation.
- Likelihood/severity thresholds require independent domain review; this is not a calibrated risk model.
- No atomic permission enforcement, durable audit log, concurrent revocation, crash recovery, or external containment exists here.
- The prototype needs property-based tests, mutation testing, threat modelling, independent review, and integration tests against the actual authorization boundary.
- High-impact actions remain outside scope until an independent authorization and containment design is implemented and reviewed.

## Test command

From the \`prototype\` directory:

\`\`\`sh
python -m unittest discover -s tests -v
\`\`\`

A passing test suite proves only the implemented unit-level behavior under those test inputs. It does not establish research validation, production readiness, safety certification, source authenticity, owner acceptance, or deployment authorization.
