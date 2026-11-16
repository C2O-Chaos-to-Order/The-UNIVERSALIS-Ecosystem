# UNIVERSALIS Simulation local validation

**Runtime:** Python 3.13.5; jsonschema 4.26.0; cryptography 46.0.4.  
**Mode:** local execution only; no GitHub Actions workflow added or dispatched.

    python -m pip install 'jsonschema>=4.23,<5' 'cryptography>=44,<47'
    python .github/scripts/simulation_contract.py

- PASS — Draft 2020-12 schema.
- PASS — 10 synthetic records across eight record collections.
- PASS — trace order, SHA-256 predecessor chain and replay root.
- PASS — Ed25519 fixture signature and signed-body digest.
- PASS — structured agent decision is bound to the referenced trace action and digests.
- PASS — synthetic-only evidence cannot be presented as external-world validation.
- PASS — 24 negative tests reject tampering, broken references, false world-validity claims, holdout leakage, self-approval and authority implication.

## Limits
No candidate simulator or package was installed; no live MCP server was connected; no physics/FEM solver was run; no independent physical, measured or social reference dataset was used. The fixture proves only schema and validator behavior, not simulator fidelity, scientific correctness, solver convergence or production interoperability.
