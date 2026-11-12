# UNIVERSALIS Eight-Stratum Capability Architecture

**Inventory:** 23rd owner-supplied toolchain inventory — Eight-Stratum Capability Ladder  
**Date:** 2026-11-12  
**Role:** UNIVERSALIS MotherThread — open, inspectable and independently operable instruments.  
**Status:** source inventory and portable contract prototype; no candidate is adopted merely by appearing in this document.

## 1. Architectural meaning of the ladder

The strata are **Base → Meta → Super → Hyper → Ultra → Magic → Quantum → Transformative**. They organize the dominant capability and integration level, not product quality, maturity, permission, autonomy, intelligence, or authority. A component may span several strata; its primary placement is an inventory aid, not a capability ceiling. A tool in a higher stratum does not receive broader authority by virtue of its classification.

| Stratum | Governing principle | Open / inspectable candidates and status |
|---|---|---|
| **Base** | Foundational substrate and primitives: OS/runtime, sandbox, memory and identity state, interface foundations | **OpenShell** (Apache-2.0; now a CNCF Sandbox project; local policy-enforced sandbox reference); **Stoa** (Apache-2.0 local-first knowledge graph/wiki with MCP); **Tur** (MIT, public Alpha, persistent structured agent state and MCP); **Omnigent** as a substrate/orchestration boundary where it spans Base/Meta. **OpenQuantum** is a commercial quantum platform/SDK and job service, not an open-source all-in-one workspace. **khy-os** is source-available with commercial restrictions, not OSI-open source. **Alexandria** remains unresolved pending exact source/release. |
| **Meta** | Orchestration above individual agents: harnesses, delegation, policy, fleet supervision and session continuity | **Omnigent** (Apache-2.0, Alpha meta-harness; it is an independent project, not established as a Databricks product); **Qualixar OS** (the current repository describes 13 topologies and 25 CLI commands; project claims require source/release pinning and independent test); **MetaMCP** (MIT MCP aggregation/gateway; branch and maintenance direction need pinning). |
| **Super** | Long-horizon agent frameworks: planning, execution, memory, delegation and bounded initiative | **DeepSeek Super-Agent** (`LofiSu/deepseek-super-agent`, MIT) is an independent implementation inspired by public DeepSeek material, not an official DeepSeek product. **SuperAGI** (MIT; historical open framework with comparatively stale release activity); **SuperAgentX** (MIT; Python agent framework with human-approval and audit features per upstream README); **SwarmClaw** (MIT; self-hosted multi-agent runtime, persistent memory, schedules and MCP; provider counts are version-sensitive). |
| **Hyper** | Executable tool composition: model-visible composed programs over existing tools | **HyperTool** is a 2026 research-paper proposal for code-block invocation over tool schemas. Paper-reported Qwen3 benchmark gains are experiment-specific, not general accuracy guarantees; a maintained canonical product release was not pinned. **Hyper by ASI Flow** is a commercial/cloud software-engineering platform, not an open-source implementation or an assumed customer-owned runtime. |
| **Ultra** | Frontier models and policy-aware routing | **Nemotron 3 Ultra**: NVIDIA reports 550B total / 55B active parameters. **open-ultra** (Apache-2.0) is a self-training routing proxy using shadow execution and grading; its live-work shadow lane creates a data-egress review requirement. **Muse Spark Open** is an open-weight 816B / 42B-active model under Meta's Muse Model License, not an unrestricted OSI open-source release; full BF16 weights are about 1.65 TB and NVFP4 about 537 GB, before runtime/activation/KV-cache overhead. |
| **Magic** | Natural-language application generation: turning intent into inspectable software artifacts | **Magic** (`polterguy/magic`, MIT) is a self-hostable full-stack app/agent generation platform with Hyperlambda and an MCP surface. **SuperMagic** (`dtyq/super-magic`) belongs to the Magic product family and is under a Magic open-source license derived from Apache-2.0 with additional restrictions; do not describe it as an unrestricted Apache-2.0 release. **Magetools** is unresolved pending a canonical source/release. |
| **Quantum** | Quantum-classical integration: circuit authoring, simulation, emulation, QPU submission and measurement | **Pasqal Neutral-Atom Agentic Toolkit** (`pasqal-io/agent-marketplace`) documents idea/specification → Pulser implementation → emulation → human-approved shot quote → QPU submission → analysis; physical QPU access is remote and costed. **TensorCircuit-NG** (Apache-2.0) is an open quantum-classical simulation/research framework; ORBIT-Q is a project benchmark, not a universal standard. **Qiskit Machine Learning** (open source); **QuOptuna** (Apache-2.0 quantum/classical AutoML); QuTiP and Qiskit are separate projects, not proof of one unified OpenQuantum distribution. **Classiq MCP** is a vendor integration candidate, not a general open protocol. |
| **Transformative** | Systemic applications spanning robotics, scientific research, and critical infrastructure | **Isaac Lab 3.0** (open-source robotics learning framework); **Isaac Lab-Arena 0.3** (Apache-2.0 Alpha benchmark/policy-evaluation framework; upstream explicitly says not for production and Isaac Sim dependencies have separate proprietary terms); **DORA Community Edition** (Apache-2.0 research-outline/drafting assistant, not an autonomous end-to-end laboratory); **ETRI Tango** (announced as an open-source no-code AI-integrated development tool on 2026-11-09; exact public source/release still needs pinning). **GR00T 2** was announced by NVIDIA but source availability was scheduled for December 2026; it is not treated as released on 2026-11-12. Muse Spark Open also spans Ultra/Transformative use cases but remains the model listed above. |

