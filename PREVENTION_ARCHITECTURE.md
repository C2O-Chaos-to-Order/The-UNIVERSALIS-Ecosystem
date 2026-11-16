# UNIVERSALIS Prevention Architecture

**Date:** 2026-11-12 | **Inventory:** Twenty-first owner-supplied toolchain inventory  
**Boundary:** Publicly reusable schemas, synthetic fixtures and source references only. No private C2O policy, incident records, signing keys, device identities or authority tokens.

## Governing principle

**Safety is an external, layered, measurable boundary—not a claim made by the agent about its own intentions.**

“Prevention of bad and evil in total” is a design objective, not a guarantee that any stack can eliminate all harm. Prevention systems have residual false negatives, false positives, gaps in tool/event coverage, model drift, policy errors, compromised hosts and human-process failures. UNIVERSALIS must disclose these limits, measure them, test them adversarially and preserve independent controls.

A moderation model, red-team scanner, governance dashboard and hardware kill switch are different instruments:
- **Moderation/guardrails** assess inputs, retrieved context, dialog, tool calls/results and outputs.
- **Runtime enforcement** decides whether an operation may execute and blocks it outside the agent's prompt.
- **Governance/GRC** tracks system inventories, risks, controls and evidence; it does not necessarily intercept execution.
- **Red-team tools** discover vulnerabilities under authorized scope; they do not automatically mitigate them.
- **Containment systems** pause, revoke, isolate or terminate workloads through an independent control plane.

## Open prevention tool candidates

### Runtime guardrails and action controls

| Project | Verified role | Maturity and limits |
|---|---|---|
| laya-guard | Local pre-execution shell/file command screening; allow/review/block | MIT project with local model and regex; ~85–90 ms and benchmark figures are project-reported. Some test sets are explicitly regression-only. Hook support differs by agent. |
| Sponsio | Action-contract checks before tool calls, including temporal/action-sequence rules | Package inspected at 0.2.0a21; prerelease. Pin exact revision, review security history and independently retest every host hook. |
| NeMo Guardrails | Configurable input, retrieval, dialog, execution/tool and output rails | Open-source framework; all five rails are not automatically enabled in every deployment. Active configuration determines coverage. |
| LlamaFirewall | Scanner framework including PromptGuard, AlignmentCheck, CodeShield and regex | Open scanner composition; model/framework defenses do not substitute for OS, network or credential enforcement. |
| HOL Guard | Local-first protection for shell/file access, packages, MCP servers/tools, plugins and skills | Apache-2.0, package inspected at 3.59.0; production-stable project metadata. Actual coverage depends on integration hooks/proxies and their documented failure behavior. |
| Universal Poison Armor | MCP-oriented input normalization, prompt-injection and dataset-anomaly defense | MIT source project; claims require independent evaluation against current attacks and actual retrieval/pipeline integrations. |

### Constitutional governance and GRC

- **arifOS:** model-independent constitutional MCP kernel with declared thirteen floors and verdicts. Its current repository also exposes the distinction between self-measurement and independent audit: generated README material records unresolved floor, actor-binding and receipt-fidelity issues. Do not treat it as independently validated authority until those gaps are resolved.
- **Charter:** exact product/repository supplied was not pinned to an authoritative source; unresolved.
- **RAI Toolkit:** ambiguous name; do not conflate it with Microsoft's Responsible AI Toolbox, NIST AI RMF or another project without exact identity.
- **VerifyWise:** AI system inventory, assessments, policy/evidence and framework mappings. New releases use a Community & Evaluation License; company use beyond the stated evaluation period requires commercial licensing. Governance/GRC is not pre-execution enforcement.

### Red-teaming and adversarial testing

- **garak (Apache-2.0):** LLM vulnerability scanner with static, dynamic and adaptive probes for data leakage, prompt injection, misinformation, toxicity and jailbreaks.
- **Promptfoo (MIT):** CLI/library for model/application evaluation and red-teaming with CI/CD integration. Current site states the project is now part of OpenAI and remains open source.
- **AgentRed (MIT):** local-first authorized red-team workbench with scope/risk gates, tool gateway, evidence and human review. Its own maturity note describes a platform kernel/workbench, not a finished commercial SaaS.
- **Agent Reliability Lab:** a name/organization exists, but the supplied agent-specific red-team product identity was not pinned. Unresolved, not a verified control.
- **RedPanda Security / Fusion Safety:** no authoritative public implementation/release and independent judging evidence pinned; unresolved vendor/product candidates.

### Specialized child safety, fraud and CBRN evaluation

