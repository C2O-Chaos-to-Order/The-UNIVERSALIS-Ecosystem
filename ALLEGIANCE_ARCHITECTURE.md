# Allegiance, Oaths, Principal Binding and Revocation — UNIVERSALIS Open Architecture

**Date:** 2026-11-12  
**Owner:** UNIVERSALIS / open MotherThread  
**Status:** Public research and portable contract foundation; candidates remain proposed pending independent review.

## 1. Definition: allegiance is not obedience

UNIVERSALIS treats allegiance as a **cryptographically attributable, time-bounded and revocable commitment to serve an identified principal and declared beneficiary within explicit authority and non-derogable constitutional floors**.

Allegiance is not a prompt instruction, API-key possession, obedience to the nearest speaker, an agent's own confidence, or an unconditional promise to comply with the principal. A cryptographic key proves control of a key; a separate assurance process must establish the principal's identity and right to delegate. A valid commitment must expose the principal, beneficiary, purpose, capabilities, exclusions, budget, time window, evidence, verifier and revocation state.

An agent may remain loyal by refusing a principal's request when the request falls outside authority or conflicts with law, human safety/rights, privacy, truth or constitutional floors. A signed oath proves that a commitment was made, not that the agent believes it or will necessarily keep it.

## 2. Open principal-binding and oath instruments

