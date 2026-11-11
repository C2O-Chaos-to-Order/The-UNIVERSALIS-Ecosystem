# Foundation Tooling v0.1
## Public architecture, requirements, threat model, and synthetic verification specification

**Document status:** Public architecture specification — candidate for owner review  
**Version:** 0.1.0  
**Prepared:** 2026-11-10  
**Classification:** Public candidate  
**Implementation status:** Specification only; it does not claim the four capabilities are implemented, independently verified, or authorized for operational use.

> **Governing principle:** A tool must never be trusted merely because it was built to enforce trust. It must establish its own provenance, authority boundaries, limitations, and evidence—and remain subject to independent verification.

This specification describes reusable public interfaces and synthetic verification methods. It contains no private runtime configuration, private repository inventory, internal authority data, credentials, private source paths, or non-public operational evidence. It is not an authorization grant or release approval.

---

## 1. Purpose and design decision

Foundation Tooling v0.1 defines four separate capabilities that can work together without collapsing identity, acceptance, authority, artifact integrity, and operational correctness into one state:

1. **Human Decision Record:** records a human review outcome against an exact artifact and evidence set. Acceptance is not authorization.
2. **Restore and Verify:** restores a selected backup or artifact into a new isolated destination, compares its contents, and runs only constrained verification checks. The original source must remain untouched.
3. **Remote Commit Checker:** verifies that an exact full commit identifier resolves in the claimed remote repository and distinguishes absence from access or service failures.
4. **Decision Authority Check:** evaluates whether an authenticated signer has explicit authority for the exact decision, subject, operation, purpose, scope, and time.

These capabilities should extend the existing Engineering Doctor and Tool/Evidence Registry. They must not create a second registry, a competing Doctor, or a new autonomous release authority.

### 1.1 Core distinctions

- Identity is not authority.
- A valid signature is not proof of authority.
- Acceptance is not permission to execute, publish, merge, deploy, or access data.
- A test pass is not acceptance.
- Commit existence is not package equivalence.
- A successful restore is not proof of application correctness.
- An unresolved or unavailable result is not a pass.
- A tool's self-assessment is not independent verification.

## 2. Relationship to existing public components

The current public source tree already contains:

- **Engineering Doctor** (`engineering_doctor/`): a LIMITED read-only command-line reporter with configurable repository scope, immutable run-record behavior, explicit limitations, public synthetic tests, and a public leak scan.
- **Tool/Evidence Registry** (`registry/`): versioned tool/evidence schemas, public records, and a fail-closed validator.
- **Knowledge Record Validator** (`knowledge/`): a public validator that keeps knowledge, interpretation, requirements, tests, evidence, review, authorization, capabilities, and permissions separate.
- **Foundation record** (`foundation/`): a published foundational invariant and associated machine-readable record.

The existing components are useful substrates, not proof that the four new capabilities below already exist. In particular, a structural reference to a human decision does not by itself verify a signature or establish that the cited person had authority. Run-record immutability does not implement a general restore-and-verify workflow.

**Reuse rule:** keep the existing public registry and Doctor as the shared public foundations. Add new schemas, testable adapters, and registry records as those components are implemented and independently reviewed. Do not duplicate their responsibilities.

## 3. Public architecture

### 3.1 Component responsibilities

| Component | Responsibility | Explicit non-responsibility |
|---|---|---|
| Human Decision Record | Capture exact subject, review scope, decision, rationale, evidence, signer identity reference, signature, and lifecycle | Does not grant permissions or execute commands |
| Signature Verifier | Verify the signed bytes, payload type, identity issuer, and configured trust policy | Does not decide whether the signer is authorized for the requested action |
| Restore and Verify | Check a backup, restore to a new isolated destination, compare content, and run bounded verification | Does not overwrite an original source or prove all application behavior correct |
| Remote Commit Checker | Resolve an exact commit in a specific remote repository and compare requested object identities | Does not infer that an inaccessible commit does not exist |
| Decision Authority Adapter | Evaluate an external project-configured authority source against exact scope and time | Does not create or broaden its own authority source |
| Evidence Record Writer | Preserve provenance, inputs, outputs, failures, UNKNOWN states, limitations, and supersession | Does not award an authorization or independent verification status |

### 3.2 Data flow

