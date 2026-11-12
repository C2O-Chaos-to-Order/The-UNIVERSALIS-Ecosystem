# UNIVERSALIS Ascendence Architecture

**Date:** 2026-11-12  
**Inventory:** Nineteenth owner-supplied toolchain inventory  
**Boundary:** Open, inspectable, independently operable capability-evolution instruments and portable evidence; no C2O-private policy or operational data.

## Governing principle

**The model proposes; the substrate validates; the model does not certify its own improvement.**

UNIVERSALIS Ascendence treats capability evolution as bounded experimental search. A candidate is an untrusted proposal until an independent evaluator and frozen promotion gate produce evidence. An improvement claim must name its baseline, candidate digest, model/harness versions, evaluator, frozen suite, holdout, never-optimized-against anchor, uncertainty, cost, safety/regression results and rollback path. A signature proves payload integrity and signer control of a key; it does not prove the truth of scores or evaluator independence.

## Open candidate inventory

- **Experience-driven task-asset evolution:** DarwinAgent (experimental 0.2.0); Harness² (Google Research/Apache-2.0, harness rather than weight evolution); The Trinity (research project, code release not verified).
- **Promotion engines and witness gates:** @metaharness/flywheel; VERDICT (exact upstream not pinned); AWS sample-sentinel-harness (Amazon Bedrock AgentCore Harness reference driver); Aura RSI Validation (exact upstream not pinned).
- **Bounded feedback/RSI substrates:** vsf-rsi (L1–L3 autonomous in its current published README, L4 human-approved); ASAN (conceptual architecture); FIRM Protocol (package-level project claims); Ormica.
- **Genome/mutation/evolution:** agent-taxonomy (GENOME.md conventions plus a classification npm package); Aragora Genesis (AgentGenome/GenomeBreeder/GenesisLedger); EvoMap Evolver (GEP Genes/Capsules/Events); Living Agent/GODEGEN and Agent DNA (exact upstream not pinned); Ouroboros (self-modification research candidate, not production default).
- **Persistence/identity continuity:** Tur (Merkle-backed state/persona and memory export; cross-model identity invariance remains an open question).
- **Search/harness experiments:** opencode-autoresearch, evolving-agent-harnesses, auto-harness, HyperAgents and ace-skill (canonical release/feature verification outstanding).

## Open protocol model

1. Freeze and fingerprint the promotion gate before the run. Its conjunctive checks are independent evaluation, paired comparison, holdout, anchor, safety veto, regression guard, budget, protected-surface guard and rollback path.
2. Keep model weights fixed when testing harness/configuration changes; bind baseline/candidate model digests.
3. Treat generated genomes, prompt edits, skills, plugins, scripts, tools, memory layout and specialist-agent proposals as untrusted mutations.
4. Keep the evaluator, promotion verifier, protected symbols, budget broker and rollback path outside the proposer-controlled mutation surface.
5. Require paired evidence and independent holdout/anchor evaluation. A zero/no-op or inconclusive result is not lift. Track utility, uncertainty, latency, cost, abstentions and safety/regression alongside the primary score.
6. Require external witness approval bound to the exact candidate digest, evaluation digest and gate fingerprint whenever the declared autonomy ceiling requires it.
7. Record every proposal, rejection, promotion, rollback and recall as a parent-linked lineage event. The receiving verifier can replay the chain to gen-0.
8. Use content-addressed memory/persona manifests to describe exported state without exporting private raw memories. A Merkle root verifies content consistency, not identity sameness across different model weights.
9. Preserve protected identity, purpose, constitution, safety, authorization, evaluator, gate and rollback surfaces. Candidate changes to those components are never self-applied.
10. Stop or roll back on a failed safety veto, regression, stale gate, invalid signature, evaluator conflict, budget overflow or missing evidence.

## Portable v1 contract package

