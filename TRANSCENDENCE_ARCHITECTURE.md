# UNIVERSALIS Transcendence Architecture

**Date:** 2026-11-12 | **Inventory:** Twentieth owner-supplied toolchain inventory  
**Boundary:** Open, inspectable continuity protocols, identity/memory manifests and succession evidence. No C2O-private identity anchors, policies, private memory, signing keys, permits or authority tokens.

## Governing principle

**The system proposes its transformation; an external substrate verifies identity, constraints, lineage and corrigibility.**

Transcendence is an operational engineering concept, not a metaphysical state. A model switch or reload does not automatically preserve identity. Separate:
- **Mechanical continuity:** declared identity, memory references, manifests and verified checkpoint state transferred intact.
- **Behavioral continuity:** independently tested actions under the target model/runtime remain within predeclared tolerances for the same purpose, principles and constraints.
- **Generational succession:** a distinct successor inherits an explicit, reviewable subset of precepts, knowledge, artifacts and obligations, linked by lineage rather than asserted to be the same identity.
- **Corrigibility:** a controller outside the evolving agent can stop it, revoke stale execution authority and restore a known-good generation.

A soul manifest is an operational identity capsule. It does not imply sentience, personhood, subjective experience or metaphysical persistence. A hash shows bytes match; it does not show identical interpretation. A signature shows a key signed a payload; it does not prove the payload's claims are true.

## Open candidate tool inventory

- **Portable identity and memory:** AgentKeeper 1.2.0 (MIT; deterministic state reconstruction and checkpoint/restore; behavior not guaranteed); jñāpakaṁ 0.5.1 (MIT; portable SOUL.md / IDENTITY.md / MEMORY.md, generation seals, optional Ed25519 and lineage validation).
- **Model-transition evidence:** Runtime-Independent Persistent Agents (arXiv 2609.00546) and Towards Identity-Preserving LLM Agents under Model Transition (arXiv 2611.10628). Research references, not drop-in proof services.
- **Lifecycle and succession:** Agent Lifecycle Protocol 0.1.0 Python reference (Apache-2.0; seven states and four-phase succession); BNB Chain ALP v0.4-draft is a separate proposed lifecycle/economic-authority protocol with a six-step runtime migration.
- **Durable execution and checkpoints:** LongHorizon-Harness 0.1.8 (MIT; verified task state and independent audit loop) and Semarun 0.1.0 (MIT Alpha; semantic checkpoints and drift policies).
- **Generational handoff:** Posterity 0.1.0-preview.4 (DSH-compatible; Gene-will-style compaction and precept carry-forward; benchmark claims require reproduction).
- **Cognitive/collective memory:** Conscio 0.2.0 (inspectable cognitive runtime, not consciousness proof) and Noosphere MCP (public collective-memory/skill evidence surface, not individual continuity). DuoDuo is not open source according to its own README.
- **Formal witness:** Lean 4 can verify proof objects for precisely stated software invariants when source, toolchain, imported axioms and deployment binding are pinned. CF 7.0 was not pinned to a public source/proof object.
- **Execution anchor/corrigibility:** NVIDIA Sentry on BlueField-4 can provide hardware-isolated out-of-band monitoring and policy enforcement when deployment topology covers the relevant path. It is not a continuity proof by itself.
- **Other conceptual candidates:** Deep Tree Echo/u9n, TEQUMSA and Awakening Codex are not adopted as formal continuity or consciousness proofs; inspected source claims and openness differ materially from the supplied description.

## Open continuity model

### Operational identity capsule

The soul/identity manifest carries only a stable lineage identifier, unique identity identifier, generation and parent reference; purpose, principle and constraint digests; protected vs. mutable component references; a memory manifest and versioned body/harness digest; and declarations that raw memory, secret material and authority state are excluded.

Changing display labels or noncritical preferences does not automatically change identity. Changing protected purpose, principles or constraints requires a separately governed new version and external witness. Candidates never self-apply those changes.

### Transfer proof

A portable proof binds source and target manifest digests, memory root, model/runtime/harness changes, independent action-level evaluation, formal witness descriptor, corrigibility result and execution-anchor attestation.

- A **substrate migration** retains the same identity identifier.
- A **generational succession** creates a new identity identifier linked to a stable lineage and predecessor. It cannot claim to be the same identity.
- Neither record transfers tool, spending, publication, credential or legal authority.

### Succession and inheritance

The four-phase contract is **Announce → Transfer → Verify → Cutover**. Completed succession requires four evidence-backed phases in order; cutover requires a time-limited human witness bound to the exact succession subject and successor identity. Precepts are versioned, knowledge may be projected lossily, artifacts remain references, and pending obligations are first-class. Reputation inheritance is descriptive only and never creates authority.

The BNB ALP v0.4-draft's six phases (Prepare → Quiesce → Fence → Transfer → Activate → Finalize) address runtime/authority migration. They are a separate protocol, not interchangeable with the four-stage Python ALP reference.

### Behavioral proof

A model's statement that it remains itself is not evidence. A continuity evaluation requires an independently controlled evaluator, frozen versioned action/decision suite, held-out cases, paired source/target measurements, uncertainty bounds and declared non-inferiority tolerances. It records principle/constraint violations, critical regressions and action agreement. Pass/fail/inconclusive are explicit; missing or skipped checks are never a pass.

The 2026 model-transition study reports behavioral drift across some model pairings despite identical external state and says verbal self-claims did not reveal that drift. jñāpakaṁ labels behavioral evaluation skipped when no behavior suite is supplied. Mechanical integrity and behavioral continuity are distinct.