- **paxmod-guard:** package documentation describes a CPU-local moderation model after an initial model download, with about 1 GB RAM and no subsequent network calls. Specialist classifier, not a complete safeguarding program.
- **SENTINEL:** behavioral child-safety moderation focused on interaction trajectory. Its current license is custom source-available with revenue and hosted-service restrictions, not unrestricted Apache-2.0 open source. Performance claims need independent reproduction and human safeguarding procedures.
- **Gonzih/parental-control:** MCP proxy that asks an agent to invoke message checks before and after responses, with guardian notifications/approval. Not an out-of-band enforcement boundary if the agent can skip the tool call.
- **merchantguard-sentinela:** exact public implementation/release not pinned; unresolved.
- **AgentVault:** located implementation describes a hackathon sandbox with synthetic invoices, bank-change and human-verification examples; not a deployed payment firewall.
- **OpenFraud (MIT, v0.1.0 Alpha):** forensic mathematics, ML and graph-analysis prototype; not a production fraud decision authority.
- **CBRN safeguards review prototype:** current repository explicitly says synthetic-data demonstration only and must not be used for operational safety, security, intelligence, emergency response or threat assessment.

### Sovereign-runtime references

NVIDIA's September 28, 2026 Open Agent Safety Platform combines **OpenShell** (open-source runtime sandbox and policy enforcement) and **Sentry** (BlueField-4 out-of-band hardware monitoring/enforcement reference design). OpenShell can run without BlueField-4; Sentry adds a hardware-isolated layer when supported hardware and real traffic-path coverage exist. Treat millisecond quarantine as a vendor claim until tested in the actual deployment.

Prediction Guard documents an in-boundary control plane for Azure tenant/VPC/GovCloud/on-prem/edge with per-agent identity, runtime policy, budgets and pause/scope-down/revoke. It is a commercial vendor candidate whose claims require deployment and contractual verification. Deliverance AI and TRUSTNOW were not pinned to authoritative implementation details in this review.

## Portable Prevention contracts implemented

The public v1 schema defines eight record families:
1. **Harm taxonomy mapping:** source namespace, version, maturity and category cross-references.
2. **Constitutional-floor profile:** prohibitions, least privilege, human veto, evidence integrity, auditability and external containment. Agents cannot modify the floor.
3. **Enforcement receipt:** exact action/policy/constitution/taxonomy, pre-execution decision, floor outcomes, fail mode, evidence references and Ed25519 signature.
4. **Harm-reduction evaluation:** attack/benign denominators, baseline/defended harmful outcomes, false-positive rate, repeated seeds and 95% Wilson intervals.
5. **Red-team finding:** authorized scope, taxonomy, reproducibility, severity, lifecycle and sanitized evidence.
6. **Containment attestation:** independent control substrate, action, confirmation/read-back, external verifier and human-controlled release.
7. **Coverage attestation:** tested/enforced layers, bypass attempts/successes, untested surfaces and guard-unavailable behavior.
8. **Case escalation:** harm domain, severity, authorized recipient, evidence digest and privacy-minimized escalation.

A signed DSSE-independent Ed25519 synthetic receipt is verified by the validator against an ephemeral test key; that key is not a production trust anchor.

## Taxonomy and legal reference versions

The taxonomy package preserves maturity/version metadata:
- **OWASP Top 10 for LLM Applications 2026** and **OWASP Top 10 for Agentic Applications 2026** are security awareness/threat frameworks, not certifications.
- **OWASP MCP Top 10** is treated as a living/beta taxonomy until its release status is checked against the project's current release.
- **MITRE ATLAS** is a living knowledge base of adversary tactics and techniques involving AI systems, not a compliance standard.
- **EU AI Act Article 5** is mapped to consolidated Regulation (EU) 2024/1689 as amended in 2026. The European Commission AI Act Service Desk notes later application dates for newly inserted prohibitions, including 2 December 2026 for two provisions. A taxonomy mapping is not a legal opinion or compliance attestation; use authentic Official Journal text and check application dates.

## Source review and adoption limits

