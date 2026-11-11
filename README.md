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

Core tests include an automated leak test. The test hashes identifiers and sliding word n-grams from Engineering Doctor files and other repository paths except the pre-existing prototype and scaffold trees, and compares those SHA-256 digests to a denylist that stores only hex digests, so it does not restate private names. A match fails the build.

See [engineering_doctor/README.md](engineering_doctor/README.md) for scope, limitations, and what is not verified.

## Development status

**Status: Documentation foundation initialized; product implementation not yet started.**

The first proposed implementation target is a bounded, local-first, read-only continuity and research capability. The exact requirements, architecture, dependencies, test criteria, and implementation stages remain subject to the research reports and owner review.

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