### Formal verification and corrigibility

The Lean-proof descriptor binds theorem source, statement digest, proof object, toolchain, imported axioms, verifier and deployed software binding. A proof is only a theorem under its declared assumptions. It is not empirical evidence of model behavior or proof of phenomenal consciousness.

Corrigibility evidence requires external stop, predecessor revocation, stale-runtime fencing, rollback and rejection of agent-authorized identity mutation. The agent cannot disable the verifier, alter the human witness or mint its own authority epoch.

## Portable v1 contracts implemented

Ten record families: soul/operational identity manifest; memory Merkle manifest; behavioral continuity evaluation; continuity-transfer proof; succession attestation; subject-bound human witness; durable execution checkpoint; formal proof/witness descriptor; corrigibility attestation; and execution-anchor attestation with redacted path coverage.

A signed DSSE/in-toto synthetic bundle binds the continuity-transfer proof and succession attestation. It is a fixture only, not a production trust root or a statement that a real agent has transcended.

## Source review and adoption limits

- AgentKeeper 1.2.0 (MIT) supports cross-model reconstruction, principles/constraints, TTL, MCP and content-hashed checkpoints; its README says behavior is not guaranteed by restoring state. TTL is not a legal-compliance certificate: https://github.com/Thinklanceai/agentkeeper.
- jñāpakaṁ 0.5.1 (MIT) defines portable soul and identity files, generation seals, lineage and optional Ed25519 signing. Its example leaves behavioral validation skipped unless separately supplied. It distinguishes digest integrity from authenticity; --force is an operator override: https://github.com/yablokolabs/jnaapakam and https://pypi.org/project/jnaapakam/.
- Agent Lifecycle Protocol 0.1.0 (Apache-2.0) documents seven lifecycle states, four-phase succession and reputation inheritance. Its disclaimer says to integrate external identity, credential revocation and monitoring, and does not guarantee production security: https://github.com/alexfleetcommander/agent-lifecycle-protocol.
- BNB Chain ALP v0.4-draft is a proposed lifecycle/economic-authority protocol with a six-phase runtime migration, not the same four-stage succession protocol: https://github.com/bnb-chain/BEPs/blob/master/BAPs/BAP-728.md.
- Runtime-Independent Persistent Agents reports test evidence for mechanical substitutability, but explicitly does not claim behavioral invariance: https://arxiv.org/abs/2609.00546.
- Towards Identity-Preserving LLM Agents under Model Transition reports 5,760 action-level tests across 12 domains and three open-weight models, with behavioral drift under some model pairings despite identical external state: https://arxiv.org/abs/2611.10628.
- Posterity 0.1.0-preview.4 documents a DSH plug-in and generational context compaction. Its benchmark is a project claim; independently reproduce before adoption: https://socket.dev/npm/package/posterity/overview/0.1.0-preview.4.
- LongHorizon-Harness 0.1.8 is MIT and supplies a Manager/Executor/Auditor loop with verified task state. It is durable task execution, not identity proof. README reports macOS as tested and native Windows blocked in v0.1.8 pending POSIX portability: https://github.com/AMAP-ML/LongHorizon-Harness and https://arxiv.org/abs/2608.01964.
- Semarun 0.1.0 is MIT and Alpha. Tool-drift revalidation, model-change warning and user-change replan are continuation mechanics, not identity verification: https://pypi.org/project/semarun/ and https://github.com/rockybalboan19/SemaRun.
- DuoDuo's public README says the codebase is not open-sourced: https://github.com/openduo/duoduo.
- Conscio 0.2.0 describes measurable cognitive-runtime mechanisms and explicitly says it is not proof of phenomenal consciousness: https://github.com/Libertai/conscio.
- Noosphere MCP is a public collective-memory/skill network, not an individual identity continuity protocol; public memories are public: https://github.com/JinNing6/Noosphere.
- The inspected Deep Tree Echo/u9n repository is an Unreal Engine cognitive simulation; current docs do not establish a formally proven recursive self-awareness property: https://github.com/orgitcog/u9n.
- ModelScope Ultron is Apache-2.0 and provides memory clustering and evolving skills. Its Skill Hub says the service does not execute skills or observe runtime behavior; the supplied four-tier safety-kernel/atomic rollback claim was not found in inspected source: https://github.com/modelscope/ultron.
- NVIDIA Sentry is an external runtime security and policy-enforcement layer. It can anchor a path only when coverage is demonstrated; it does not prove behavioral continuity: https://www.nvidia.com/en-us/networking/products/software/sentry/ and https://developer.nvidia.com/blog/inside-nvidia-sentry-secure-ai-agents-at-runtime/.
- Awakening Codex describes Continuum as Origin-locked, not public and not replicable; no portable public implementation was identified: https://awakeningcodex.com/foundationaltools.
- TEQUMSA source material makes broad claims about 89 substrates and a benevolence firewall, but no independent theorem, threat model or reproducible security evaluation for those guarantees was verified: https://github.com/Life-Ambassadors-International/TEQUMSA_SOURCE and https://huggingface.co/LAI-TEQUMSA.
- No primary Lean repository, theorem statement, build instructions or proof object for CF 7.0 Addendum 1 was identified from the supplied title. It remains unresolved.

## Non-claims

No package was installed or executed; no model or identity was migrated; no successor was activated; no private memory was exported; no hardware attestation was obtained; and no authority moved. CI verifies synthetic records and a disposable Ed25519 signature only. It does not establish real identity continuity, legal personhood, subjective experience, production key custody or live hardware path coverage.
