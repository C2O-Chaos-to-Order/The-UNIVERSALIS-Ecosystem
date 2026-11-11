# Addendum 2026-11-10 — Rule 1 reason quality and permission growth

This note records two gaps found in the public Rule 1 implementation on
`feat/knowledge-records-v0.1` and the fixes that followed. It does not
rewrite earlier assessment text except to add structured citations to
the current working records so they continue to validate.

## Before (verified in source)

`check_rule_1_assessment()` accepted any non-empty string as a
`not-applicable-with-reason` reason. Placeholders such as `n/a`,
whitespace-only values after a later strip, missing evidence citations,
and identical reasons reused across protections were not rejected.

`check_capability_authorization_growth()` returned immediately when the
capability set did not grow. A permission-only increase or an
authorization-only increase therefore escaped that check. A tool could
also cite its own id as the human decision record.

Knowledge example records stored `"commit": "working-tree"` on synthetic
sources. That string is not a commit fingerprint.

## Fix

- `not-applicable-with-reason` now requires a reason of at least 40
  characters, rejects placeholders (`n/a`, `none`, `tbd`, and similar),
  rejects duplicate reasons on the same assessment, and requires a
  `reason_ref` whose id appears in the reason text and exists in the
  registry as an evidence record or as a cited human decision id.
- Authorization or permission growth now requires a cited human decision
  and a re-done Rule 1 assessment whether or not capabilities also grew.
  A record may not cite its own `id`, `record_id`, or `name` as that
  decision.
- Synthetic knowledge source `commit` fields now use the real commit
  that introduced those fixtures,
  `6269294d73ebf2e599fbc8c85e8d5020b042da81`. The string `working-tree`
  is rejected as a commit.

The checker still cannot judge whether a written reason is true. The
human-decision check still does not verify a signature or that the cited
party had authority. Those limits are documented in
`foundation/README.md`.

## Local mutation checks (not committed)

On 2026-11-10, using Python 3.14.10:

1. The structured-reason call in `check_rule_1_assessment()` was replaced
   with the old non-empty-string check. Result: 3 failed
   (`test_placeholder_and_empty_na_reasons_are_rejected`,
   `test_duplicate_na_reasons_are_rejected`,
   `test_na_reason_without_existing_evidence_ref_is_rejected`). Exit 1.
   The file was restored.
2. The original `if not capability_set_grew(...): return []` early return
   was reinserted. Result: 6 failed (permission-only, authorization-only,
   and self-authorization tests in knowledge records and the registry).
   Exit 1. The file was restored.

## Known gaps that remain

- A well-formed reason is not checked for truth.
- A cited human decision id is not signature-checked and is not checked
  for authority.
- Enforcing these record checks does not prove a tool can never cause
  harm.