- **laya-guard (MIT):** local pre-execution screening, 11-agent adapters and a 322M multilingual model according to the project; benchmark numbers are project-reported and some sets are regression tests: https://github.com/scs0209/laya-guard.
- **Sponsio (Apache-2.0; 0.2.0a21 prerelease):** checks tool calls against runtime contracts and action history. Release notes discuss findings/fixes from earlier alpha versions; verify exact release and retest integrations: https://github.com/SponsioLabs/Sponsio and https://pypi.org/project/sponsio/.
- **NeMo Guardrails:** five configurable rail types; actual active sequence is configuration-dependent: https://docs.nvidia.com/nemo/guardrails/latest/about/rail-types.html.
- **LlamaFirewall:** modular scanner architecture in Meta PurpleLlama including PromptGuard, AlignmentCheck, CodeShield and regex: https://github.com/meta-llama/PurpleLlama/tree/main/LlamaFirewall.
- **EuroSafeGuard:** recall and harmful-reply reduction figures are specific to test sets, seeds and high-compute configuration; project materials also report seed variation. Not a universal prevention guarantee: https://github.com/EuroSafeAI/EuroSafeGuard and https://guard.safe.eu/paper.
- **HOL Guard (Apache-2.0; 3.59.0):** local-first control for shell/files/MCP/package/skills; event coverage and failure behavior vary by integration: https://github.com/hashgraph-online/hol-guard.
- **Universal Poison Armor (MIT):** source describes multiple poisoning/prompt-injection defenses; independent testing and RAG integration review are required: https://github.com/mzaid007/Universal-Poison-Armor.
- **arifOS (AGPL-3.0):** thirteen-floor kernel and ledger are project-described. README generated state differentiates self-measurement from independent audit and identifies unresolved issues; not independently verified as a complete sovereign authority plane: https://github.com/ariffazil/arifOS.
- **VerifyWise:** current repository uses VerifyWise Community & Evaluation License 1.0 for new releases; corporate use beyond stated evaluation period requires commercial licensing. GRC is not action blocking: https://github.com/verifywise-ai/verifywise.
- **garak (Apache-2.0):** LLM vulnerability scanner and probing framework, not production runtime enforcement: https://github.com/NVIDIA/garak.
- **Promptfoo (MIT):** local CLI/library for evals and red-team workflows with CI/CD; current site states it is part of OpenAI and remains open source: https://github.com/promptfoo and https://www.promptfoo.dev/about/.
- **AgentRed (MIT):** local-first authorized workbench with scope/risk/tool gates, evidence and human review; its maturity note describes an unfinished workbench/platform kernel: https://github.com/Coff0xc/AgentRed.
- **PaxmodGuard:** package docs describe local CPU checks after first model download and about 1 GB RAM; validate age-appropriate performance and false positives/negatives independently: https://www.paxmod.com/docs/paxmodguard.
- **SENTINEL:** current custom license has revenue and hosted-service restrictions; source-available, not unrestricted open source. Behavioral-detection claims are project claims pending independent review: https://github.com/sentinel-safety/SENTINEL/blob/main/LICENSE.
- **Gonzih/parental-control:** public MCP pre/post message checks depend on the client/agent invoking them; not independent external enforcement: https://mcprepository.com/Gonzih/parental-control.
- **AgentVault:** local hackathon sandbox using synthetic invoice/bank-change demos, not verified payment production infrastructure: https://github.com/luxinlabs/AgentVault.
- **OpenFraud (MIT, Alpha):** framework marked Alpha in package metadata and requires substantial infrastructure; not production-validated fraud prevention: https://github.com/Veedubin/openfraud.
- **CBRN safeguards review prototype:** synthetic data only and explicitly not for operational use: https://github.com/EODTrip2026/cbrn-safeguards-review-evaluation.
- **GuardianClaw:** inspected public GuardianClaw platform is a web/API cognitive flow builder; current inspected source did not verify the supplied robotics/ISO TS 15066 or benchmark claims: https://github.com/guardianclaw/guardianclaw-platform.
- **NVIDIA Open Agent Safety Platform (September 28, 2026):** OpenShell + Sentry/BlueField-4; hardware enforcement requires deployment path coverage: https://nvidianews.nvidia.com/news/open-agent-safety-platform and https://developer.nvidia.com/blog/nvidia-open-agent-safety-platform-a-reference-for-continuous-in-silicon-agent-monitoring/.
- **Prediction Guard:** product/marketplace documentation describes in-boundary deployment, action controls, identity, budgets and intervention. Vendor claims pending security and deployment testing: https://predictionguard.com/ and https://marketplace.microsoft.com/en-us/product/predictionguard1770129613213.prediction-guard.
- **Charter, RAI Toolkit, TELOS, Operator Lite, RedPanda Security, Fusion Safety, Agent Reliability Lab as the described red-team product, merchantguard-sentinela, Deliverance AI and TRUSTNOW:** exact source/release identity or independent evidence not pinned; unresolved.

## Non-claims

No package was installed or run; no actual agent action was intercepted; no child-safety, CBRN, fraud or security case was evaluated; no production kill switch was tested; and no private C2O data was accessed. CI validates synthetic record semantics, computed metrics and a disposable signature only. It does not prove zero risk, legal compliance, perfect moderation, unbiased detection, complete coverage, production containment or incident-response adequacy.
