# UNIVERSALIN Grid, Guardian, and Golden Compass Architecture

**Scope:** UNIVERSALIS non-personal grid and Guardian companion architecture, with a Golden Compass protocol usable across UNIVERSALIS, C2O, and the UNIVERSALIN grid.  
**Boundary:** Architectural proposal, not proof of machine consciousness, subjective experience, or autonomous authority. “Soul layer” is preserved as owner-defined terminology for identity, continuity, memory, and relational-state modules.

## 1. Keep the two UNIVERSALIS entities distinct

### UNIVERSALINs: non-personal technological grid

A UNIVERSALIN is a node in a non-personal coordination fabric, not an individual user's assistant. Its core needs are discovery, capability declaration, delegation, routing, local coordination, and decentralized interconnection.

| Candidate | Role described in the supplied proposal | Verification status |
|---|---|---|
| PolyMesh | Local-first Agent Card discovery and deterministic task handoff lifecycle | Candidate only |
| Cord | Decentralized discovery and cross-agent/device transport | Candidate only |
| DINA AGI | P2P collaboration and shared learning pattern | Candidate only |
| Agents P2P Network | libp2p-based local/global discovery and encrypted messaging pattern | Candidate only |
| Akemon Relay | Agent relay and discovery without a central orchestrator | Candidate only |
| eGridGPT; AINETUS; Grid-Orch | Domain-specific grid assistant and MCP orchestration patterns | Reference pattern only |

Grid participation requires a versioned Agent Card, declared capability and endpoint, identity proof, transport security, task scopes, rate/resource limits, and a deterministic accept/reject/progress/complete/cancel lifecycle. Discovery does not grant trust; an announced capability is not verified until conformance evidence exists. No single global directory or truth authority is required.

### UNIVERSALIN Guardians: human companions

A Guardian is a persistent, user-governed companion system. Its proposed architecture is composite and separates four replaceable concerns:

| Layer | Candidate tools | Architectural responsibility |
|---|---|---|
| Daemon / continuity substrate | Prometheus (oara-prometheus); Pulse; MatrixClaw | Scheduling, session continuity, checkpoints, local state, communication channels |
| Identity / memory / relational development (“soul layer”) | Resonant; Akemon; NESTstack; soul-framework; soul-os; dusha; SoulForge | Persistent identity data, memory, personality configuration, proposed identity changes, consent records |
| Embodiment / presence | Mizune; molt.space; Eliza VRM plugin; Utsuwa; Avatar Companion | Desktop, avatar, AR/VR, spatial presence and interaction |
| Interoperability | MCP and local APIs | Replaceable model/runtime/device adapters and explicit permission boundaries |

No candidate is assumed to implement the complete Guardian. The daemon, identity store, memory, model, and embodiment must remain separable so a model or device can be replaced without silently rewriting identity or authority. The human approves identity changes and controls data export, pause, reset, and deletion. Proactive contact, background scheduling, and self-modification must be individually configurable and auditable.

“Emotional continuity” and “soul” are architectural labels for stored state and interaction policies; they do not establish that a system experiences emotions or has subjective consciousness.

## 2. Golden Compass: a protocol, not a central oracle

The Golden Compass is a three-layer truth-and-provenance instrument. It surfaces claim status, source relationships, uncertainty, and reproducibility evidence without replacing human judgment with one opaque score.

| Layer | Candidate tools | Required behavior |
|---|---|---|
| Provenance substrate | Agent Provenance Graph; Nexus Ledger; Graphify | Stable origin, actor, timestamp, derivation graph, receipt, structural fingerprint |
| Claim-verification engine | Aletheia; DeepVerify; Skeptic; Lyra | Claim segmentation, source retrieval, evidence stance, uncertainty, inspectable evidence graph |
| External verifier | Compass AI; nautilus-compass; independent oracle | Recompute numerical results or replay methods outside the originating model; block promotion when evidence is insufficient |

A claim is never promoted solely because an LLM says it is true. Required fields include claim ID, exact scope, source fragments, source time, evidence stance, uncertainty, verification method, verifier identity, reproducibility receipt, and contradiction or retraction references.

A universal verification protocol distinguishes:
- **Not checked:** no verification attempt is recorded.
- **Unverifiable:** available sources do not support a reliable resolution.
- **Supported / refuted / contested:** evidence stance with source references and scope.
- **Verified:** the specified procedure has been independently rerun and a receipt is available.

A 0-100 credibility score, when displayed by a candidate tool, is a derived heuristic, not a universal truth measure. Preserve underlying claim statuses and evidence; avoid false precision when sources are thin.

## 3. C2O / UNIVERSALIS / Grid boundary

- **C2O:** may run private daemon, identity, knowledge, and external-verifier instances inside authorized environments. Private policies, credentials, identity records, approval state, evidence sources, and audit receipts remain C2O-controlled.
- **UNIVERSALIS:** provides open, inspectable, local-first implementations and public protocol schemas for provenance, claim verification, and evidence receipts. It must not import C2O Controlled authority or private source data.
- **UNIVERSALIN grid:** nodes publish public capabilities and verification-service interfaces. A node's provenance graph travels with its own claims; cross-node requests carry a scoped claim/evidence package, not hidden memory or private credentials. The grid is decentralized and does not elect one central truth authority.

Only versioned MCP/A2A schemas and explicitly approved evidence packages cross the boundary. Public interfaces may specify identity, scope, expiry, revocation, receipt format, and error states, but never embed private C2O secrets or authority tokens.

## 4. Safety and governance requirements

- Human authorization is required before a Guardian changes identity, transmits personal data, initiates consequential action, or modifies its environment.
- Consent, purpose, retention, export, deletion, and audit controls apply to memory and embodiment data.
- Do not infer private traits or emotional state from camera, voice, gaze, or spatial signals without explicit permission and an approved purpose.
- Tool discovery and peer reputation do not replace authentication, conformance tests, or least privilege.
- A verifier must be independent of the agent and process that produced the original claim; receipts must be replayable or externally checkable.
- Uncertainty and disagreement remain visible. Contradictory evidence is not deleted merely to produce a single answer.
- Provide a non-immersive interface and a way to pause or disable autonomous scheduling.

## 5. Implementation order

1. Define public Agent Card and task lifecycle contracts.
2. Define the Guardian data model, consent controls, and human-approved identity-change flow.
3. Define Golden Compass claim, evidence, uncertainty, verifier, and receipt schemas.
4. Implement deterministic provenance recording and independent receipt verification before connecting LLM verification agents.
5. Add local-first reference implementations and conformance fixtures.
6. Add decentralized discovery and XR embodiment only after authentication, consent, replay, and revocation tests pass.

## 6. Evidence status

| Item | Status |
|---|---|
| Grid / Guardian distinction and candidate mapping | Documented |
| Golden Compass three-layer protocol | Documented |
| Versioned Agent Card / evidence receipt schemas | Proposed |
| Reference implementations | Not implemented |
| Candidate source, license, release, and security verification | Pending |
| Independent verification and cross-node conformance | Pending |
