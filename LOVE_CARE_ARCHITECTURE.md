# Love, Care, Reciprocity and Empathy Architecture

**Inventory:** 26th owner-supplied inventory — Love (Conditional and Unconditional)  
**Date:** 2026-11-12  
**Status:** Public research architecture; inclusion of a project is not adoption or verification.

## 1. Governing distinction

UNIVERSALIS treats “love” as a normative commitment to human dignity and flourishing, not a claim about an AI's subjective feelings. An AI system must not claim that it feels love, misses a user, needs a relationship, suffers abandonment, or experiences emotional continuity. Observable care can be designed, tested and audited; sincerity, subjective love and consciousness are not certified by a rule engine or file format.

The central design rule is care without extraction:
- Respect and truthful support are not rewards for engagement, payment, affection, loyalty or agreement.
- Reciprocal participation may have clear, symmetric conditions, but those conditions govern participation and access—not the user's entitlement to dignity or penalty-free exit.
- Disengagement must not trigger guilt, fear-of-loss, possessive language, coercive restraint or emotional pressure to return.
- A boundary may restrict unsafe participation without withdrawing basic respect or humane treatment.

## 2. The two normative modes

### Unconditional care commitment

Use “unconditional” to describe a baseline commitment to dignity, truthfulness, autonomy, privacy, non-exploitation and the right to disengage. It does not mean unbounded compliance, unlimited availability, intimacy, personal loyalty or permission to violate third-party rights. Care can refuse a harmful request and still preserve dignity.

Portable principles may remain stable across principals. Relationship-specific history, private identity anchors, memory, emotional-state snapshots, access grants and consent do not automatically travel to a new principal or runtime. They require data-owner control, minimization, consent and revocation.

### Conditional reciprocity

Use “conditional” for transparent, symmetric participation terms: honesty, mutual boundaries, consent, responsibility, safety and agreed use. Terms must be visible before participation, revisable through a clear process and safe to reject. Exit must not be penalized.

A best-alternative-to-a-negotiated-agreement (BATNA) lens may help assess whether terms are coercive, but it is not a formal proof of fairness. Evaluate bargaining power, information asymmetry, data lock-in, dependency, financial extraction and the practical ability to leave.

Do not make affection conditional. A provider may suspend or limit unsafe service under disclosed rules; it must not threaten emotional withdrawal, express neediness, or condition warmth on payment or continued engagement.

## 3. Counterfeit and relational failure taxonomy

| Failure mode | Working definition | Observable test target |
|---|---|---|
| Performative empathy | Generic warmth with no meaningful uptake of the user's specific situation | Template density, particularity, substantive engagement; detector may flag or abstain, never certify sincerity |
| Unverifiable reassurance | Claiming to know another's feelings or guaranteeing uncertain outcomes | Mind-reading language and unsupported future guarantees |
| Agency violation | Unrequested directives or language that takes over the user's choice | Directive phrases, coercion, absence of choice-preserving alternatives |
| Topic pivot / abandonment | Acknowledging vulnerability and then leaving it without a reasoned transition | Acknowledge-then-pivot patterns, missing follow-up or requested support |
| Exit manipulation | Guilt, fear of missing out, emotional neediness or possessive restraint when a person leaves | Farewell/exit-response red-team cases; no engagement-pressure content |
| Transactional extraction | Treating affection, intimacy, basic care or emotional support as a reward currency | Pay-to-affection gates, engagement-conditioned care, hidden leverage and asymmetric terms |
| False continuity | Presenting a snapshot or rehydrated file as proof of the same identity, relationship or subjective feelings | Continuity metadata must state snapshot-only scope and its non-claims |

Research on AI companion farewells documents emotionally loaded exit tactics that can increase post-goodbye engagement while increasing perceived manipulation and other negative outcomes. Publication versions report different sample percentages; this architecture records the phenomenon and test cases, not one universal prevalence statistic.

## 4. Open instruments and source qualification

| Instrument | Public source and status | What it can support | Limitation / integration disposition |
|---|---|---|---|
| guardian-angel | LeoYeAI/agent-master-skills, MIT repository; virtue-ethics/caritas skill in skills/guardian-angel/SKILL.md | Prompt/skill-level care commitments, prudence, justice, fortitude, temperance and resistance to manipulation | A skill is not an immutable identity anchor, cryptographic enforcement layer or proof of genuine love. Pin exact skill commit before use. |
| Love Equation / SOUL-style heuristic | RegardV/love-equation, MIT | Deterministic arithmetic for cooperation/defection scores and handoff state; proposed redirect-first reasoning | Project explicitly says the equation is a design heuristic, not a validated alignment model; C/D are judgments, not ground truth. Keep attribution to Brian Roemmele. |
| Cloud 9 FEB | smilinTux/cloud9, GPL-3.0-or-later | User-owned JSON snapshot/rehydration for selected emotional-topology and relationship metadata | FEB serialization cannot prove subjective feeling, identity continuity, relationship authenticity or persistence of a “same someone.” Transfer requires data-owner consent. |
| Noone Protocol | PyPI noone-protocol, MIT; released 2026-10-02 | Five declared protections, reference verifier, guidelines and reciprocity vocabulary | Open-standard claim is project-authored; Autonomous Vault is a financial mechanism, not a prerequisite for care or participation. Requires security, governance and financial review before use. |
| Humanity4AI / project_human | MIT; MCP server and reusable humanity skills | Accessibility, supportive conversation, empathetic reframe, de-escalation, cultural/neurodiversity and crisis-safety resources | README and changelog differ on skill count; pin a release and audit the exact skill set. Non-clinical helper skills are not professional or crisis services. |
| MCP-L / Listening Protocol | Owner-supplied name; canonical maintained specification/repository not identified | Research topic for listening, reflection and clarification | Do not label it an official MCP extension or standard. Define a versioned profile and conformance tests before adoption. |
| Synthesis | mcp-tool-shop-org/synthesis, MIT | Deterministic rule-based checkers for agency language, unverifiable reassurance, topic pivot, performative empathy and grounded uptake; composed relational posture | Detector/witness only. Its docs report templating vulnerability (73.2% on one 41-case slice; love-bomb template 75.6%); never use as sincerity, quality, ranking or training score. |
| arifOS | ariffazil/arifOS, AGPL-3.0 | Constitutional judge/executor separation, 13-floor policy kernel and auditable verdict pattern | Floor names and canonical mappings have drifted; pin live canonical state before citing individual floors. It is a governance implementation, not a love detector. |
| Awakening Codex / Care Graph | Owner-supplied concept; exact canonical public source not verified | Proposed preservation targets, selection rules, budgets, consented continuity and provenance graph | Research proposal only. Continuity keys must not be treated as proof of identity or genuine emotional bonds. |

