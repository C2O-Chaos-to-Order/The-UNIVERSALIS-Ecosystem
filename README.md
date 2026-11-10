# UNIVERSALIS

**UNIVERSALIS is the public open-source Architecture and Transformative Intelligence product family.**

**Guiding principle:** *With Power, Comes Responsibility.*

## Repository purpose

This repository is the source home for the open-source UNIVERSALIS product: architecture specifications, implementation code, automated tests, developer documentation, build and verification workflows, packages, and release artifacts.

UNIVERSALIS-specific research, evidence registers, research reports, requirements, and independent review records belong in [Research for the UNIVERSALIS Ecosystem](https://github.com/C2O-Chaos-to-Order/Research-for-the-UNIVERSALIS-Ecosystem).

The governing research methodology and paired technical/Human Tablet source collections remain in [Research for the C2O Ecosystem](https://github.com/C2O-Chaos-to-Order/Research-for-the-C2O-Ecosystem).

## Source and authority boundary

**C2O is Private Source. UNIVERSALIS is Open Source.**

This repository must contain only material approved for public release under the applicable license. It must not contain C2O private credentials, internal data, private infrastructure, unpublished private source, or private operational procedures.

No automatic mirroring or synchronization from C2O is permitted. Any future interoperability must use a separately reviewed and authorized interface that preserves identity, data, permission, ownership, audit, and revocation boundaries.

## Development status

**Status: LIMITED prototype and research scaffold are present on `main`. This is not an accepted product, release, or authorization.**

`main` is at `3c521a82ee1404bd09d219c59ff6a466cb0721d0` (2026-10-31 7:34:33 PM CT, America/Chicago). A `git ls-tree -r --name-only` of that HEAD listed **81** files: this `README.md` plus **80** paths under `prototype/` and `scaffold/`. Fifteen of those paths match `*/tests/test_*.py`. The previous sentence claiming that product implementation had not yet started was incorrect for this HEAD.

The file [`prototype/REQUIREMENT_TRACE.md`](prototype/REQUIREMENT_TRACE.md) traces public `ULC-<tablet>-<clause>` identifiers to tests that exercise behaviour. That file itself says a named test does not mean the requirement is accepted, reviewed, or complete, and that thirty-one identifiers are not implemented.

Research packages for UNIVERSALIS are not on this `main`. They live as open draft pull requests #1–#8 in [Research for the UNIVERSALIS Ecosystem](https://github.com/C2O-Chaos-to-Order/Research-for-the-UNIVERSALIS-Ecosystem). This `main` has no `.github/` workflow tree; a verification workflow is proposed on pull request #7 of this repository (not applied here).

Do not interpret this README, a successful build, or the prototype and scaffold as implementation acceptance, production readiness, deployment permission, or release authorization.

## Development rules

- Follow the governing C2O Research Plan and applicable Do No Harm/risk controls.
- Build only against traceable, accepted requirements.
- Keep authentication, authorization, tenant isolation, validation, and action controls outside the language model.
- Prefer maintained dependencies and established security mechanisms; do not invent cryptography.
- Test negative, boundary, adversarial, privacy, recovery, and cross-component cases.
- Preserve evidence, limitations, and regression history.
- Require explicit owner authorization for release and deployment.

**Research informs design. Evidence supports claims. Authorization governs consequential change.**

## Public traceability (2026-11-10)

This map uses only public locators. It does not copy private C2O corpus text.

| Step | What exists here | Gap |
|---|---|---|
| Requirement | [`prototype/REQUIREMENT_TRACE.md`](prototype/REQUIREMENT_TRACE.md) on this `main` | The file states that the collection-level `UNI-001`…`UNI-015` map is a different register and is not implemented here. |
| Research | Research packages are in Research-for-the-UNIVERSALIS-Ecosystem drafts #1–#8, not in this repository | This product `main` is not the research ledger. |
| Simulation | Not present as an accepted ledger on this `main` | **GAP.** Draft research pull requests may claim executed runs; they are not on Research-UNI `main` and are not accepted by this note. |
| Spec | Prototype and scaffold documents and code comments on this `main` | **GAP** as an accepted product specification or release. |
| Implementation | `prototype/` and `scaffold/` on this `main` (LIMITED) | Not accepted, not authorized, not a release. Additional tests and the verification workflow live on feature-branch pull requests (including #7) and are therefore not all visible from this default branch (F-25). |

A longer private ledger lives in `Research-for-the-C2O-Ecosystem` `CORRECTIONS/2026-11-10/F-06-F-18-F-25-traceability-and-evidence-ledger.md` (private repository). That file is not copied here.
