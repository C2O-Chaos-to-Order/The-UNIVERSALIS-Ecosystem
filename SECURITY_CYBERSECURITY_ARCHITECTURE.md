# Security and Cybersecurity Toolchain — UNIVERSALIS

**Boundary:** Open, inspectable, independently operable MotherThread.  
**Owner repository:** The UNIVERSALIS Ecosystem.  
**Status:** Portable security evidence contracts and validators implemented; no third-party security tool is installed or integrated by this change.

## 1. Architecture principles

Security is an external, layered enforcement boundary around agents and tools. Local-first and independently inspectable operation are preferred; policy evaluation and containment must not depend solely on model reasoning. Interception, telemetry, approval routing and hard system-call enforcement are distinct capabilities and must be recorded separately.

UNIVERSALIS publishes schemas, non-sensitive example policies, test fixtures and sanitized evidence formats. It does not publish C2O's private policies, credentials, incident data, asset inventory, target scope, key material or audit traces.

## 2. Open candidate inventory

### Runtime security and agent firewalls
- **AgentWall:** MCP request/response proxy and YAML policy candidate. Supplied accuracy/latency claims were not reproduced; review code, policy defaults and fail-open behavior.
- **HOL Guard:** local-first action/secret/package/MCP/skill review with local receipts. Its own documentation says event coverage depends on what each host integration exposes; inspect its support matrix per agent.
- **AgentSentrix:** three-tier risk and human quarantine gateway candidate; latency and prevention figures remain supplier claims pending reproducible benchmark.
- **ShieldPilot:** claimed prompt-injection patterns, analyzers and hash-chained audit; exact canonical source/release and numbers remain unverified.
- **AgentShield:** name collision/identity ambiguity. The repository found during this review describes an AI agent configuration/MCP security scanner (CLI/GitHub Action/GitHub App), not the described bidirectional runtime interceptor. Do not equate them without an exact source URL.

### Zero-trust, gateways and kernel sandboxing
- **ZTAgent:** open gateway/SDK candidate with OIDC, OPA and HMAC-chained audit. Development defaults turn authentication off and allow running without OPA; production validation rejects those defaults. Treat a development instance as unsafe until configured and checked.
- **OS-Cicada / Sentry_Gateway:** supplied kernel firewall/15-stage MEF/PQC fleet claims require exact repository identity, source, license and repeatable evidence.
- **Kest Core:** SPIFFE/OAuth, OPA/Cedar and Merkle-DAG lineage candidate; canonical project/source and interoperability remain to be confirmed.
- **NVIDIA OpenShell:** open Apache-2.0 secure runtime candidate with kernel-level isolation and declarative policies; version/platform support must be pinned.
- **MCPGuard-Dynamic:** source describes a three-layer MCP proxy with application validation and eBPF/BPF-LSM system-call controls; published repository includes a 14-server/82-case benchmark and Linux/BPF-LSM prerequisites. Performance claims need independent reproduction.
- **k8e:** Cilium/eBPF DNS/FQDN egress-control candidate; verify exact repo and supported kernel/runtime versions.

### Prompt-injection and behavioral defense
- **SNAFT, APEX, Phalanx AI, AgentSecCore:** behavioral firewalls, pre-execution authorization and layered prompt/code scanning candidates; supplied rule counts and security claims remain unverified until source/release pinning.
- **Axora AgentGuard:** component/action security candidate. Its documentation distinguishes discovery, scanning, observation and enforceable interception; support depends on host/integration path.

### Authorized defensive assessment and red teaming
- **modelWrecker, ARTEX, PentAGI, CyberAI and CyberStrike:** candidates for isolated, owner-authorized testing only. No autonomous testing against public or third-party systems is enabled by this repository foundation. The contract records asset-scope digest, authorization, hard boundary, exclusions, operator, stop conditions, safe reproduction type and evidence digest. It intentionally excludes exploit code, payloads and command sequences.
- **ARTEX:** CERT-EU reported use by threat actors, no hard technical scope enforcement in the described project and removal of the original upstream repository in October 2026. Public forks are not treated as a trusted upstream.

### Supply-chain and endpoint assurance
- **agentic-security:** open scanner/posture tool with SBOM/AI-BOM, VEX, SARIF and technical framework coverage. Its current README explicitly states that it does not claim compliance/certification and does not publish SARD benchmark scores.
- **Hawkeye Agent:** package/dependency health and SBOM candidate; deps.dev, CVE and OpenSSF Scorecard outputs should be pinned to source versions and timestamps.
- **Chainloop:** open Apache-2.0 evidence store/attestation system; its current repository describes signed, timestamped in-toto records, SBOMs, VEX, SARIF and SLSA provenance. Self-hosting and key custody still require local deployment review.
- **Vectra Guard:** endpoint/command-risk candidate; exact upstream, package integrity and platform behavior remain to be verified.

All product names remain candidates/reference patterns, not installed integrations. The source-supplied numerical claims (prevention rates, pattern counts, latency, star counts and tool counts) are not adopted as UNIVERSALIS acceptance criteria.

## 3. Portable contract family

The shared v1 schema defines versioned records for taxonomy crosswalks, policy enforcement receipts, containment attestations, scope-bounded assessment metadata, sanitized findings, SBOMs, build provenance, sandbox/kernel evidence, hash-chained audit records and technical-control coverage. It carries opaque references and content digests, not private policies or raw incident content.

## 4. Crosswalk and evidence rules

- OWASP LLM Top 10 2025 and OWASP Agentic Top 10 2026 are separate versioned threat taxonomies.
- OWASP MCP Top 10 2025 remains marked beta/pilot in its published roadmap at the time of this review; do not present it as a finalized standard.
- MITRE ATLAS is a living AI threat knowledge base. Mappings must retain source edition/version, item labels, relation type (equivalent/related/partial/etc.) and rationale.
- NIST AI 600-1 is a Generative AI risk-management profile, not a cyber threat taxonomy or certification. NIST/OWASP technical-control reports are evidence maps only and cannot be called a certification or compliance determination.
- A finding is evidence-bearing but is not proof of exploitability or risk by itself. Record confidence, reproduction method, evidence digest and remediation status.
- A containment claim must identify the enforcement substrate and whether the control plane is independent of the agent. A software policy receipt is not hardware attestation.

## 5. Cryptographic boundaries

Portable receipt signatures use public-key signatures and an optional public-key reference, key fingerprint, signed-payload digest, signature bytes and verification status. The schema does not implement signing, key discovery, trust-anchor distribution, revocation checks or signature verification.

HMAC audit chains are local to systems holding the HMAC secret; do not export a private HMAC key or imply cross-ecosystem verification of an HMAC with an undisclosed shared key. The portable format instead supports a SHA-256 hash chain and optional detached public-key signature. Hash chains show tampering relative to a trusted root; they do not prove authorship or truth.

## 6. Implementation status and limits

Shared schemas, synthetic fixtures, RFC 9162 inclusion-proof verification, SHA-256 audit-chain verification and semantic negative tests are implemented on the proposal branch. No security scanner, proxy, eBPF module, OpenShell runtime, Sentry DPU, package scanner, red-team engine, SBOM generator, or signature service is installed or invoked. Public examples use synthetic references only.