## 2. Interoperability is role-specific

The shared contracts intentionally distinguish:

- **MCP:** client-to-server tool, resource and prompt interaction; it is not, by itself, an agent-to-agent delegation standard.
- **A2A:** agent-to-agent discovery, task collaboration and artifact exchange (A2A v1.0.0).
- **ACP:** an agent-client protocol, not the agent-to-agent protocol.
- **OCI images:** portable container artifacts; an OCI-compatible image does not prove compatible kernel, accelerator, hardware, policy, runtime or hypervisor behavior.
- **Agent Skills / `SKILL.md`:** a skill-artifact format, not a transport protocol or execution authorization.
- **OpenAI-compatible APIs:** inference wire compatibility, not model equivalence, routing policy, data residency or sovereignty.
- **OpenQASM / Qiskit QPY / PennyLane / Cirq:** distinct circuit representations and serialization ecosystems. A bridge or export profile must be tested; the names do not establish universal circuit equivalence.
- **ROS 2 / robot action schemas:** control and message interfaces, not a safety certification or physical actuation grant.
- **Hyperlambda, JSON-LD and `SOUL.md` / `IDENTITY.md`:** project or ecosystem formats/conventions; they are not asserted here as universal standards for every application or agent identity.

Compatibility status is `not_tested` until a defined profile, producer/consumer versions, fixtures, round-trip tests and failure behavior are recorded.

## 3. Portable contracts implemented

`schemas/strata/stratified-capability-contracts.v1.schema.json` provides fourteen record families:

1. `stratum_profile` — canonical order, principle and boundary rule.
2. `component_manifest` — component class, source, license, maturity, deployment mode, interface and limitations.
3. `interoperability_profile` — protocol role, producer/consumer, capability set and conformance evidence.
4. `orchestration_session` — participating agents, harness, policy/sandbox references and cross-device status.
5. `lifecycle_event` — bounded agent lifecycle transition.
6. `proactive_action_receipt` — trigger, risk, scope and approval outcome.
7. `composition_contract` — code, tool-schema, static-analysis, runtime-policy and sandbox digests.
8. `composition_execution_receipt` — tool invocations, trace, result and Ed25519 evidence signature.
9. `model_route_decision_receipt` — selected model/provider, sovereignty classification, cost, latency and egress decision.
10. `application_provenance_receipt` — intent/source/dependency/runtime digests, tests and publication approval reference.
11. `quantum_execution_receipt` — circuit, backend, emulation, cost/shot quote, human approval, job and result evidence.
12. `robot_policy_evaluation` — policy, embodiment, action schema, benchmark and sim-to-real evidence; never actuation authority.
13. `sovereign_deployment_attestation` — residency/egress, isolation, hardware-root and independent-verifier evidence; cannot self-certify compliance.
14. `evidence_claim` — source-bounded claim, verification status, reviewer and limitations.

The shared fixture is synthetic and deliberately unsigned: the composition receipt has `signature: null` and `signature_verification: not_present`. The schema defines an Ed25519 receipt envelope, but this fixture does not contain or verify a signature. Production signing and trust-anchor operations remain unimplemented.

## 4. Acceptance gates by stratum

A candidate is not accepted solely because its README says open, sovereign, safe, self-hosted, deterministic or production-ready. Require the exact canonical source, version, license, SBOM, dependency/egress profile, deployment modes, supported interfaces, positive and negative tests, failure behavior, provenance and independent validation appropriate to the claim.

