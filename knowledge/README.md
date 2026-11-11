# Knowledge records

Status: LIMITED

This package stores a corpus-agnostic `knowledge_record` schema, a fail-closed
stdlib validator, and synthetic example records. It is not scientific
validation, an authorized release, or a completed product.

- Schema: [`schemas/knowledge-record.schema.json`](schemas/knowledge-record.schema.json)
- Validator: `python -m knowledge.validate`
- Tests: `python -m unittest discover -s knowledge/tests -t . -v`
- Example records: [`records/`](records/) (`KNOW-0001` provenance, `KNOW-0002` clarity, `KNOW-0003` recovery)
- Synthetic sources: [`fixtures/`](fixtures/)
- Rule 1: [`../foundation/README.md`](../foundation/README.md)

Knowledge, interpretation, requirements, tests, evidence, limitations,
`review_status`, authorization, and `claim_class` are separate fields.
Interpretation status is `proposed`. `review_status` is `pending`. Authorization
defaults to `NOT_AUTHORIZED`. A record cannot be marked `accepted` without a
cited human decision record. Authorization cannot be inferred from a test pass.

A pass is not authorization.

Example requirement identifiers are `REQ-PROV-01`, `REQ-CLAR-01`, and
`REQ-RECOV-01`. They point at tests already present in this repository, plus the
knowledge-record tests in this package.

The validator applies Rule 1 recursively to itself. Publicly that is `tool-002`.
The same assessment is also stored in [`SELF_ASSESSMENT.json`](SELF_ASSESSMENT.json).

Authorization or permission growth cannot occur in the same change, whether or
not the capability set also grew, unless a cited human decision record is
present and the Rule 1 assessment is re-done. A record may not cite its own id
as that decision. The decision check does not verify signatures or authority. That rule enforces the companion working principle in
`foundation/ASCENDENCE_RESPONSIBILITY.md`. The principle is not part of the
RULE-1 digest and is not a Research Plan amendment. Mapping it onto the phase
axis (Ascendence → Transcendence) is an interpretation only.