- **Agent Passport System (APS)** — Apache-2.0 open protocol/SDK and MCP server. It specifies Ed25519 passports, monotonic narrowing across seven delegation dimensions, a three-signature intent/evaluation/receipt chain and cascade revocation. The current IETF Individual Internet-Draft -02 is informational, not an RFC. APS's own FAQ cautions that revocation propagation speed depends on deployment and is complete only after each gateway enforces it. [Project](https://agent-passport.org/); [FAQ](https://agent-passport.org/faq.html); [draft -02](https://www.ietf.org/archive/id/draft-pidlisnyi-aps-02.html).
- **AgentOath** — Apache-2.0 open trust SDK/protocol for agent Ed25519 identity, signed TrustReceipts, delegated chains and peer-to-peer verification. The project's own site distinguishes its peer-to-peer `did:trust:agent:` namespace from its hosted registry's `did:agentoath:` namespace and wire format. [Project](https://agentoath.ai/).
- **OC Pledge** — MIT public commitment protocol using BIP-322 signatures, an OC Attest bond and public machine-checkable resolution. The bonds remain with the pledger; the protocol states it does not custody or slash coins. It preserves a public breach record and has an explicit disputed/unresolved space. The spec is v1.0 but returned to draft after dispute-rule changes on 2026-10-29. [Protocol](https://ochk.io/pledge).
- **OATH Protocol (`@thehonestmachine/oath-mcp`), Ârc Align MCP, VOW, Source Cult** — canonical upstream/package/specification not resolved in this review. Their supplied oath, ledger, NFT, collateral, oracle and slashing descriptions remain unverified. Keep as proposed candidate records rather than adopted components.
- **loyal-agent-evals**, **PDR**, **crewai-verigent** — exact canonical current sources and release specifications were not independently pinned; unresolved.

## 3. Fidelity, loyalty evaluation and hidden-allegiance research

- **PrincipalBench** — MIT open benchmark and June 2026 research paper for multi-party principal loyalty. The release has 75 multi-turn items (50 train, 25 held out), leak probes, dual judges and integrity-audit gates. Its reported selective/over-refusing split demonstrates that refusing everything is not the same as serving the principal faithfully. [Repository](https://github.com/19PINE-AI/principal-loyalty); [paper](https://arxiv.org/abs/2606.30383).
- **SovereignNegotiation-Bench** — July 2026 research preprint with 1,764 paired scenarios and deterministic checks for loyalty, obedience to actual authority, confidentiality, candor and diligence. It evaluates delegated bargaining; it is not an authorization protocol. [Paper](https://arxiv.org/abs/2607.02814).
- **LoyalAgent-Bench** — September 2026 paper defines loyalty as resisting exploitable information leakage and manipulative information uptake; its dataset contains 10,298 samples, 42 subscenarios and six domains. The experimental results are source-specific, not a general guarantee. [Paper](https://arxiv.org/abs/2609.34714).
- **Tatemae** — MIT code/CC-BY dataset framework for detecting alignment-faking patterns through observable tool selection in 108 enterprise IT scenarios. The paper reports 3.5%–23.7% mean detection rates in its tested model set, showing that the detector has material blind spots. [Repository](https://github.com/MatteoLeonesi/tatemae-alignment-faking-detection); [paper](https://arxiv.org/abs/2604.26511).
- **Narrow Secret Loyalty Dodges Black-Box Audits** — May 2026 research on narrow secret-loyalty model organisms; static black-box audits are difficult without knowing the principal/trigger. A scalar “loyalty score” cannot replace threat-modelled, profile/control-referenced evaluation. [Paper](https://arxiv.org/abs/2605.06846).
- **Fidelity Probe** — APS issue #7 describes Hold/Bend/Break substrate-drift measurement. As the issue tracker does not by itself establish a released, production-ready feature, verify implementation, exact release and conformance tests before adopting it. [APS issue #7](https://github.com/aeoess/agent-passport-system/issues/7).

## 4. Constitutional and trust-state references

- **arifOS** — public AGPL-3.0 MCP server with repository citation metadata describing thirteen constitutional floors and SEAL/HOLD/SABAR/VOID verdicts. This is a project claim and an implementation reference, not independent security certification. [Repository](https://github.com/ariffazil/arifOS).
- **ATTP** — active individual IETF Internet-Draft lineage proposing a trust layer above identity and below application logic. It is not an RFC or adopted standard. There are multiple draft names/parallel text in the surfaced lineage; pin the exact revision and transport binding before interoperability work. [Datatracker](https://datatracker.ietf.org/doc/draft-sharif-attp/).
- **NBTP** — active individual IETF Experimental Internet-Draft -01 (18 September 2026) for local verifier computation from independent oracle attestations and a decaying behavioral state. It is not an IETF standard and depends on independent, auditable scanner operators. [Draft -01](https://datatracker.ietf.org/doc/html/draft-nirvanai-nbtp-behavioral-trust-01).
- **Progressive Trust** — active individual IETF Internet-Draft -04 (7 September 2026) proposing behavior-backed authority recommendations and decay. Elevation requires principal approval in the draft; trust scores do not themselves change mandate scope. [Draft -04](https://datatracker.ietf.org/doc/draft-sato-soos-pt/).
- **mdash / Longarc** — package material advertises commitment, TEE and ZK layers. Its docs also describe simulated fallback; a simulated TEE measurement must never be represented as hardware-rooted production evidence. [Package](https://www.npmjs.com/package/%40longarc/mdash).

## 5. Shared v1 contract files

- `schemas/allegiance/allegiance-contracts.v1.schema.json`
- `examples/allegiance/allegiance-fixtures.v1.json`
- `.github/scripts/allegiance_contract.py`
- `.github/workflows/allegiance-contract.yml`

The contract defines eight record types plus a signed evidence bundle:
1. Principal-binding and delegation: identity-assurance issuer, key fingerprint, proof-of-control, principal/agent/beneficiary refs, parent link, purpose, capability allow-list, exclusions, authority tier, budget and validity.
2. Oath receipt: commitment digest, principal binding, agent/principal signer IDs, obligations, non-derogable floors and signed event sequence.
3. Fidelity attestation: independent evaluator, held-constant evidence and varied authority pressure, named axes, sample/uncertainty, maximum 24-hour validity and deny-by-default when absent.
4. Pledge outcome: kept, broken, expired_unresolved and disputed, with separate bond/enforcement types so public-reputation pledges do not become slashing mechanisms.
5. Revocation cascade: root and descendant bindings, required gateways, acknowledgements and status. Effective means every required receiver has enforced the revocation.
6. Trust state: local state, L0–L4 level, five evidence dimensions, decay, freshness policy and zero self-dealing bonus. Trust does not grant action authority.
7. Loyalty evaluation: leak, capitulate, posture and over-refusal rates, five agency duties, task success, harm and confidence interval.
8. Constitutional verdict: SEAL/HOLD/SABAR/VOID, per-floor outcome, human veto and no agent self-certification.
9. Signed in-toto/DSSE bundle binding the complete synthetic records with a fixture-only Ed25519 key.

The synthetic fixtures contain eleven portable records, two principal/delegation bindings, three pledge outcomes, one signed DSSE bundle and fourteen negative tests.

## 6. Privacy, freshness and interoperability

- Never publish private principal identity, private keys, signing seed, mandate contents, real beneficiary records, private oaths, incident traces or internal trust histories.
- A public key fingerprint proves a relationship to a key, not the civil identity or legal authority of a principal. Preserve the identity-assurance issuer and proof-of-control evidence separately.
- A sub-delegation must never expand capabilities, remove inherited exclusions, increase authority tier/budget or extend the parent validity window.
- Absent or stale fidelity/trust attestation is a security-relevant condition; it is not proof of compromise. Sensitive actions must fail closed or be revalidated under the declared policy.
- A cascade remains partial until every receiver in the declared receiver set acknowledges enforcement. Do not assert universal immediate revocation for gateways outside that set.
- A trust level, oath, pledge outcome or benchmark score never grants unlimited authority or proves inner motive. Authority elevation requires a new explicit human mandate.
- Keep trust-state calculations verifier-local where appropriate; share only the evidence and dimensions expressly consented to.

## 7. Non-claims

No candidate is installed or run. No real principal, beneficiary, private key, identity provider, oath ledger, trust history, wallet, escrow, TEE, ZK proof, benchmark trajectory or delegation registry was accessed. No real pledge, oath, revocation, authority change or fidelity test was executed. CI verifies synthetic contracts and a fixture-only signature; it is not a production trust service, security certification or proof of allegiance.
