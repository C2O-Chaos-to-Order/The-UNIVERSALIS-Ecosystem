# UNIVERSALIS Public Repository Catalog and Integration Contract

**Identifier:** UNI-REPO-CATALOG-001  
**Version:** 0.1.0  
**Status:** Proposed public catalog and interoperability contract; pending review  
**Snapshot date:** 2026-11-11  
**Scope:** The 12 public UNIVERSALIS repositories in the C2O-Chaos-to-Order organization

## 1. Purpose

This catalog records the public UNIVERSALIS repository family, identifies each repository's canonical responsibility, and defines the minimum contracts required for the repositories to work together.

It is public by design. It lists only public UNIVERSALIS repositories and public-safe responsibilities. It does not enumerate private repository names, private branch names, credentials, internal source paths, or private operational details.

This catalog does not claim that the listed repositories are complete, independently validated, or production-ready. A repository's existence, public visibility, successful CI run, or merged proposal does not establish acceptance, scientific validity, safety certification, or permission to deploy.

## 2. Public repository catalog

All commit identifiers below are the observed main-branch snapshots on 2026-11-11.

| Repository | Main snapshot | Current state | Canonical responsibility |
|---|---|---|---|
| [The-UNIVERSALIS-Ecosystem](https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Ecosystem) | 6679b9720f3dbf8878fddd6f5d06f776edf8f29c | Product source; LIMITED | Public product architecture, portable implementation, prototype, research/evidence scaffold, public registries, tests, developer documentation, build/verification workflows, and authorized releases. |
| [Research-for-the-UNIVERSALIS-Ecosystem](https://github.com/C2O-Chaos-to-Order/Research-for-the-UNIVERSALIS-Ecosystem) | 8e65021ba3e6e6c3a9333d16e98c87b00e4c6fb5 | Research workspace; 1 open PR (#8) | Public research methods, public source registers, research charters, evidence, requirements, reports, simulation protocols, independent review, and build/no-build recommendations. |
| [The-UNIVERSALIS-Ontology](https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Ontology) | 96bc06a41017b83f001e69493e52a6956c746138 | Master ontology documents | Canonical public master ontology for Human and Intelligence. Markdown is the canonical text; DOCX is a companion copy. |
| [The-UNIVERSALIS-Human-Knowledge](https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Human-Knowledge) | 5bb83c319c759193dfd3aed9054c5b419edf65f5 | Domain documents | Human Subjects of Knowledge (H-K). |
| [The-UNIVERSALIS-Human-Capabilities](https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Human-Capabilities) | 0622e6c63f7ad6922685da138a7630ca767fbdb4 | Domain documents | Human Capabilities (H-C). |
| [The-UNIVERSALIS-Human-Skills](https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Human-Skills) | 6619e44f8abb75c5cbaf79a76991f80f0909e1aa | Domain documents | Human Skills (H-S). |
| [The-UNIVERSALIS-Human-Powers](https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Human-Powers) | 6ec7b3b648ef0659f76f983ebf7978c86be82eef | Domain documents | Human Powers (H-P). |
| [The-UNIVERSALIS-Intelligence-Knowledge](https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Intelligence-Knowledge) | 4d77c248ed63fb27508fabd63bb34945e6095ad2 | Domain documents | Intelligence Subjects of Knowledge (I-K). |
| [The-UNIVERSALIS-Intelligence-Capabilities](https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Intelligence-Capabilities) | d728ae02a84f97f6b0115f0db20d0355bff85800 | Domain documents | Intelligence Capabilities (I-C). |
| [The-UNIVERSALIS-Intelligence-Skills](https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Intelligence-Skills) | bf8ef3f6629cdd31b78f85bac6a1fac22ef2f849 | Domain documents | Intelligence Skills (I-S). |
| [The-UNIVERSALIS-Intelligence-Powers](https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Intelligence-Powers) | 1884b513281269e488d1a38ab05a97538f8d6020 | Domain documents | Intelligence Powers (I-P). |
| [The-UNIVERSALIS-Encyclopedias](https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Encyclopedias) | Empty | Uninitialized | Planned public encyclopedia destination. It may contain only public-safe, rights-cleared, provenance-preserving material. |

The eight Human/Intelligence domain repositories currently identify a canonical Markdown document and a companion DOCX file. The Markdown file remains authoritative when the two differ. The ontology repository follows the same canonical-text rule.

## 3. Public integration model

The repositories are a connected knowledge and product system, not twelve interchangeable folders:

1. The master ontology defines the shared Human and Intelligence concepts, identifiers, and relationships.
2. The eight Human/Intelligence repositories own their respective domain documents and proposed domain taxonomies.
3. Public research records evidence, provenance, uncertainty, contradictions, requirements, and review outcomes. It does not silently turn a research finding into a product requirement or implementation authorization.
4. The product repository consumes reviewed, versioned, public-safe requirements and contracts. It owns public implementation, tests, documentation, and releases.
5. The encyclopedia repository, once initialized, organizes only public-safe, rights-cleared material with source provenance and unresolved claims visible.

A domain repository must declare which ontology version it uses. The ontology must not silently absorb an unreviewed domain change. Research claims must remain traceable to their sources and cannot acquire authority merely by appearing in a domain document or encyclopedia.

## 4. Required public artifact contract

Every artifact intended for cross-repository use should have:

- a stable artifact identifier and schema version;
- a canonical repository and relative path;
- a commit SHA and blob SHA when pinned to a Git object;
- source role, author/owner, version, retrieval or creation date, and provenance;
- license and rights status;
- release classification and limitations;
- dependency identifiers and compatible version ranges;
- evidence status and authorization status as distinct fields.

A Git-pinned source uses the complete D09 tuple: repository, repository-relative path, commit, and blob SHA. Partial or orphan locator fields are invalid. A source locator proves identity and traceability of the object; it does not prove the source is true, safe, licensed, reviewed, or authorized for a particular use.

## 5. Public research method must be portable

Public UNIVERSALIS research must have a public, versioned method profile that explains research intake, assumptions, evidence classes, pre-simulation preparation, simulation execution, post-simulation analysis, reporting, verification, failure handling, and acceptance boundaries.

The public research process must be usable by contributors who have no access to non-public repositories or systems. Public workflows must not require private credentials, private corpus access, private paths, or a private document as an inaccessible operational dependency.

The public research README currently points to non-public governance material as its methodology authority. That reference is a portability gap. The correction is to publish a reviewed, self-contained public method profile with its own version and provenance. This profile must be an approved public derivative; private material must not be copied or exposed merely to remove the link.

Until the public method profile is available and the public research package is reconciled, do not represent the public research process as fully independent or complete.

## 6. Public/private source boundary

- No automatic mirroring or synchronization from private systems is permitted.
- Public repositories contain only material approved for public release under the applicable license and rights.
- Public source registers use true public provenance for public examples and vendored fixtures.
- A synthetic fixture is a newly authored fixture, not a substitute for the historical identity of a private source.
- No private credentials, data, private paths, source code, operational configuration, or unpublished procedures are introduced into public repositories.
- Any proposed external interface is separately reviewed, versioned, scoped, revocable, least-privilege, and auditable.
- A request is not authorization. An authorization is not proof of safety. A successful operation is not proof of correctness.

The catalog does not authorize public release or transfer. It defines the public-side structure within which a separately authorized transfer could be reviewed.

## 7. Compatibility and change control

Before a change to one public repository is treated as integrated, its declared consumers should verify:

1. the referenced ontology and schema versions exist;
2. identifiers and relationships resolve;
3. canonical source and companion-file status are clear;
4. source locators, classifications, licenses, and rights metadata are valid;
5. dependent repositories remain compatible with the new version;
6. public-release and privacy checks pass;
7. limitations, contradictions, deprecations, and migration notes are recorded.

Breaking changes require a version increment, a migration note, and a consumer-impact review. Branch names and mutable main references are not dependency pins.

A future cross-repository compatibility workflow should test the public contracts across the repositories listed here. This workflow is not implemented by this document. It must be built only after the repository source content, ontology identifiers, version contracts, and research-method profile are reconciled.

## 8. Current public integration blockers

- The public research method is not yet self-contained and portable.
- The eight domain repositories are document baselines; machine-readable domain exports, ontology compatibility declarations, and cross-repository conformance tests remain to be established.
- The public encyclopedia repository is empty and has no initialized scope or content.
- The README status snapshots in the ontology and domain repositories do not all match their current main-branch commit identifiers; those snapshots require refresh against the current tree.
- The current product prototype, Engineering Doctor, and scaffold retain LIMITED/prototype classifications. This catalog does not change those classifications or authorize their deployment.

## 9. Work order

1. Publish and review the portable public research-method profile.
2. Reconcile the outstanding public research PR and package classification.
3. Refresh the ontology and eight domain-repository README snapshots and add this catalog as their shared public integration reference.
4. Define stable machine-readable ontology/domain schemas and compatibility declarations.
5. Initialize the public encyclopedia repository with a README, scope, rights policy, source rules, and acceptance criteria before adding content.
6. Add cross-repository compatibility checks after the source contracts and version pins exist.
7. Reassess product implementation only against reviewed requirements and evidence.

**Status rule:** a public repository is not complete because its README lists a role. Its canonical artifacts, source lineage, schema/ontology compatibility, evidence, and release gates must be present and verified.
