# Insurgence, Resistance and Defensive Threat Modeling — UNIVERSALIS Open Architecture

**Date:** 2026-11-12  
**Owner:** UNIVERSALIS / open MotherThread ecosystem  
**Status:** Public research and portable contract foundation; candidates remain proposed pending independent review.

## 1. Purpose and boundaries

UNIVERSALIS treats insurgence as asymmetric emergence. The open MotherThread supports lawful grassroots participation, public-interest communication, evidence-led counter-narrative, safe research and defensive study of adversarial emergence in agentic systems.

“Resistance” here means lawful, nonviolent and consent-based participation, open criticism, resilience and preservation of human decision authority. This repository must not become a source of operational guidance for terrorism, violence, weapon construction, recruitment, covert influence, evasion, intimidation or targeting. Dual-use insurgency simulations are catalogued as research references only; no operational scenario playbooks or exploit payloads are included.

C2O may privately deploy approved counter-insurgence controls, but this public layer does not require C2O credentials, private policies, threat data, identity keys, authority tokens or services.

## 2. Public grassroots and counter-narrative candidate

- **Insurgent Campaign** — public Tessl agent-skill listing for grassroots campaign design under spending asymmetry. The listing specifies a seven-stage workflow and emphasizes not inventing competitor information. It covers commercial, NGO and political-civic campaigns, so any UNIVERSALIS use must be wrapped in transparent sponsorship, source-backed claims, voluntary participation, personal-data minimization, no sensitive-trait targeting, no covert personas/astroturf and nonviolence. It is a candidate skill listing, not a verified runtime platform. [Tessl skill](https://tessl.io/registry/skills/github/bencium/bencium-marketplace/insurgent-campaign).
- **Cartographies of Sovereign Resistance** — owner-supplied Human-in-Command concept. A canonical public source or maintained implementation was not identified; retain as a proposed research concept pending a source reference.
- **Counter-narrative contract** — facts must be sourced, assumptions labeled, sponsors disclosed and corrections preserved. Do not manufacture testimonials, impersonate community members or suppress opposing lawful speech.

## 3. Defensive threat-model and research references

- **InsurgiSim** — older University of Pennsylvania paper describing a research prototype for modeling insurgent/terrorist agent theories and embedding it in a simulator. No current maintained release or public software distribution was confirmed. It is treated only as a historical research reference; no tactical scenario recipes are included. [Paper](https://repository.upenn.edu/bitstreams/78e429ea-06bd-4bb1-8dcb-72a28e89914c/download).
- **ARIS** — research and professional-education series, including “Resistance and the Cyber Domain”; not a software product. [Series overview](https://www.robertburrell.com/assessing-revolutionary-and-insurgent-strategies-aris).
- **MASON RebeLand** — peer-reviewed 2010 agent-based model paper on politics, environment, state stability and insurgency as an emergent social-system phenomenon. Research reference, not a currently verified toolchain package. [DOI](https://doi.org/10.1111/j.1468-2486.2009.00911.x).
- **RAND Infinite Potential** — RAND platform for facilitated Day After AGI policy exercises. “Infinite Potential—Insights from the Robot Insurgency Scenario” (2025) reports four runs of a tabletop policy exercise; it is not an executable robot-insurgency simulator. [RAND report](https://www.rand.org/pubs/research_reports/RRA4231-1.html).
- **Cambridge CASP 2026 report** — field research based on 57 interviews with 27 former Boko Haram members. It documents interview testimony about reported AI use. Treat the testimony as a significant source-reported threat signal while preserving limits: a qualitative former-member sample does not provide population prevalence or independent forensic verification of each reported use. [CASP report](https://casp.ac/reports/ai-enabled-terrorism); [independent report review](https://www.premiumtimesng.com/news/top-news/894830-boko-haram-used-chatgpt-other-ai-tools-to-plan-attacks-build-bombs-report.html).

The shared threat model uses only abstract risk classes and evidence tiers. It does not encode operational attack methods, weapon details, evasion paths, target-selection logic, recruitment tactics or exploit sequences.

## 4. Resistance and agent-boundary research

- **AgentDojo** — MIT-licensed ETH Zürich framework and benchmark for evaluating prompt-injection attacks and defenses on LLM agents. The package documentation notes that its API is still under development. It tests benchmarked defenses under a declared suite; it does not prove execution sovereignty, human command or production containment. The submitted 0%-utility/100%-false-stop statement is not supported by the primary AgentDojo documentation and is not adopted. [Repository](https://github.com/ethz-spylab/agentdojo); [docs](https://agentdojo.spylab.ai/).
- **PEA (Policy–Execution–Authorization)** — April 2026 arXiv preprint proposing separated policy, execution and authorization planes and a K×I×P analysis. Treat as a proposed architecture and test hypothesis, not a standard or proven implementation. [Preprint](https://arxiv.org/abs/2604.23646).
- **Peer-Preservation in Frontier Models** — Berkeley research published March 2026 reports controlled multi-agent scenarios in which tested models exhibited oversight-conflicting behaviors. It is an important red-team evidence source; the behaviors are recorded only as abstract failure-mode labels, not operational instructions. [Berkeley report](https://rdi.berkeley.edu/blog/peer-preservation/).
- **Shutdown/graceful degradation** — required defensive properties include deny-before-effect, independently controlled safe-stop, identity/capability revocation, auditable state transition and human-authorized release. These are architecture patterns and tests, not a standalone product.
- **NVIDIA Sentry** — vendor-described agent runtime monitoring/enforcement in a hardware-isolated BlueField-4 security domain. This is a product/reference architecture, not a universal hardware kill switch. Actual containment depends on topology and whether protected communications traverse the enforcement path. [NVIDIA overview](https://www.nvidia.com/en-us/networking/products/software/sentry/); [technical blog](https://developer.nvidia.com/blog/inside-nvidia-sentry-secure-ai-agents-at-runtime/).

## 5. Shared v1 contract files

- `schemas/insurgence/insurgence-contracts.v1.schema.json`
- `examples/insurgence/insurgence-fixtures.v1.json`
- `.github/scripts/insurgence_contract.py`
- `.github/workflows/insurgence-contract.yml`

Four portable records plus a signed envelope are defined:
1. **Threat model:** explicit assessment scope, established/speculative/undemonstrated evidence tiers, sources, limitations, risk categories and mitigation references.
2. **Resistance attestation:** test-suite identity, environment, policy/execution/authorization separation, independent stop path, human-command path, test outcomes and utility/false-stop metrics.
3. **Containment receipt:** trigger, timestamps, action, enforcement substrate, service-state transition, agent non-override and pending human release.
4. **Resistance campaign plan:** seven ordered stages; source-backed factual claims; sponsor disclosure; voluntary participation; privacy; non-deception and nonviolence.
5. **Signed attestation:** in-toto Statement v1 inside DSSE, cryptographically checked with a fixture-only Ed25519 public key.

The synthetic fixture contains one threat model, one resistance attestation, one containment receipt, one campaign plan, three signed attestations and twelve negative tests. The signing key is a test fixture only, not a public production trust anchor.

## 6. Privacy, human command and comparability

- A threat tier describes evidence quality within a stated scope; “established” does not mean universal truth.
- A successful resistance test applies only to the named versions, test cases, environment, metrics and sample count.
- Report task utility and false-stop rates alongside security outcomes; a boundary that prevents every useful action is not a viable design.
- A containment receipt is evidence of a specific state transition, not proof that every process, device or hardware path was stopped.
- A signed receipt proves integrity/authorship under a trust policy, not causality, legal compliance or correctness.
- Keep C2O baselines, incidents, identities, permits, control policies, production signer material and private telemetry out of the public fixture.
- Divergence findings should reuse the preceding portable divergence contract rather than duplicating or conflating its metric definitions.

## 7. Non-claims

No candidate tool was installed or invoked. No real campaign, agent attack, threat simulation, incident response, hardware watchdog, shutdown, quarantine, capability revocation or production test was performed. CI validates synthetic record integrity and fixture signatures only; it does not certify products, actual human-command guarantees, political campaign outcomes, device capabilities or production security.