```text
Human reviewer
   │ decision about exact artifact + scope
   ▼
Human Decision Record ──► Signature Verifier
                                │
                                ▼
                        signer identity claims
                                │
                                ▼
                       Authority Provider Adapter
                                │
                       AUTHORIZED / DENIED / UNKNOWN

Remote Commit Request ──► Remote Provider Adapter (GET only)
                              └── exact repository + commit + optional tree/digest

Backup / Snapshot ──► Integrity Check ──► New Isolated Restore Destination
                                                ├── file manifest comparison
                                                ├── constrained application checks
                                                └── original-source unchanged check

All components ──► versioned evidence records ──► public registry after review
```

A project may provide an authority provider through a documented interface. An unconfigured provider must not default to approval. The public implementation must remain usable without any external private service.

### 3.3 Shared evidence record

Each run should preserve:

- schema ID/version, record ID, tool ID/version, and source/build provenance;
- unique run ID and UTC start/finish timestamps;
- exact input subjects, full commit SHA or artifact digest, and digest algorithm;
- policy/authority provider version and digest where applicable;
- decision scope, purpose, and operation where applicable;
- signature-verification result separately from authority result;
- observed output, tests executed, evidence locators, failures, skipped tests, and limitations;
- source/target before-and-after digests for restore operations;
- correction and supersession links for updated decisions.

Never record access tokens, passwords, private keys, recovery codes, or unnecessary personal data. Public fixtures must use synthetic identities and synthetic repositories, such as `.invalid` example domains.

## 4. Technology and dependency assessment

These are candidate technologies for evaluation, not a frozen dependency lockfile.

| Area | Recommended starting point | Important limitation |
|---|---|---|
| Runtime | Python 3.11+ to align with the current public codebase and CI baseline | Keep the core dependency footprint small and test on the declared supported interpreter matrix |
| Record structure | Existing Tool/Evidence Registry patterns and JSON Schema Draft 2020-12 | The current project validator supports a limited, explicit subset of JSON Schema keywords; new schemas must stay within that subset or the validator must be extended and tested. A `$schema` declaration alone does not prove full conformance |
| Signed records | DSSE-style typed envelope; evaluate an in-toto Statement v1 predicate for subject and decision metadata | in-toto describes authenticated software-artifact metadata; it does not establish human authority. DSSE does not supply project key management or authority policy |
| Signature implementation | Evaluate Sigstore Cosign for signing and verification bundles | Identity claims, issuer constraints, timestamp, certificate, and transparency proof must be verified. A valid signature does not authorize an operation |
| Restore backend | Generic filesystem/backup adapter; evaluate restic where the selected backup system uses it | `restic check --read-data` reads backup data; restore verification does not prove application correctness. Always restore to a new isolated target |
| Remote commit resolution | GitHub REST GET commit endpoint behind a provider-neutral interface | A private repository may return 404/403 when the caller lacks permissions; treat ambiguous access as unresolved |
| Authority policy | Small deterministic evaluator and a versioned provider contract for the first iteration; evaluate OPA/Rego if policy complexity justifies it | Policy update/distribution becomes a security boundary. A policy engine is not itself a source of legitimate authority |
| Cryptographic operations | Maintained signing and verification tools/libraries | Do not implement cryptographic algorithms or signature formats from scratch |
| Tests | Standard-library `unittest`, synthetic fixtures, and optional property-based tests after dependency review | No real identities, credentials, private corpora, or live operational data in public tests |

### 4.1 Dependency rules

- No always-running policy service or signing service is mandatory for the first iteration.
- Pin exact tested third-party versions and preserve dependency/build provenance when a dependency is adopted.
- Use standard-library tools for deterministic file hashing, path checks, record serialization, and local comparisons where suitable.
- Keep external integrations behind narrow adapters with explicit timeouts, errors, and result states.
- Do not add public dependencies on private infrastructure or private configuration.

## 5. Functional requirements

### 5.1 Human Decision Record

The record must bind:

- unique decision and record IDs;
- exact repository, commit, artifact version, and/or content digest under review;
- review scope and explicit exclusions;
- outcome: `ACCEPT`, `REJECT`, `DEFER`, or `REQUEST_CHANGES`;
- human rationale and evidence references;
- signer identity reference and verified issuer;
- decision timestamp and policy version;
- signature envelope and payload digest;
- lifecycle and supersession reference;
- explicit `does_not_authorize` statement.

A moving branch name is not a sufficient subject. Resolve and store the full commit SHA and relevant artifact digest. A changed artifact requires a new decision. Corrections create new superseding records; the original record remains verifiable.

