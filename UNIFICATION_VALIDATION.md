# Unification Contract Validation

**Inventory:** 24th owner-supplied inventory  
**Status:** Source committed; execution evidence pending. No passing test claim is made for this revision.

## Shared artifacts
- UNIFICATION_ARCHITECTURE.md
- schemas/unification/unification-contracts.v1.schema.json
- examples/unification/unification-fixtures.v1.json
- .github/scripts/unification_contract.py

The fixture contains synthetic public metadata only. Every record has authority_effect = none and boundary = portable_public_record. It contains no C2O-private authorization schema, policy, identity, key, permit, credential, model weight, deployment topology or operational trace.

The standard-library validator checks identifiers, kinds/layers, source and limitation data, public boundary, authority effect, interface roles, MCP/A2A separation, product-versus-standard classification and evidence for independently_verified claims. It defines 12 negative semantic cases.

From the repository root, run:

    python .github/scripts/unification_contract.py --fixture examples/unification/unification-fixtures.v1.json

Preserve stdout/stderr, interpreter version, commit SHA and file digests with the execution record. No GitHub Actions workflow is added or dispatched.

A successful contract check validates only the synthetic fixture. It does not prove a product is installed, two products interoperate or a vendor claim is true. Independent security and compatibility tests remain required.