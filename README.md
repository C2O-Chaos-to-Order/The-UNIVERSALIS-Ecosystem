# UNIVERSALIS

**UNIVERSALIS is the public open-source Architecture and Transformative Intelligence product family.**

**Guiding principle:** *With Power, Comes Responsibility.*

## Repository purpose

This repository is the source home for the open-source UNIVERSALIS product: architecture specifications, implementation code, automated tests, developer documentation, build and verification workflows, packages, and release artifacts.

UNIVERSALIS-specific research, evidence registers, research reports, requirements, and independent review records belong in [Research for the UNIVERSALIS Ecosystem](https://github.com/C2O-Chaos-to-Order/Research-for-the-UNIVERSALIS-Ecosystem).

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

**Status: bounded implementation and tooling exist; no research programme has been conducted in this repository, and nothing here is independently verified.**

This repository contains a bounded, local-first, read-only continuity prototype and a research/evidence scaffold. Neither is an accepted implementation or a research result.

The separate Engineering Doctor and Tool Registry sections above describe their own limited tools; they do not upgrade the prototype or scaffold to accepted status or demonstrate an end-to-end research workflow.

Do not interpret this README, a successful build, or an experimental prototype as implementation acceptance, production readiness, deployment permission, or release authorization.

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