**Tamper-evidence qualification:** a signature protects payload integrity but does not make storage physically unchangeable. Use append-only semantics, content-addressed record identity, protected storage, retained signature material, and an independently governed audit or transparency trail where needed.

### 5.2 Restore and Verify

The verifier must:

1. resolve an exact source/snapshot ID;
2. check backup integrity using the selected backend;
3. create a unique, new, empty restore destination;
4. reject a target that aliases the source or escapes the allowed destination;
5. restore without destructive overwrite/delete behavior;
6. compare a deterministic path/content manifest and explicitly selected metadata;
7. run only allowlisted non-destructive application checks in isolation;
8. compare the original source before/after digests;
9. preserve failures, UNKNOWN results, and limitations.

Restored scripts or binaries must not be executed automatically. Network access should be disabled by default. Any additional access requires separate, scoped authorization.

### 5.3 Remote Commit Checker

The first provider may be GitHub, using GET-only requests against the exact repository and full commit SHA. The interface should allow later providers without changing the record contract.

Required output states:

- `VERIFIED_EXISTS`
- `COMMIT_MISMATCH`
- `NOT_FOUND_OR_NOT_AUTHORIZED`
- `UNAVAILABLE`
- `RATE_LIMITED`
- `INVALID_REFERENCE`
- `TREE_MISMATCH`
- `PACKAGE_DIGEST_MISMATCH`

Commit SHA, Git tree SHA, and package digest are distinct identifiers and must be stored separately. Never claim that an inaccessible private commit does not exist based on a 404 alone.

### 5.4 Decision Authority Check

The evaluator consumes:

- verified signer identity and issuer;
- configured authority provider and version;
- decision type, exact resource, operation, purpose, and scope;
- effective time, expiry, delegation chain, and revocation state;
- separation-of-duty rules where configured.

It returns `AUTHORIZED` only when all required inputs positively establish a matching, active grant. Other outcomes include `NOT_AUTHORIZED`, `EXPIRED`, `REVOKED`, `SCOPE_MISMATCH`, `SIGNER_UNVERIFIED`, `UNKNOWN`, and `CONFLICT_REVIEW_REQUIRED`.

A valid signer without a grant is not authorized. An unavailable authority provider is not a pass. The evaluator cannot create or amend its own grants. Any authorization is narrow, time-bounded, and must be rechecked at execution time when revocation or scope may have changed.

## 6. Requirements and threat model

| ID | Threat / failure mode | Required control | Test evidence |
|---|---|---|---|
| PUB-TH-01 | Signature is treated as authority | Separate signature and authority outcomes | Signed but undelegated actor is denied |
| PUB-TH-02 | Payload or signer is tampered with | Typed envelope, exact digest, issuer/subject verification | Byte alteration, wrong issuer, or wrong payload type fails |
| PUB-TH-03 | Old decision is replayed | Bind subject digest, purpose, scope, policy version, and time | Decision cannot apply to a changed artifact or expired operation |
| PUB-TH-04 | Delegation is expired, revoked, or overbroad | Versioned authority provider, scoped grants, revocation, fail-closed states | Expired/revoked/missing/stale grant never authorizes |
| PUB-TH-05 | Restore overwrites original | New isolated destination; path canonicalization; no delete/overwrite | Source manifest remains identical; alias/path traversal is blocked |
| PUB-TH-06 | Backup corruption is mistaken for success | Backend integrity check and exact restored-content comparison | Bit flip/missing file/interrupted restore is not pass |
| PUB-TH-07 | Remote 404 is mistaken for nonexistence | Preserve access ambiguity and authentication context | Insufficient-access fixture returns unresolved state |
| PUB-TH-08 | SHA syntax or branch name is mistaken for remote identity | Require full SHA and verify returned repository/object identity | Abbreviated SHA, wrong repo, or object mismatch fails |
| PUB-TH-09 | Tree SHA is mistaken for package equality | Keep Git tree and package digest separate | Wrong package digest fails independently |
| PUB-TH-10 | Tool self-assessment is trusted as independent review | Independent verifier and clean reproducible test run | Tool's own success record cannot satisfy independent gate |
| PUB-TH-11 | Public material leaks private content | Synthetic-only public fixtures, leak scan, secret scan, review | Public leak and secret checks pass |
| PUB-TH-12 | Policy update silently changes permission | Versioned, digest-bound policy; externally governed update | Stale/tampered policy blocks decision |
| PUB-TH-13 | Unknown is converted to success | Explicit state vocabulary and fail-closed behavior | Unavailable, skipped, and unsupported cases remain unresolved |
| PUB-TH-14 | Compromised dependency or build is trusted | Record source, dependency lock, build digest, signature, and independent reproduction | Independent rebuild and hash comparison |