- Frozen promotion-gate manifest with canonical fingerprint.
- Autonomy-ceiling declaration with per-level approval and rollback requirements.
- Genome contract with component mutability, parent reference, mutation set and multidimensional fitness vector.
- Paired evaluation record with fixed model digest, frozen suite, holdout, anchor, safety, regression, budget and rollback results.
- Subject-bound human witness approval.
- Admission card with explicit promote/reject/human-review/inconclusive decisions.
- Parent-linked lineage event with content digest.
- Merkle memory/persona manifest with digests and disclosed data classes only.
- DSSE/in-toto signed ascent receipt binding the admission card and lineage event.

A portable record is evidence, not an execution permit. Promotion, external publication, capability grants and production deployment require the receiving environment's own authorization.

## Candidate source notes and qualifications

- DarwinAgent 0.2.0 is marked experimental; its own docs distinguish scripted offline replay from genuine model learning and use an externally configured model endpoint: https://github.com/gogoingai/DarwinAgent.
- Harness² (arXiv 2610.14224; Apache-2.0 repository) evolves prompts/guardrails/memory/tools/skills/scripts/subagents/plugins around fixed weights. Its README warns unrestricted network access and disabled Codex sandbox in the executor: https://github.com/google-research/harness2 and https://arxiv.org/abs/2610.14224.
- AWS sample-sentinel-harness implements an agent-authored witness-gated loop on Bedrock AgentCore Harness; it is AWS-specific and its README differentiates live-validated capabilities from designed/simulated work: https://github.com/aws-samples/sample-sentinel-harness.
- @metaharness/flywheel advertises frozen conjunctive gates, an anchor and holdout, Ed25519 receipts and replay; production mode requires pinned gate/signer identities and independent evidence. Project history documents a replay-anchor gap; require a pinned release and independent replay test: https://www.npmjs.com/package/@metaharness/flywheel and https://github.com/ruvnet/metaharness/issues/230.
- vsf-rsi currently documents L1–L3 autonomy and L4 human approval; local governance may deliberately lower that ceiling: https://github.com/rm-w3kufe/vsf-rsi.
- agent-taxonomy explicitly describes GENOME.md and mutation as conventions beyond the package's implemented classifier/validator: https://github.com/suryast/agent-taxonomy.
- Aragora Genesis documents AgentGenome, PopulationManager, GenomeBreeder, FractalOrchestrator and GenesisLedger: https://github.com/synaptent/aragora/blob/main/docs/workflow/GENESIS.md.
- EvoMap Evolver's source describes its safe validation-command allowlist, staged external assets, and host-runtime boundary: https://github.com/EvoMap/evolver.
- The Trinity's repository currently presents code as coming soon; retain its paper as research until a tagged executable release is confirmed: https://github.com/InfRec-Cardinal/The-Trinity.
- ASAN is a conceptual architecture paper. FIRM capabilities are package/project claims. The inspected Ormica 0.10.0 release documents permission-chain and auto-pruning features; PyPI now lists 0.11.1, so re-pin and review the newer release and its permission defaults before adoption: https://github.com/Variable-Fox/ASAN-Architecture, https://pypi.org/project/firm-protocol/, https://pypi.org/project/ormica/0.10.0/.
- Tur's docs explicitly identify cross-model identity invariance and the nature of persistent persona adaptation as open hypotheses: https://erivlis.github.io/tur/essays/the-calibration-of-expectation/.
- Ouroboros is deliberately self-modifying and should be treated as an adversarial research/test candidate, not a default open production engine: https://github.com/razzant/ouroboros.
- Exact maintained sources/releases remain unverified for VERDICT, Aura RSI Validation, Living Agent/GODEGEN, PDR, Agent DNA, OpenCode Autoresearch, evolving-agent-harnesses, auto-harness, HyperAgents and ace-skill.

## Non-claims

No candidate is installed or adopted by this inventory. No live model training, weight mutation, agent genome breeding, harness promotion, private memory export, production deployment or hardware containment was performed. CI validates synthetic contract semantics and a disposable fixture signature only; it does not establish model improvement, generalization, evaluator independence, constitutional safety, identity continuity, production signing key custody or hardware enforcement.
