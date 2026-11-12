# Universal Tooling Contract (Public Derivative)

**Identifier:** UNI-TOOL-CONTRACT-PUBLIC-001  
**Version:** 0.1.0  
**Status:** Public-safe derivative; pending further owner review if needed  
**Date:** 2026-11-12  
**Scope:** Public UNIVERSALIS tooling under C2O governance  
**Guiding principle:** *With Power, Comes Responsibility.*

## 1. Purpose

This is the public-safe derivative of the authoritative Universal Tooling Contract owned by C2O (Father Thread).

It defines the shared interface contracts, provenance rules, and validation patterns that public UNIVERSALIS tools must follow. It contains only material approved for public release. It does not contain private source, private paths, credentials, unpublished procedures, or internal C2O identifiers.

C2O remains the authoritative source of truth for the full contract. Any future updates to shared schemas or rules originate in C2O and are transferred only through the explicit private-to-public transfer gate.

## 2. Authority model (public view)

- C2O retains governance and authorization authority.
- UNIVERSALIS implements only approved public-safe subsets of the contracts.
- UNIVERSALIS tools report evidence, status, limitations, and proposals. They do not self-authorize.
- A public tool pass, test success, or registry entry is not authorization, scientific validation, or independent verification.

## 3. Universal principles (public subset)

Public tools must:

1. Be read-first and fail-closed by default.
2. Use versioned schemas and explicit provenance tuples (repository, path, commit, blob SHA) for public objects.
3. Separate evidence status from authorization status.
4. Preserve limitations, contradictions, and UNKNOWN results.
5. Never require private credentials, private corpus access, or unpublished data.
6. Emit immutable run records.
7. Remain usable by contributors who have no access to private C2O repositories.

## 4. Public tool set (initial)

| Tool | Public contract | Notes |
|------|-----------------|-------|
| Cross-repository Compatibility & Contract Checker | Schema version, ontology pin, public provenance, README-vs-tree, dependency range checks | Public allowlist only. Extends patterns from Engineering Doctor. |
| Domain / Ontology Exporter + Validator | Markdown-to-JSON schema export and crosswalk for public domain and ontology repositories | Markdown remains canonical. |
| Provenance & Transfer-Gate Reviewer (public checklist) | Public-safe checklist subset only | Does not receive or store private source locators. |
| Capability & Evidence Registry | Extends existing `registry/` schemas | Only cleared public records. |
| Research Method Profile Runner | Fully self-contained public method profile | No dependency on private research plans. |

## 5. Shared public artifact contract

Public artifacts intended for cross-repository use must include the minimum fields defined in the accompanying public schema (stable ID, schema version, public repository and path, provenance, license/rights, classification, limitations, evidence status, authorization status as distinct fields).

A public source locator proves identity of the public object; it does not prove the source is true, safe, licensed, reviewed, or authorized for a particular use.

## 6. Public/private boundary

- No automatic mirroring or synchronization from private systems.
- This repository and its tools must remain fully usable without access to private C2O repositories.
- No private credentials, data, paths, source code, or unpublished procedures are introduced here.
- Any future interface is separately reviewed, versioned, scoped, revocable, and auditable.

## 7. Current disposition

**Status:** Public-safe derivative. Implementation of individual tools remains LIMITED or proposed until requirements, evidence, and explicit authorization are recorded.

Companion public schemas will be added under `registry/schemas/` or a dedicated tools directory after further review.

**With Power, Comes Responsibility.**
