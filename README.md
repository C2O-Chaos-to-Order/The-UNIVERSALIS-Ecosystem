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

## Engineering Doctor

**Status: LIMITED**

Engineering Doctor is a read-only command-line reporter. It inventories operator-configured repositories using GET-only GitHub access, can detect stacked pull requests, README-versus-tree drift, and conflicting status language, and can run optional public demo unittest adapters for the already-public `prototype/` and `scaffold/` suites in this repository. Each run writes an immutable JSON record and a Markdown brief.

Classification: PUBLIC_CANDIDATE. The default repository allowlist is empty; operators pass `--repo` and/or `--allowlist-file`.

> A pass is not authorization, scientific validation, or independent verification.

```text
python -m engineering_doctor run --output-dir /tmp/engineering-doctor-runs --repo The-UNIVERSALIS-Ecosystem
python -m unittest discover -s engineering_doctor/tests -t . -v
```

Core tests include an automated leak test. The test hashes identifiers and sliding word n-grams from Engineering Doctor files, the public `registry/`, and other repository paths except the pre-existing prototype and scaffold trees, and compares those SHA-256 digests to a denylist that stores only hex digests, so it does not restate private names. A match fails the build.

See [engineering_doctor/README.md](engineering_doctor/README.md) for scope, limitations, and what is not verified.

## Tool Registry and Evidence Registry

**Status: LIMITED**

`registry/` is a minimal public registry for tool records and evidence records. It ships versioned JSON Schemas (`registry/schemas/`) and a fail-closed stdlib validator (`python -m registry.validate`) that rejects unknown fields, missing fields, bad identifiers, and evidence or test links that do not resolve.

The first record is [`registry/tools/tool-001.json`](registry/tools/tool-001.json) (Engineering Doctor, LIMITED / PUBLIC_CANDIDATE). The owner field is the placeholder `owner`. Evidence attached there is public and reproducible only: the core unittest suite and public GitHub Actions run [42900738045](https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Ecosystem/actions/runs/42900738045). Additional live-run evidence recorded by the private adapter that consumes this public core is not copied here. Records do not contain scores or confidence values. `REQ-RUBY-01` and `REQ-ONYX-01` record existing Doctor behaviour (a pass is not acceptance; run records are immutable and keep failures and UNKNOWN results) as public-safe references to privately originated principles labelled Ruby and Onyx. They are not a tablet-compliance claim and are not authorization.

A pass is not authorization, scientific validation, or independent verification.

## Development status

**Status: bounded implementation and research tooling exist; no research programme has yet been conducted inside this repository, and nothing here is independently verified.**

Two things are in this repository. The first is a bounded, local-first, read-only continuity prototype. The second is a research and evidence scaffold: a package format, schemas, and validation tools intended to hold research records once that research exists. Neither is an accepted implementation or a research result.

The separate Engineering Doctor and Tool Registry sections above describe their own limited tools; they do not upgrade the scaffold or prototype to accepted status or demonstrate an end-to-end research workflow.

### What exists and has been executed

| Component | What it does | How far it is verified |
|---|---|---|
| `prototype/` | A local, read-only continuity and research prototype. SQLite store, append-only records, evidence states kept apart from transport outcomes, coverage that must reconcile, six distinguishable route outcomes, invalidation that reopens dependents, status rendering that requires text and a machine value, and an in-memory authorization stub. | 69 automated tests pass locally on Python 3.13. Stages P0–P3 and P5–P7 are implemented against the requirement identifiers listed in `prototype/REQUIREMENT_TRACE.md`. **Thirty-one register identifiers are not implemented**, and the trace says which. The authorization type is a stub and proves nothing about a real identity provider. Not independently reproduced. |
| `scaffold/tools/validate_programme.py` | Checks a programme package for internal consistency: manifest integrity, traceability, recorded execution fields, expectation locking, count arithmetic, honesty of status claims, and release classification. | Seven checks, all exercised. **It does not re-execute simulations, award credit, or establish that a finding is true.** |
| `scaffold/tools/validate_records.py` | Structural conformance of standalone record files against one scaffold schema. Implements `type`, `enum`, `const`, `required`, `properties`, `additionalProperties`, `items`, `minLength`, `maxLength`, `pattern`, `minimum`, `maximum`. Any other constraint keyword stops the run with exit 2 rather than being ignored. | 268 scaffold tests pass locally, including positive, negative, and boundary fixtures for every supported keyword, and a mutation test that requires each programme check to fail when the defect it exists to catch is present. Its `additionalProperties` handling is audited against every schema file by a test, and it refuses a keyword or keyword argument it cannot apply rather than skipping it. One documented deviation: it rejects `1.0` for `type: integer`, which draft 2020-12 permits. **Not a complete JSON Schema implementation, and a pass is not scientific validation.** |
| `scaffold/tools/new_programme.py` | Instantiates an empty programme package from the public template, with zero counts, `PENDING` acceptance, and SHA-256 locks. | Verified: a freshly generated package passes all seven programme checks. It contains no research and claims none. |
| `scaffold/tools/corpus_probe.py`, `clause_leak_check.py`, `evidence_states.py`, `package_files.py` | Corpus indexing without writing into it; a character-level scan utility; the evidence ladder and its separate execution-outcome axis; path locking and classification declarations. | Exercised by the author. The scan is not a privacy certification, release clearance, or independent verification. |

### What has been executed

- The prototype test suite: 69 tests pass.
- The scaffold test suite: 268 tests pass, 1 skipped. The skip needs a private corpus that is not present here, so it is not a pass.
- `new_programme.py` generated a package that then passed all seven programme validator checks.
- The corpus-leak scan utility was exercised by the author; its output is not a privacy certification or release authorization.

### What remains incomplete

- **No research has been conducted in this repository.** No hypothesis has been investigated, no scenario model has been executed, and no research report has been produced from executed evidence. The scaffold can hold such work; it does not yet contain any.
- **The Tablets have not been integrated as research inputs here.** Mapping clauses to hypotheses, comparing them against external evidence, and separating established knowledge from speculative or metaphorical claims is research work that has not begun in this repository.
- **No end-to-end research workflow has been demonstrated.** Ingest, provenance, evidence registration, claims, research execution, simulation execution, record validation, report generation, and the effect of a correction on dependent conclusions have not yet been run as one connected workflow.
- **No mutation testing, no independent reproduction, and no adversarial execution** of these suites has been performed. Every result above is a self-reported local run by the author of the code.
- **Architecture dependencies remain incomplete.** Architecture-dependent stages cannot proceed until the required source documents are recovered, reviewed, and cleared for public use.

### What has not been independently verified

Nothing in this repository has been independently reproduced. Every test result, every validator pass, and every count above is reported by the party that wrote the code. Independent challenge is a separate role, and until it happens these results are claims by their author, not verified facts.

A passing test demonstrates that the tested behaviour matches its test case. It does not demonstrate that a requirement is accepted, that a research question is answered, that a finding is true, that the product is ready, or that release is authorized.

Do not interpret this README, a successful build, a passing test, a validator pass, or an experimental prototype as implementation acceptance, production readiness, deployment permission, or release authorization.

## Development rules

- Follow applicable do-no-harm and risk controls.
- Build only against traceable, accepted requirements.
- Keep authentication, authorization, tenant isolation, validation, and action controls outside the language model.
- Prefer maintained dependencies and established security mechanisms; do not invent cryptography.
- Test negative, boundary, adversarial, privacy, recovery, and cross-component cases.
- Preserve evidence, limitations, and regression history.
- Require explicit owner authorization for release and deployment.

**Research informs design. Evidence supports claims. Authorization governs consequential change.**

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
