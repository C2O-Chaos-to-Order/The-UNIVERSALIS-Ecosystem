# Divergence Detection and Reconciliation — UNIVERSALIS Open Architecture

**Date:** 2026-11-12  
**Status:** Open architecture and portable contract foundation; candidates remain proposed pending independent verification.

## 1. Scope and principles

Divergence is a family of related but non-identical measurements: behavioral trajectories, configuration/infrastructure state, schema/data shape, policy clauses, ontology semantics, federated identity, embedding/RAG retrieval, and reconciliation conflicts.

UNIVERSALIS provides open, inspectable, independently operable tools and portable contracts. Its shared reports must not depend on C2O, contain C2O baselines or incident data, or encode private authority tokens. A JSON shape is not evidence that different metrics are comparable. Every report therefore carries its domain, metric definition, units, normalization version, cohort/window, uncertainty and comparability limitations.

## 2. Candidate tools and verification notes

All candidates require exact source/version/license/security/data-flow checks before adoption.

### 2.1 Behavioral / trajectory divergence

- **TraceFork** — 2026 EMNLP demo paper on paired GUI-agent trajectory alignment and divergence visualization. The reported dataset comprises 1,722 tasks and 1,387 aligned pairs; median 45.5 ms and F1 0.910 apply to the paper's described evaluation. [ACL Anthology](https://aclanthology.org/2026.emnlp-demos.15/).
- **Praxen** — read-only Worker Remit vs observed-evidence verifier; emits HTML/JSON/text. It complements, but does not replace, runtime monitoring. [GitHub](https://github.com/open-agent-ai-security/praxen).
- **AlignmentCheck (LlamaFirewall)** — open-source semantic/few-shot reasoning audit for goal hijacking and prompt-injection-induced misalignment; probabilistic guardrail, not proof. [Meta research](https://ai.meta.com/research/publications/llamafirewall-an-open-source-guardrail-system-for-building-secure-ai-agents/).
- **driftbase** — agent behavior fingerprinting, 12 weighted dimensions, confidence intervals and cost analysis. Vendor materials refer to EU AI Act Articles 9 and 12, not Article 72. Its own documentation says the score measures behavioral difference, not quality. [Product](https://driftbase.io/), [score](https://driftbase.io/docs/drift-score-reference).
- **SEISMOGRAPH** — Page-CUSUM plus DP aggregate metrics and quorum. The 38-day result is a seeded synthetic backtest, not a real historical detection; the public network currently lacks three independent observers. [GitHub](https://github.com/Tania-coder/SEISMOGRAPH).
- **agentdrift** — quality-drift candidate; exact upstream and judge calibration require pinning.
- **Shadow** — supplied .agentlog/nine-axis/LASSO capabilities were not matched to a canonical upstream in this review; unresolved.
- **Hodoscope** — LLM summaries and embeddings produce interactive trajectory maps; model/provider data flow matters. [GitHub](https://github.com/AR-FORUM/hodoscope).
- **Arbiter** — research paper on budget-aware monitoring of multi-agent conversations; not production certification. [arXiv](https://arxiv.org/abs/2606.10747).
- **Agent Behavioral Contracts** — formal drift-score research reference combining compliance gap and Jensen–Shannon divergence; assumptions and implementation need further validation. [Research locator](https://www.researchgate.net/publication/401211575_Agent_Behavioral_Contracts_Formal_Specification_and_Runtime_Enforcement_for_Reliable_Autonomous_AI_Agents).
- **AEBA** — IETF individual Internet-Draft defining event/sequence behavior monitoring and signed signals. Weights remain implementation-defined; not an RFC. [Datatracker](https://datatracker.ietf.org/doc/draft-sharif-aeba/).

### 2.2 Configuration and infrastructure drift

terraship; DriftSentry; tfdrift; cloudrift; stackdrift; driftmgr.

Verified distinctions:
- tfdrift (sudarshan8417) is a Terraform scan/report/auto-remediation CLI. It is not assumed to be the only project named tfdrift. [GitHub](https://github.com/sudarshan8417/tfdrift).
- cloudrift is an AWS-focused pre-apply Terraform plan/live-state and OPA policy tool, not a general multi-cloud drift engine in its current README. [GitHub](https://github.com/inayathulla/cloudrift).
- stackdrift handles CloudFormation property-level drift. [PyPI](https://pypi.org/project/stackdrift/).
- driftmgr (catherinevee) documents AWS/Azure/GCP/DigitalOcean infrastructure drift and remediation. [GitHub](https://github.com/catherinevee/driftmgr).
- terraship's surfaced source was a beta VS Code marketplace extension; DriftSentry's canonical upstream was not resolved. Do not adopt the broader supplied claims until pinned. [Marketplace](https://marketplace.visualstudio.com/items?itemName=Terraship.terraship-vscode).

### 2.3 Schema and data drift

Flyway Community drift checks; sqldrift; saropa_drift_advisor; gcfm.

Flyway distinguishes history validation from live schema comparison and has flow-specific semantics. [Docs](https://documentation.red-gate.com/flyway/flyway-concepts/drift-analysis). Saropa Drift Advisor is a debug-focused Dart/Flutter SQLite/Drift inspection tool with schema diff and migration preview; it is not a generic production data-drift engine. [Package](https://pub.dev/packages/saropa_drift_advisor). Exact sources/features for sqldrift and gcfm need pinning.

### 2.4 Policy divergence

Risk Cognizance; PolicyIQ; Semantic Consensus Framework (SCF).

Risk Cognizance advertises policy-drift detection and AI Governance support across ISO 42001, NIST AI RMF and EU AI Act; vendor descriptions are not certification evidence. [Product](https://riskcognizance.com/product/ai-governance-grc-software). PolicyIQ's 91.6% precision is target performance on a controlled synthetic corpus in an October 2026 paper, not independently reproduced production accuracy. [Zenodo](https://zenodo.org/records/23133813). SCF's canonical upstream/specification remains unresolved.

### 2.5 Semantic and ontological divergence

OntoLDiff; owlcompare; open-ontologies alignment; OnDeT.

- owlcompare v0.1.0 currently provides syntactic/structural comparison; inferential and impact layers are planned. [GitHub](https://github.com/Ajala111/owlcompare).
- open-ontologies is MIT/Rust/Oxigraph/SQLite/Lean tooling. Tie seven-signal alignment claims to the pinned repository paper/release. [GitHub](https://github.com/fabio-rovai/open-ontologies).
- OntoLDiff and OnDeT upstreams remain unresolved. Logical-difference completeness via Uniform Interpolation depends on the supported logic/profile and proof conditions.

### 2.6 Identity and federation divergence

- sm-divergence implements the current October 2026 individual IETF Internet-Draft draft-chandra-agent-registry-corroboration-02, paired with sm-resolver. The cited draft maps to versions 0.12.0 and 0.7.0. It covers present/absent/error observations, source/vantage comparison, propagation delay and signed Corroboration Records. It is an individual Internet-Draft, not an adopted RFC. [IETF draft](https://datatracker.ietf.org/doc/draft-chandra-agent-registry-corroboration/02/).
- Federated-learning disagreement-resolution candidates require exact upstream, client isolation and privacy threat-model verification.

### 2.7 Embedding and RAG divergence

- ragdrift — Rust/Python five-dimensional RAG drift crate; pin versions and detector assumptions. [docs.rs](https://docs.rs/ragdrift/latest/ragdrift/).
- embspec and embspec-mcp — embedding/index compatibility and frozen-probe retriever stability. The 95–99% recovery at approximately 1% corpus re-encoding cost is a source-attributed result, not a guarantee. [Python](https://github.com/MukundaKatta/embspec), [MCP](https://github.com/mukundakatta/embspec-mcp).

### 2.8 Resolution and reconciliation

- Graph Merge — TypeGraph fork/branch/reconcile operation, with plan preview and explicit conflicts rather than silent overwrite. [Docs](https://typegraph.dev/graph-merge/).
- ConcordAI and Automated Codebase Reconciliation — exact canonical upstream and maturity unresolved.

## 3. Shared contract files

- schemas/divergence/divergence-contracts.v1.schema.json
- examples/divergence/divergence-fixtures.v1.json
- .github/scripts/divergence_contract.py
- .github/workflows/divergence-contract.yml

The schema defines three record types:
1. Behavioral-axis contract: metric definition/unit, normalized range, method, baseline cohort/window, uncertainty and comparability constraints.
2. Divergence report: domain, digested baseline/candidate references, comparison window, evaluator/ruleset, findings, axis scores and confidence intervals, optional identity observations and typed schema/policy/ontology/RAG details.
3. Signed attribution receipt: in-toto Statement v1 wrapped in DSSE; the signature binds report subject/digest, axis/domain, opaque actor reference, method, confidence, baseline and evidence digests.

Nine proposed behavioral axes are included: task outcome, policy compliance, tool sequence, tool selection, action rate, latency, error rate, capability use and resource cost. They are proposed portable definitions, not a claim to replicate a third-party axis taxonomy.

## 4. Safety, privacy and comparability

- Do not export raw baselines, traces, user prompts, incident details, cloud identifiers, private policy text, registry keys or private ontology stores.
- A digest is an integrity reference, not anonymization. Low-entropy private values must not be hashed and exported as a substitute for redaction.
- Keep score domains and units distinct. Do not compare a normalized behavior score to an ontology witness count or Terraform resource severity without explicit calibration.
- Preserve baseline window, cohort, sampling plan, model, embedding encoder, index manifest, schema/ontology profile, ruleset and evaluator versions.
- Statistical confidence intervals characterize sampling uncertainty; they do not prove causality.
- Actor attribution requires corroboration and complete identity/audit context. An LLM-generated root-cause hypothesis is not an attribution proof.
- Detection, attribution, adjudication and remediation are separate operations. Remediation needs human review and rollback.

## 5. Non-claims

No third-party candidate has been installed, benchmarked or certified. No live agent trace, production cloud account, database schema, policy corpus, ontology store, registry, vector index or C2O baseline was read. No remediation, model recall, rollback or incident action was performed. CI validates only synthetic contract records and a disposable test signature.
