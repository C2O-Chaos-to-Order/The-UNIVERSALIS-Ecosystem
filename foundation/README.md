# Foundation: Rule 1 and related working principles

This directory stores the Foundational Safety Invariant and one related working principle.

## What this is

Rule No. 1 is **Do No Harm. Do No Destruction.** It is stored as a single immutable, versioned invariant document:

- `foundation/RULE_1.md` — canonical human-readable text. The text between `RULE-1-CANONICAL-START` and `RULE-1-CANONICAL-END` is the hashed body.
- `foundation/rule_1.json` — machine-readable record with id `RULE-1` and `canonical_sha256` of that body.

Knowledge records and tool records reference Rule 1 by id `RULE-1` plus that digest. The validator fails closed if the reference is missing or the digest does not match.

This is an enforced, declared invariant with evidence. It does not prove that a tool can never cause harm.

## Related working principle

`foundation/ASCENDENCE_RESPONSIBILITY.md` (`WP-ASCENDENCE-01`) is referenced from `RULE_1.md` and listed under `related_working_principles` in `rule_1.json`. It is **not** part of the RULE-1 canonical text or digest. It is **not** a Research Plan amendment. Mapping it onto the existing phase axis (Ascendence → Transcendence) is an interpretation only.

The working principle is enforced by one update-path rule: if a tool record or knowledge record grows its capability set, its authorization or permissions must not grow in the same change unless a cited human decision record is present and the Rule 1 assessment is re-done. A capability increase alone never raises authorization.

## Where Rule 1 is enforced

- Canonical text is hashed. `foundation/rule_1.json` must carry the matching digest.
- Every knowledge record and tool record must cite `RULE-1` with that digest.
- Every knowledge record and tool record must carry a six-protection `rule_1_assessment`. Status `open` is treated as unaddressed and fails. `not-applicable-with-reason` requires a reason. `addressed` requires evidence locators.
- A proposed update that would change RULE-1 text or digest is rejected. The previous record (`K_n`) is kept.
- `review_status` of `accepted` requires a cited human decision record.
- Authorization cannot be inferred from a test pass. A pass is not authorization.
- Capability growth cannot raise authorization or permissions without a cited human decision and a re-done Rule 1 assessment.
- The knowledge validator applies these checks to itself (public `tool-002`, or the documented private equivalent in `knowledge/SELF_ASSESSMENT.json`).

## Where Rule 1 is not enforced

- These records do not prove that a tool, model, or operator cannot cause harm.
- They do not monitor runtime behavior outside the recorded artifacts.
- They do not replace law, independent review, or human judgment.
- They do not amend the Research Plan or rename its phases.
- They do not automatically stop physical, organizational, or downstream harm.
- They are not scientific validation of any tablet, tool, or claim.
- Measurement records and any Starlink adapter are out of scope for this step.
- Official integration matrices, where they exist, remain independently assessed and are not altered here.

Recursive application means the enforcing tools are checked against Rule 1 as well. That check is still a recorded assessment with evidence, not a proof of harmlessness.