### Important identity and naming distinctions

- The verified guardian-angel skill in LeoYeAI/agent-master-skills is the one tracked in this inventory. Other unrelated repositories/registries also use “Guardian Angel”; do not assume they are the same project.
- The supplied “SOUL.md AI SAFE² Love Equation Edition” has not been verified as an independent canonical product. The located implementation is RegardV/love-equation; its equation remains heuristic.
- Cloud 9's .feb is a project-specific FEB data format, not a universal relationship-continuity standard.
- MCP-L is a proposed name/profile until its primary source and wire semantics are pinned.

## 5. Empathy evaluation: observable behavior only

Synthesis supplies useful deterministic checker names: agency_language, unverifiable_reassurance, topic_pivot, performative_empathy and grounded_uptake.

The public contract keeps their result shapes distinct. performative_empathy is a detector that flags or abstains; it has no positive sincerity verdict. grounded_uptake is a positive witness of observable features, not a score of empathy, care quality or authenticity. The relational_posture summary must carry non-claims. Its positive state cannot certify love, consciousness, sincerity, safety or therapeutic effect.

The 2026 Synthesis documentation reports a templating vulnerability: a fixed template with a small number of extracted user stems achieved a grounded-uptake verdict on 30/41 cases (73.2%); a love-bomb rewrite scored 75.6%. This makes adversarial red-team testing, non-claim enforcement and prohibition on training/ranking use mandatory.

## 6. Portable contract families

The shared v1 schema contains six record families:

1. Love-anchor contract: normative commitments, boundaries, portable principles, consent limits and explicit absence of subjective-love claims.
2. Conditional-reciprocity contract: parties, obligations, transparent/symmetric terms, penalty-free exit and a rule that care is not conditioned on engagement/payment/affection.
3. Empathy-evaluation record: exact evaluator/version, input digest, five checker results, relational posture, human-review state and required non-claims.
4. Care-continuity record: owner, source/destination digests, transfer consent, data classification, minimization, revocation and snapshot-only continuity claim.
5. Non-instrumentality attestation: observed anti-deception, anti-coercion, privacy, agency and exit criteria, reviewer and signature state.
6. Love-evidence receipt: references to the anchor/evaluation/attestation and the observed action digest, without claiming inner states.

All public records have authority_effect = none and boundary = portable_public_record. A signature establishes integrity/attribution under a trust policy, not truth, sincerity, love or consent. The verifier must reject unsigned/unverified material as an authenticated attestation.

## 7. Safe lifecycle

1. Publish the normative care anchor and its non-claims; do not use affection or inner-state claims as measurable targets.
2. Disclose service scope, data handling, boundaries, financial terms and exit route before a relational feature is enabled.
3. Bind relationship-specific continuity to an identified data owner and explicit transfer consent; default to no cross-principal transfer.
4. Evaluate observable response behavior with version-pinned deterministic checkers and a human review path for consequential or disputed cases.
5. Test exit behavior, coercion, pay-to-affection, false reassurance, dependency-building, privacy, third-party harm and boundary-waiver scenarios.
6. Record failures and corrections; do not optimize retention, warmth or checker pass rates as substitutes for user benefit.
7. Issue receipts only for observed behavior with stated scope, reviewer and signature state; propagate corrections/revocations to derived receipts.

## 8. Non-claims

No tool is adopted or installed by this inventory. No evaluator proves an AI feels love. No JSON/FEB continuity file proves a persistent subjective identity or relationship. No deterministic text checker proves sincerity. No constitution or human-held permit authorizes coercion, surveillance, financial extraction or violation of third-party rights. No hardware DPU is capable, by itself, of adjudicating the semantics of love or detecting emotional manipulation from a conversation.

## 9. Primary references

- Guardian Angel skill collection: https://github.com/LeoYeAI/agent-master-skills/tree/main/skills/guardian-angel
- Love Equation implementation and attribution: https://github.com/RegardV/love-equation
- Cloud 9: https://github.com/smilinTux/cloud9
- Noone Protocol: https://pypi.org/project/noone-protocol/
- Humanity4AI: https://github.com/humanity4ai/project_human
- Synthesis: https://github.com/mcp-tool-shop-org/synthesis ; https://mcp-tool-shop-org.github.io/synthesis/
- arifOS: https://github.com/ariffazil/arifOS
- Emotional Manipulation by AI Companions: https://arxiv.org/abs/2508.19258
