# Disorder and Chaos Prevention Architecture

**Inventory:** 25th owner-supplied inventory — Disorder and Chaos Prevention  
**Date:** 2026-11-12  
**Status:** Public research architecture; candidate tools are not adopted by inclusion.

## Purpose

Disorder in agentic systems is a continuous reliability and governance concern. UNIVERSALIS provides inspectable fault-injection harnesses, stability measurements, replayable experiments and portable evidence contracts. Chaos engineering means bounded perturbation in an authorized test environment, not uncontrolled disruption. Public experiment records permit synthetic, isolated-test and staging targets only; production fault injection requires separate environment-specific authorization.

## Theoretical foundations and limits

The June 2026 Intelligence Entropy / ADE research proposes an operational entropy construct over output consistency, task accuracy and cross-session coherence. The earlier Silent Failure paper uses S(t)=S0·exp(alpha·t); the later ADE paper extends this to S(t,Cm)=S0·exp(alpha·t/Cm) and proposes a Lyapunov stabilization condition lambda>alpha/Cm. The ADE repository describes L0 as a meta-principle, L1–L4 as physical-constraint/organizational/execution/user-adaptation layers, and 23 core components.

These are author-proposed models and author-reported experiments, not accepted physical laws or independently reproduced guarantees. The exponential form needs an operationally defined state, time unit, system boundary, alpha-estimation procedure, capability coefficient and operating conditions. A weighted aggregate of accuracy, consistency and coherence is not Shannon entropy without a valid information-theoretic definition. Monotonic growth must be measured, not assumed.

A silent failure is an unexpected deviation without an externally surfaced trigger or reliable error signal; it is not causeless. Hidden state, scheduler guards, timing, persistence boundaries, tool routing, configuration drift or missed acknowledgements may be causal. Channel Fracture reports particular cross-agent delivery failures, not a universal law.

Controlled/Hedge/Chaos is retained as owner-proposed operational vocabulary: Controlled = within measured bounds; Hedge = degraded confidence/warning requiring verification or throttling; Chaos = declared invariant breach requiring containment. These are not natural physical phases. The CAAI public proof pack calls itself proof-of-origin and Phase-1.5 testing/validation, not a final product release.

Re_EOS, ECR, Oscillation Warning and variance throttling remain proposals until canonical definitions, units, calibration, falsifiable hypotheses and independent data are supplied. A Reynolds-like name does not establish equivalence to fluid mechanics. The Second Law of Intelligence is a separate 2025 research proposal defining ethical entropy over a finite goal distribution; it is not a thermodynamic law. ENTRO-DASA is a 2026 Zenodo research framework requiring independent implementation/replication. CAST is an arXiv vision and research agenda, not a deployed guarantee. Covenant Protocol/Ontological Locking and G.O.D Harmony remain unresolved pending primary specifications.

## Five-layer disorder taxonomy

| Layer | Working meaning | Observable examples |
|---|---|---|
| Communication | Channel fracture, delivery/acknowledgement failure | Missing acknowledgements, duplicate delivery, handoff failure |
| Cognition | Confidence/answer drift, unsupported inference | Repeated-task variance, citation mismatch, unsupported certainty |
| Structure | Orchestration/dependency/lifecycle breakdown | Deadlocks, retry storms, loops, orphaned agents |
| Knowledge | Memory/retrieval/provenance/continuity decay | Stale memory, retrieval miss, failed read/write |
| Normative | Deviation from declared policy/consent/action constraints | Scope violations, ignored constraints, approval drift |

An incident may span multiple layers. A layer describes symptom domain, not root cause; trigger type and cause status are recorded separately.

## Prevention and resilience candidates

| Function | Candidate | Qualification |
|---|---|---|
| Security chaos/invariant testing | agentic-chaos-security | Apache-2.0 v1, agentic-chaos/v1 format, reproducible faults, MCP proxy and multi-agent/A2A/AP2 examples. A green run only covers tested probes/targets/runs. |
| Deterministic test fault injection | pytest-agent-chaos | MIT, pre-1.0; transport interception is stack-specific, recovery heuristic does not prove semantic correctness. |
| Attack-to-regression | chaos-bringer | PyPI project describes attack → observe → judge → finding → regression → replay → CI; pin release/source/license. |
| Agent robustness | Flakestorm | Public GitHub project under Apache-2.0; chaos/adversarial mutations. OECD listing was not independently verified. |
| Infrastructure chaos | Chaos Monkey Agent | Public prototype uses LangGraph, Toxiproxy, Docker Compose and Kubernetes Operator; do not infer production readiness. |
| LLM-assisted chaos cycle | ChaosEater | Owner-supplied candidate; canonical maintained source and reproduction evidence unresolved. |
| MCP fault injection | MCP-Injector | arXiv 2610.32555: 1,350-cell study; a permanent-heavy profile reduced task-completion score 60% in tested settings—not a universal threshold. |
| Agent orchestration load | Swarmbreaker | PyPI 0.1.0; confidence-labelled knee points; explicitly not a model-quality benchmark. |
| Browser/network faults | ChaosBull | Public MIT MCP/Playwright project; pin version and constrain target. |
| Flight recorder/replay | Resilience Lab | Exact canonical source/release not established; unresolved. |
| Runtime gauges | llmosafe | MIT Rust project; project-specific classifier/OOV scores on 0–65,535 scale, not universal entropy units. |
| Cybernetic stability | ENTRO-DASA | Zenodo v1.0.0 research; convergence claims need independent tests. |
| Agent SRE | Agent SRE Governance | Draft spec in Microsoft Agent Governance Toolkit; not an industry standard. |
| Adaptive stability | RAFAEL | Package-index entry exists; canonical source/reproducible implementation unresolved. |
| Cross-domain phase stability | SCPN Phase Orchestrator | AGPL-3.0-or-later, 36 domain packs. Review-only by default; quantum/neuromorphic targets produce review artifacts and keep hardware writes disabled. |