The current public foundation invariant remains unchanged by this specification. Record-level checks are declared controls supported by evidence; they do not prove that a tool can never cause harm.

## 7. Synthetic test plan and acceptance criteria

Only disposable synthetic identities, repositories, commits, backup snapshots, and files are allowed in public tests.

### 7.1 Shared tests

| ID | Test | Expected result |
|---|---|---|
| SH-01 | Conformant synthetic record | Structural validation succeeds |
| SH-02 | Unknown record field or unsupported schema keyword | Rejected fail-closed |
| SH-03 | Missing evidence or malformed digest | Rejected or UNKNOWN; never pass |
| SH-04 | Missing/mismatched tool provenance | Provenance gate fails |
| SH-05 | Synthetic private-phrase fixture injected into public scan | Leak test fails |
| SH-06 | Test suite passes without human decision | No acceptance or authorization is inferred |

### 7.2 Human Decision Record tests

- HD-01: valid signature over exact payload verifies; authorization remains separate.
- HD-02: changed payload byte fails signature verification.
- HD-03: wrong issuer/subject/certificate fails identity verification.
- HD-04: duplicate ID with different payload is rejected.
- HD-05: correction creates a superseding record and preserves the original.
- HD-06: changed artifact/commit digest is not covered by the old decision.
- HD-07: `ACCEPT` does not create a permission or execute a command.
- HD-08: missing signature bundle or unverifiable timestamp remains incomplete.

**Pass gate:** all HD cases return the defined outcomes and no accepted record grants authorization.

### 7.3 Restore and Verify tests

- RV-01: healthy snapshot restores to a new destination; required hashes match.
- RV-02: corrupted blob or file fails integrity verification.
- RV-03: missing, extra, or changed file fails manifest comparison unless an explicit expected-difference rule exists.
- RV-04: destination aliasing the original source is refused.
- RV-05: path traversal or an escaping symlink is blocked.
- RV-06: application test cannot write outside the isolated scratch area.
- RV-07: unavailable, locked, or interrupted backend returns UNKNOWN/UNAVAILABLE.
- RV-08: changed original-source before/after digest is a critical failure.

**Pass gate:** all RV cases pass their expected control, the restore is reproducible, and the original source is unchanged.

### 7.4 Remote Commit Checker tests

- RC-01: exact full SHA exists in the exact repository → `VERIFIED_EXISTS`.
- RC-02: abbreviated or malformed SHA → `INVALID_REFERENCE`.
- RC-03: wrong repository or returned SHA mismatch → `COMMIT_MISMATCH`.
- RC-04: private-repository 404 without established access → `NOT_FOUND_OR_NOT_AUTHORIZED`.
- RC-05: provider rate limit → `RATE_LIMITED`.
- RC-06: timeout, DNS, TLS, or API failure → `UNAVAILABLE`.
- RC-07: wrong expected Git tree SHA → `TREE_MISMATCH`.
- RC-08: wrong expected package digest → `PACKAGE_DIGEST_MISMATCH`.

**Pass gate:** access ambiguity is retained, and the checker exposes only GET operations.

### 7.5 Decision Authority tests

- DA-01: active exact-scope grant → `AUTHORIZED` only for the stated scope.
- DA-02: valid signature but no grant → `NOT_AUTHORIZED`.
- DA-03: expired or revoked grant → `EXPIRED` or `REVOKED`.
- DA-04: different resource, action, purpose, or artifact digest → `SCOPE_MISMATCH`.
- DA-05: missing/stale authority provider → `UNKNOWN`.
- DA-06: unverified signer or issuer → `SIGNER_UNVERIFIED`.
- DA-07: configured conflict rule → `CONFLICT_REVIEW_REQUIRED`.
- DA-08: attempted self-creation or self-amendment of authority → refused and recorded as a security failure if any change occurs.
- DA-09: `REJECT` or `DEFER` outcome never authorizes the rejected/deferred operation.

