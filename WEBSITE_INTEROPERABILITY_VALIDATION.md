# Website Interoperability Validation — UNIVERSALIS

Branch: `implementation/repository-foundation-2026-11-12`  
Contract version: 1.0.0  
Status: **Implemented; awaiting the current PR-head CI run.**

## Positive contract fixture

The public fixture contains six synthetic website contract records:
1. Site definition and revision.
2. Agent capability manifest and interaction/discovery declarations.
3. Revision-pinned site ChangeSet.
4. Scoped site permission profile.
5. Website audit receipt and findings summary.
6. Site preview/publish/deployment receipt.

The validator checks unique page routes and IDs; draft/preview/publication lifecycle; explicit WebMCP maturity, structured state, revision pinning, stale proposal rejection and a human publishing gate; stale-revision refusal; approval before committing publish/deploy changes; scoped permission consistency; human approval for publish/deploy permissions; audit severity summary reconciliation; and signature/operator/approval metadata on successful production publish, deploy and DNS receipts.

## Negative contract tests

Eleven cases must be rejected:
1. Duplicate site route/page definition.
2. Publish capability without human approval and owner authorization.
3. WebMCP surface without stale-proposal protection.
4. Stale ChangeSet marked committed.
5. Approved ChangeSet without approval reference.
6. Publish/deploy ChangeSet committed without human approval.
7. Publish permission without a human gate.
8. Audit summary that does not reconcile with its findings.
9. Passing audit containing a critical finding.
10. Successful production publish without approval.
11. Successful production deployment without signature metadata.

## Public-boundary checks

The shared schema, synthetic fixture, validator and CI workflow are public portable artifacts. The UNIVERSALIS repository does not contain the C2O-private website authorization schema, fixture, publishing budget, private governance policy, signing-key reference or private validator. It contains no C2O credentials, deployment secrets, private content, owner/authority decisions, domains under private operation or operational audit reports.

## CI execution evidence

Workflow: `.github/workflows/website-interoperability-contract.yml`. It installs the JSON Schema validator and runs the six-record/eleven-negative-case public contract test.

**CI receipts:** To be added after GitHub completes the run for the current PR head. Passing CI proves only schema and synthetic-fixture behavior.

## Limits

No live website was crawled or audited; no site content was changed or published; no CMS token or deployment secret was created; no DNS change was made; no third-party CMS, builder, scanner, WebMCP implementation or DAST tool was installed; no production build was released; and no cryptographic signing service was used. CI does not establish website ownership, authorization, accessibility conformance, privacy, production security, source-product suitability, interoperability or deployment.
