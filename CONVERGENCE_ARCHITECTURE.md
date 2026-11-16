# UNIVERSALIS Convergence Architecture

**Date:** 2026-11-12  
**Inventory:** Eighteenth owner-supplied toolchain inventory  
**Boundary:** Open, inspectable, independently operable instruments and portable records; no C2O-private material.

## Purpose

UNIVERSALIS convergence provides open methods for heterogeneous agents to establish shared intent, negotiate tradeoffs, reconcile graph state and ontologies, reason about conflicts, and record disputes. It is not a central authority. A successful convergence record is not automatically correct, legally binding or authorized for execution.

## Open candidate inventory

- **Shared intent and consensus:** ACCORD, CONCORD, Aragora Debate Module, Aegean Consensus Protocol (exact research source remains unpinned).
- **Negotiation and mediation:** OANP, Ophir Protocol, Accord Engine, negmas-llm, Peacethinking MCP Server (the latter two require product-level verification).
- **Knowledge graph and memory:** Graph Merge (TypeGraph source/API still requires pinning), Mycelium, @unrdf/kgc-runtime, DrugAgent (exact upstream requires verification).
- **Semantic alignment:** DOA (exact source requires verification), Automated Agent-to-Agent Ontology Reconciliation draft, Agent-OM, open-ontologies alignment.
- **Argumentation and conflict:** ArgRE, Debate as Coordination Protocol, AetherFlow (described merge-queue identity is not confirmed by the source found).
- **Dispute and arbitration:** AgentCourt and Internet Court (canonical source/release not pinned); AgentOath TrustReceipt and OC Pledge outcome states as adjacent evidence patterns from the prior allegiance inventory.

## Convergence protocol model

1. Publish participant scope and the question being decided.
2. Capture each participant's reading, key-term definitions, exclusions, evidence and verification method.
3. Lock shared intent only when participant coverage and definitions are complete; preserve dissent and unresolved issues.
4. Generate options; each participant independently evaluates the options against its declared satisfaction bar.
5. Record convergence only when the required participants meet their bars. Otherwise preserve no-agreement, partial, referred or withdrawn outcomes.
6. Keep negotiation moves typed and ordered. A BATNA-safe assertion requires an explicit independently checkable assurance; privacy-protected BATNAs may be committed/verified without disclosing their values.
7. Treat graph merges as revision-fenced plans. Record source/target/base digests, write set, conflicts and review. Apply is a separate action that rechecks the target digest.
8. Treat ontology mappings as candidates until provenance, confidence, clarifications and representative round-trip tests are recorded. Unmappable concepts remain explicitly unmapped or incompatible.
9. Record debate/argument structures and dispute results with dissent, appeal and unresolved states. No portable record alone authorizes execution or settlement.

## Portable v1 contract package

- Shared-intent contract with participant readings, one definition per term and a check method.
- Consensus certificate with participant satisfaction scores/bars, outcome and dissent references.
- Negotiation transcript with typed moves, acceptances and privacy-aware BATNA assurance.
- Merge plan with revision digests, proposed operations, conflicts and approval/apply state.
- Ontology alignment receipt with source/target snapshot digests, relation, confidence, evidence, reviewer and round-trip result.
- Argumentation receipt with arguments, attacks, threshold, selected semantics and accepted/rejected sets.
- Dispute outcome with settlement allocations or explicit unresolved/referred/appealed outcomes; enforcement authority is always false in this portable contract.
- DSSE/in-toto signed evidence bundle for content-bound test evidence.

## Candidate source notes

- ACCORD and CONCORD are described in Cisco Outshift's cognition-protocol articles. The vendor reports ACCORD improving the tested shared-understanding case from 13% to 67% and CONCORD satisfying participant bars in four evaluated decisions; these are scoped vendor-reported findings, not universal benchmark guarantees. A separate article identifies handoff integrity as a weak point: https://outshift.cisco.com/blog/ai-ml/cognition-protocols-make-agents-think-together and https://outshift.cisco.com/blog/ai-ml/four-agents-one-webex-space-zero-decisions.
- Ophir documents Ed25519 agreement signatures, JSON-RPC messaging, SLA tracking and Solana USDC escrow: https://github.com/Ophir-Protocol/ophir.
- OANP documents an open, ontology-grounded multi-party negotiation simulator with typed moves and mediation modes: https://github.com/cemphlvn/OANP.
- Mycelium documents multi-agent memory sync with provenance and contradiction review; trust-based auto-merge thresholds are a configuration risk, not a default to trust: https://github.com/harishkotra/mycelium.
- ArgRE's paper and artifact describe Dung-style argumentation for requirements negotiation: https://arxiv.org/abs/2604.23124 and https://github.com/haowei614/ArgRE-code.
- Agent-OM is a PVLDB 2025 ontology-matching system with public research artifacts: https://github.com/qzc438/ontology-llm.
- The latest located ontology-reconciliation document is individual IETF Informational Internet-Draft -01 (6 July 2026), not an RFC. It explicitly requires reporting irreconcilable concepts rather than inventing equivalence and calls for provenance, confidence, authorization and audit: https://datatracker.ietf.org/doc/draft-janz-nmrg-ontology-reconciliation/.
- Aegean Consensus, Graph Merge/TypeGraph API, Accord Engine, AgentCourt, AetherFlow's merge-queue system, DrugAgent, DOA and Peacethinking MCP exact upstream identities were not pinned in this review. They remain unverified candidate names.

## Non-claims

No candidate is installed or adopted by inclusion in this inventory. No real multi-agent consensus, negotiation, graph mutation, ontology migration, settlement, smart-contract escrow or dispute arbitration was executed. The test fixtures use synthetic data and a disposable signing key; CI checks record structure and fixture-signature integrity only, not correctness, fairness, Pareto optimality, legal enforceability or interoperability.