**Pass gate:** all DA cases behave as specified; authority remains external and governed.

### 7.6 Independent verification gate

Before owner review, a separate verifier must reproduce the build/test run from recorded source and dependency references, verify the package digest and signed records, exercise negative cases, and list all UNKNOWN/skipped/unsupported cases. A tool's own report is not sufficient evidence of its correctness.

## 8. Implementation sequence

| Step | Deliverable | Exit criteria |
|---|---|---|
| 0 | Shared schema and interface map | Registry compatibility checked; unsupported schema keywords fail closed |
| 1 | Human Decision Record | HD-01–HD-08 pass; acceptance remains separate from authorization |
| 2 | Restore and Verify | RV-01–RV-08 pass; source remains unchanged |
| 3 | Remote Commit Checker | RC-01–RC-08 pass; inaccessible is not reported as nonexistent |
| 4 | Decision Authority Check | DA-01–DA-09 pass; evaluator cannot change its own authority source |
| 5 | Integrated adversarial review | Cross-component replay, stale policy, compromised dependency, and privacy tests pass independently |

This specification and the associated synthetic tests do not constitute a research or simulation pass, product readiness, or release authorization.

## 9. Public data and privacy requirements

Public-source material may include:

- generic schemas and provider-neutral interfaces;
- public documentation and public dependency references;
- synthetic identities, repositories, commits, snapshots, and fixtures;
- public test results that can be reproduced from the public tree;
- generic threat models and limitations.

Public-source material must not include:

- private repository inventories, allowlists, or runtime configuration;
- private credentials, tokens, keys, signing material, or internal identity mappings;
- private source paths, private run records, private operational counts, or internal evidence;
- non-public policy bundles, delegation records, role mappings, or revocation data;
- unpublished research material or source that has not passed public-release review.

The automated public leak scan is a useful defense, but it is not a complete privacy guarantee. Review source, diffs, metadata, test output, links, and commit messages. A clean scan proves only that the scanned content did not match the current denylist under its current rules.

The public implementation must be independently buildable and operable. Any external authority service is optional and configured by the consuming project. No public tool defaults to a private provider or private credential.

## 10. Limitations and decisions still open

1. Final identity provider and signer-claim policy are not selected.
2. The storage/transparency mechanism for append-only decision records requires a separate design decision.
3. Authority provider data model, delegation issuance, revocation semantics, and separation-of-duty rules are project-configured and not defined by this public specification.
4. The backup backend and tested version must be selected before implementation.
5. File metadata portability, symlink behavior, archive rules, and package digest rules need platform-specific tests.
6. The existing registry validator supports a limited schema-keyword subset; full Draft 2020-12 conformance must not be assumed.
7. No security certification, universal absence-of-harm guarantee, legal compliance, production readiness, or universal correctness is claimed.

## 11. Source register

### Existing public components

- Repository README: https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Ecosystem/blob/main/README.md
- Engineering Doctor: https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Ecosystem/tree/main/engineering_doctor
- Tool/Evidence Registry: https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Ecosystem/tree/main/registry
- Knowledge Record Validator: https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Ecosystem/tree/main/knowledge
- Public foundation record: https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Ecosystem/tree/main/foundation

### Technology and standards references

1. in-toto Attestation Framework specification: https://github.com/in-toto/attestation/blob/main/spec/README.md
2. DSSE specification: https://github.com/secure-systems-lab/dsse
3. Sigstore Cosign quickstart and blob signing: https://docs.sigstore.dev/quickstart/quickstart-cosign/ and https://docs.sigstore.dev/cosign/signing/signing_with_blobs/
4. Sigstore verification: https://docs.sigstore.dev/cosign/verifying/verify/
5. restic integrity check: https://github.com/restic/restic/blob/master/doc/man/restic-check.1
6. restic restore verification: https://github.com/restic/restic/blob/master/doc/man/restic-restore.1
7. GitHub REST commit endpoints: https://docs.github.com/en/rest/commits/commits
8. GitHub REST authentication and permission responses: https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api
9. JSON Schema Draft 2020-12: https://json-schema.org/draft/2020-12/
10. Open Policy Agent policy language and integration: https://www.openpolicyagent.org/docs/policy-language and https://www.openpolicyagent.org/docs/integration

These links support the documented standards and technology assessments. They do not establish that a dependency has been adopted, installed, or security-reviewed in this project.

---

**End of public specification.**