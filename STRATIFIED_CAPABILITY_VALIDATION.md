# UNIVERSALIS Eight-Stratum Capability — local validation

**Runtime:** Python 3.13.5; jsonschema 4.26.0; cryptography 46.0.4.  
**Mode:** local execution only; no GitHub Actions workflow added or dispatched.

Run from the repository root:

    python -m pip install 'jsonschema>=4.23,<5' 'cryptography>=44,<47'
    python .github/scripts/stratified_capability_contract.py

## Results

- PASS — Draft 2020-12 schema validation.
- PASS — 21 synthetic records across 14 record collections.
- PASS — canonical eight-stratum order and all eight principle entries.
- PASS — MCP / A2A / ACP semantic distinction.
- PASS — Ed25519 composition receipt, key identity and signed-body digest.
- PASS — external model route requires explicit egress approval.
- PASS — public application publication requires human approval reference.
- PASS — remote QPU submission requires human approval, emulation evidence, shot/cost quote and job reference.
- PASS — simulation-only robot evaluation cannot authorize actuation or overclaim real-world safety.
- PASS — air-gap/compliance assertions require independent evidence and do not self-certify.
- PASS — 20 negative tests rejected protocol confusion, digest/signature tampering, license omission, unchecked external egress, publication/QPU/robotics overreach, invalid sovereignty claims and evidence inflation.

## Limits

The fixture and validator are synthetic. No third-party tools were installed or executed, no live ACP/A2A/MCP interop test was performed, no frontier model was downloaded, no QPU was submitted, no application was published, no robot was actuated and no sovereign deployment was independently audited. These checks validate only the contract semantics and synthetic evidence. They do not establish external product behavior, quality, safety or legal compliance.