- Base/Meta/Super/Hyper: verify sandbox enforcement outside model control, capability scopes, session/lifecycle transitions, spend/compute ceilings, revocation, composition preflight and runtime enforcement. Static analysis alone cannot secure a composed program.
- Ultra: bind routing to an explicit provider allowlist, sovereignty class, egress approval, local/remote distinction, cost ceiling and route receipt. Local inference only stays local when model serving, telemetry, moderation, logging, embeddings and tools also avoid unapproved egress.
- Magic: retain generated source, dependency lock/SBOM, build environment, test results and human publication approval. Natural-language intent is not an executable specification or correctness guarantee.
- Quantum: emulate before QPU use; bind circuit/backend/shot count/quote; require human approval before billable submission; preserve raw measurement provenance and calibration/date metadata. A simulator result is not a QPU result.
- Transformative: robotics needs independent policy evaluation, sim-to-real evidence, domain safety case, hardware interlocks and separate actuation authority. Critical-infrastructure deployment requires system owner approval, independent red-team/assurance, recovery testing and jurisdiction-specific review.

## 5. Source corrections and unresolved candidates

- NVIDIA OpenShell is now a CNCF Sandbox project; Sandbox status is not production certification. Its filesystem enforcement depends on Landlock configuration: `hard_requirement` and `best_effort` have different fail behavior. OpenShell also uses Seccomp and policy/network mediation. Source: https://www.cncf.io/projects/openshell/ and https://github.com/NVIDIA/OpenShell.
- Omnigent is Apache-2.0 and describes itself as Alpha in its upstream README. Its repository is `omnigent-ai/omnigent`; the inspected source does not establish that it is a Databricks product. Source: https://github.com/omnigent-ai/omnigent.
- Qualixar OS upstream describes 13 topologies and 25 CLI commands. These are project-maintainer claims; profile-test and release-pin before adopting. Source: https://github.com/qualixar/qualixar-os.
- ACP is agent-client; A2A is agent-agent; MCP is tool-server/client. Keep these semantics distinct. Sources: https://agentclientprotocol.com/ and https://a2a-protocol.org/latest/.
- DeepSeek Super-Agent in this inventory is the independent MIT repository `LofiSu/deepseek-super-agent`; upstream says it is not an official DeepSeek product. Source: https://github.com/LofiSu/deepseek-super-agent.
- `khy-os` is source-available with commercial restrictions. `sov-kernel-monster` uses FSL-1.1 with Apache-2.0 as a delayed Change License dated 2030-07-22; both require different licensing treatment from OSI-open-source packages. Sources: https://pypi.org/project/khy-os/ and https://github.com/SNAPKITTYWEST/sov-kernel-monster.
- Muse Spark Open is an open-weight 816B / 42B-active release under Muse Model License. Meta documents checkpoint sizes around 1.65 TB BF16 and 537 GB NVFP4, excluding runtime and KV-cache overhead. It may run locally or through a hosted provider; hosted use is not local-only. Sources: https://huggingface.co/meta-models/Muse-Spark-Open-816B-A42B and https://dev.meta.ai/docs/muse-spark-open.
- Nemotron 3 Ultra is 550B total / 55B active, not 500B / 50B. Source: https://research.nvidia.com/labs/nemotron/Nemotron-3-Ultra/.
- SuperQ's air-gap / SuperPQC capabilities are vendor-reported; no NIST certification or validation is inferred. Source: https://superq.com/.
- GR00T 2 code/source availability was scheduled for December 2026; as of this inventory date, do not imply the announced source is already released. Source: https://developer.nvidia.com/.
- Isaac Lab-Arena 0.3 is Alpha and explicitly not for production; Isaac Sim dependencies have separate proprietary licensing. Source: https://github.com/isaac-sim/IsaacLab-Arena.
- `DSH (Dome Sovereign Hub)`, `Alexandria`, `Magetools`, `Thales HexaForce` source/release identity and the exact `Classiq MCP` implementation remain unresolved in this review. Treat DSH as an owner-proposed C2O architecture until its private artifact is supplied.

## 6. Public boundary and non-claims

The UNIVERSALIS repository contains only public candidate references, portable schemas, synthetic records and generic protocol/attestation formats. It contains no C2O private policies, keys, permits, authority tokens, identity anchors, telemetry, world models or deployment data. No component is installed or adopted merely by inventory. Local contract validation does not prove component compatibility, production operation, software safety, model equivalence, scientific correctness, QPU results, robot safety or legal compliance.