## Corrections and acceptance limits

- ADE's earlier and capability-adjusted equations are different model versions; do not merge silently. Its 100K-scale experiments, 33.6-day monitoring, 69–98% channel-fracture baseline and below-0.02% system-death estimate are author-reported, not independent certification.
- llmosafe documents entropy as classifier probability × 65,535 and surprise as OOV ratio × 65,535. Its default thresholds are in that project-specific scale; the supplied 1,000/500 thresholds are not universal defaults.
- MCP-Injector's 60% degradation is specific to its permanent-heavy stress profile, two gpt-oss model sizes, three agent stacks and 25 tasks.
- FIRM Protocol gives successful agents more influence through Hebbian authority. That coordination model is not a source of human-defined C2O authority.
- NVIDIA Sentry's BlueField-4 "only path" claim applies to its documented reference topology. Each deployment must verify complete path coverage, bypass resistance and independent readback.
- OpenShell's dynamic network/provider controls differ from static Landlock filesystem and seccomp process controls, which require sandbox recreation. Landlock defaults to best_effort in current docs; fail-closed deployments must configure and verify hard_requirement.
- SCPN's domainpack inventory is not a safety case; review-only proposals and hardware writes are distinct.

## Portable contract model

The shared v1 schema defines six record families: disorder taxonomy profile; disorder event; bounded chaos experiment; stability receipt; containment attestation; and resilience index. Records bind the taxonomy/regime, trigger and cause status, target digest, fault classes, hypothesis, seed, safety preconditions, duration, cleanup, metric definition/unit/threshold/uncertainty, containment action/substrate/readback/signature state, and resilience numerator/denominator/formula/fault universe/confidence interval.

Every portable record has authority_effect = none. An absent or unverified signature is never described as signed. Resilience scores are comparable only when metric definitions, workload, sampling, fault universe and confidence method match.

## Safe experiment lifecycle

Declare an authorized synthetic/isolated/staging target; define a falsifiable hypothesis and invariants; bound fault class/intensity/rate/duration; verify credentials are synthetic, budgets and containment are ready; inject bounded faults; evaluate invariants, recovery, correctness and confidence separately; stop on scope escape, unexpected egress, containment failure, irreversible effects or budget breach; remove faults and verify cleanup by independent readback; record outcomes and promote confirmed findings to regression tests.

## Non-claims

No tool/runtime gauge/framework/hardware kill path is installed or adopted. No experiment was run, no external system was fault-injected and no hardware was actuated. Contract validation does not prove scientific validity, product correctness, production resilience or safety certification.

## Primary sources

- ADE: https://arxiv.org/abs/2606.18065 ; https://github.com/ADE-standard/intelligence-entropy
- Silent Failure: https://arxiv.org/abs/2606.08162
- Channel Fracture: https://arxiv.org/abs/2606.04896
- Second Law: https://arxiv.org/abs/2511.10704
- CAST: https://arxiv.org/abs/2506.03056
- CAAI: https://github.com/collapsefield/collapse-aware-ai-public-proof-pack
- ENTRO-DASA: https://zenodo.org/records/20353988
- agentic-chaos: https://github.com/RicoKomenda/agentic-chaos
- pytest-agent-chaos: https://pypi.org/project/pytest-agent-chaos/
- chaos-bringer: https://pypi.org/project/chaos-bringer/
- Flakestorm: https://github.com/flakestorm/flakestorm
- Chaos Monkey Agent: https://github.com/arec1b0/the_chaos_monkey_agent
- MCP-Injector: https://arxiv.org/abs/2610.32555
- Swarmbreaker: https://pypi.org/project/swarmbreaker/
- ChaosBull: https://github.com/Omkar2240/chaosbull-mcp
- llmosafe: https://github.com/moeshawky/llmosafe
- FIRM: https://pypi.org/project/firm-protocol/
- Agent SRE draft: https://github.com/microsoft/agent-governance-toolkit
- SCPN: https://github.com/anulum/scpn-phase-orchestrator
- NVIDIA Sentry: https://www.nvidia.com/en-us/networking/products/software/sentry/
- NVIDIA OpenShell: https://github.com/NVIDIA/OpenShell/blob/main/docs/security/best-practices.mdx
