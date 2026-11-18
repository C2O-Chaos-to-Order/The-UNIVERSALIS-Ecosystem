# Governed Execution and Worker Lifecycle Service
## Public UNIVERSALIS architecture specification v0.1.0

**Identifier:** UNI-EXEC-ARCH-001  
**Version:** 0.1.0  
**Date:** 2026-11-18  
**Status:** Proposed product architecture; implementation and independent review pending  
**Boundary:** Public, provider-neutral, independently operable  
**Research counterpart:** [UNI-DP-11 — Governed Execution, Worker Lifecycle and Thermodynamic Accounting](https://github.com/C2O-Chaos-to-Order/Research-for-the-UNIVERSALIS-Ecosystem/blob/integrate/master-2026-11-16/RESEARCH/DOMAIN_PACKS/UNI-DP-11_Governed_Execution_Worker_Lifecycle_and_Thermodynamic_Accounting_v0.1.0.md)

## 1. Architectural intent

The Governed Execution and Worker Lifecycle Service (the Forge service) is the public product architecture for bounded computational execution. It separates request intake, readiness, authorization, resource reservation, queue admission, worker supervision, observation, cancellation, persistence, independent evaluation and release.

It must be possible to determine from a run record:
- what was requested, by whom and within which declared scope;
- which independent gates admitted or withheld work;
- which worker and runtime were assigned;
- what resource budget was reserved and consumed;
- whether the worker was queued, starting, observed alive, paused, stopping or confirmed terminated;
- which candidates were generated and persisted;
- which independent evaluation and release decisions remain outstanding.

The service does not infer consciousness, will, truth, quality, ethics or permission from activity, heat, color, throughput or resource consumption.

This specification is an architecture contract. It does not claim that the service has been coded, deployed, security-tested or authorized for production.

## 2. Design principles

1. **Fail closed:** unknown, missing, expired, stale or contradictory mandatory evidence cannot silently become PASS.
2. **Independent authority:** the executor cannot grant its own authorization, invent readiness, increase its own hard budget or accept its own candidate.
3. **Observed lifecycle:** queue admission, process start, worker liveness, stop request and termination are different facts.
4. **Enforceable limits:** a local counter is not evidence that an external CPU, memory, accelerator, monetary or energy ceiling was enforced.
5. **No-new-work on revocation:** revoked or unknown required authority blocks consequential new work and enters the declared stop/escalation path.
6. **Candidate separation:** generated and persisted output remains unverified until an independent evaluator records a scoped decision.
7. **Portable contracts:** provider-specific mechanisms sit behind versioned interfaces and do not become implicit authority.
8. **Inspectable operation:** each state, control and external effect has provenance, limits and reviewable evidence.
9. **Accessible status:** color, animation, sound or spatial presentation never becomes the only source of state or control.
10. **Privacy by boundary:** public instances are fully operable without private credentials, private policies, private records or non-public control-plane access.

## 3. Component architecture

The logical service is decomposed into separately replaceable components:

| Component | Responsibility | Must not do |
|---|---|---|
| Request API | Validate identity, operation, scope, limits and idempotency key | Treat a request as authorization |
| Policy decision adapter | Obtain scoped authorization and revocation decisions | Delegate final authority to the worker or model |
| Readiness adapter | Verify declared environment and dependency readiness | Reuse a stale or unrelated health signal |
| Reservation adapter | Reserve, consume and reconcile typed resources | Convert synthetic units to joules without a measurement contract |
| Admission controller | Evaluate required gates and create an admitted queue item | Start a worker before all mandatory checks pass |
| Scheduler | Select a compatible worker under quota, fairness and tenant constraints | Treat queued work as running |
| Worker supervisor | Start, pause, stop and observe the identified worker using a supported runtime | Claim termination without independent observation |
| Telemetry/attestation adapter | Supply worker-specific status and observation provenance | Promote missing telemetry to idle |
| Event ledger | Append lifecycle events and preserve provenance | Rewrite historical evidence silently |
| Candidate store | Persist content-addressed candidate artifacts and metadata | Mark a candidate accepted |
| Evaluation interface | Receive independent evaluation decisions | Be controlled by the candidate generator |
| Release interface | Apply separate publication, transfer or deployment authorization | Infer release permission from acceptance alone |
| Operator interface | Expose state, controls, limits and evidence | Override policy or represent animation as activity |

The diagram is logical, not a statement that one process or deployment topology is required. Components may be colocated for a local installation if trust boundaries and separation of authority remain enforceable.

## 4. Admission and gate contract

### 4.1 Three core gates

The necessary admission rule is:

**Generate ⇒ Ready = PASS AND Authorized = PASS AND BudgetAvailable = PASS.**

This expression is necessary, not sufficient. A start decision also requires operation-specific worker availability, runtime compatibility, safety holds, valid input/scope, telemetry and output-handling checks.

Each gate decision includes:
- gate name and policy/version;
- decision ID and issuer/source identity;
- explicit status;
- observed-at and expiry/freshness information;
- scope and subject to which the decision applies;
- evidence reference or reason;
- revocation or supersession information where supported.

Statuses are PASS, FAIL, UNKNOWN, ERROR, REVOKED, EXPIRED and STALE. NOT_APPLICABLE is permitted only for an explicitly optional gate whose contract allows it. It is never a substitute for one of the three core gates.

The controller checks gate evidence at queue admission, immediately before worker start, before consequential steps, before new capabilities or data boundaries, before reservation increments, before resume, and before output transfer or release.

### 4.2 Authority isolation

The requester, policy authority, readiness source, budget authority, scheduler, worker, observer, candidate evaluator and release authority are separately identified. One implementation may host more than one role only where the assurance design demonstrates separation, least privilege, tamper-evident records and an independent path for critical decisions.

The model or agent may propose a request and explain its intended work. It cannot turn its own proposal into permission. The worker may report what it believes happened; supervisor and external evidence are needed to substantiate consequential lifecycle claims.

## 5. Request, run and resource contracts

A request is immutable after admission except through explicit, versioned amendments. A run record binds the request to the actual execution.

Minimum request fields:

- request ID, requester ID, tenant/isolation-domain ID;
- operation, declared scope and input references;
- component and requested version;
- output class and handling policy;
- requested worker capabilities and runtime constraints;
- maximum runtime and resource ceiling;
- authorization and readiness decision references;
- reservation request, resource class and unit;
- cancellation, retry, cleanup and idempotency policy;
- telemetry policy, persistence policy and sharing restrictions.

Minimum run fields:

- run ID and request digest;
- admitted policy and gate-decision references;
- scheduler and worker identities;
- runtime image/configuration digests and effective capabilities;
- reservation identity, reserved/consumed/remaining quantities and expiry;
- state and ordered event references;
- worker observations and source identity;
- candidates, persistence references and evaluation references;
- stop reason, termination evidence, cleanup status and unresolved side effects.

Resource reservation must distinguish reserved, consumed, released and reconciled quantities. Units are typed: CPU time, memory, accelerator allocation, storage, network transfer, tokens, monetary cost and joules are not interchangeable. Physical energy claims require a meter, declared measurement boundary, calibration/provenance and uncertainty.

## 6. Lifecycle state machine

The service uses explicit states at minimum:

requested → queued → starting → running

and, where applicable:

running → pausing → paused → running

Any active state may enter stopping. A terminal outcome may be cancelled, stopped, failed, timed_out, budget_exhausted, authorization_revoked, finished_unverified or candidate_withheld. A candidate may separately reach candidate_persisted. This is not a single linear enum: run state, worker observation, output persistence, evaluation and release status are separate fields.

### 6.1 State rules

- REQUESTED is not admitted.
- QUEUED means admitted work is waiting; it is not a running worker.
- STARTING means a start operation was requested; it does not prove that the worker is alive.
- RUNNING requires a fresh observation of the identified worker in an allowed running status and current gate/reservation checks.
- TELEMETRY_UNKNOWN means activity cannot be truthfully established. It must not be displayed as idle.
- PAUSED requires observation of the worker's paused status and a valid pause transition.
- STOPPING means no new consequential work is allowed and termination is not yet confirmed.
- STOPPED/CANCELLED for a started worker requires fresh, worker-specific termination evidence. A not-started queued request may be cancelled as never started, without inventing a worker termination event.
- FINISHED_UNVERIFIED means execution ended; it is not independent acceptance.
- CANDIDATE_PERSISTED means durability is confirmed by the storage contract; it still does not imply acceptance.

### 6.2 Cancellation and termination

Cancellation first closes the no-new-work boundary. The supervisor then signals the actual worker using runtime-specific controls. The service remains STOPPING while the worker is alive, telemetry is missing, or termination evidence is stale. It records the exact evidence source and time when termination is confirmed.

Worker termination, child-process termination, external service completion, rollback, cleanup and reversal of side effects are distinct claims. A process exit does not prove an external operation was reversed. Uncooperative workers or remote services require explicit escalation and residual-risk records.

### 6.3 Restart and retry

A terminal run is never revived in place. A retry creates a new run identity and records its parent/attempt relationship. Idempotency keys and external-effect ledgers prevent duplicate effects where the downstream service supports that guarantee. When exactly-once execution cannot be guaranteed, the interface must describe the actual delivery semantics and reconciliation protocol.

## 7. Distributed orchestration and failure containment

The scheduler and workflow layer must account for:
- queue fairness, priorities, quotas, backpressure and capacity limits;
- fan-out/fan-in, dependencies and bounded concurrency;
- tenant isolation and transitive tool capabilities;
- retry storms, recursion, circular dependencies and restart amplification;
- deadlock, livelock, starvation and priority inversion;
- common-mode policy or telemetry failure;
- partial failure across worker, queue, storage and external services;
- cancellation cascades and cleanup interference between tenants;
- portfolio-wide resource ceilings across individually valid jobs.

Concurrency and resource accounting are enforced at the resource-owning boundary, not solely by the coordinator. Global ceilings must be evaluated in addition to per-run ceilings. Recovery mechanisms have their own rate limits and budgets.

## 8. Security, privacy and trust boundaries

The model is not the reference monitor. Authentication, authorization, scope enforcement, network egress, filesystem access, process isolation, secret delivery, rate limits and kill controls must be enforced by independently testable software or hardware controls outside model reasoning.

Required design work includes:
- per-run least-privilege identity and short-lived capabilities;
- host/guest isolation selected for the threat model and runtime;
- explicit network, filesystem, device and tool permissions;
- protected secrets and no secrets in prompts, logs or candidate artifacts;
- tenant-separated queues, storage, telemetry and audit views;
- signed or otherwise authenticated worker observations where the threat model requires them;
- tamper-evident event history with defined trust roots;
- fail-closed behavior on policy, telemetry, broker or supervisor failure;
- resource exhaustion, denial-of-service and recursive-work controls;
- data retention, deletion, export and incident processes.

A hash proves identity relative to a digest, not truth or authorship. A signature proves only the signer and payload relationship supported by its key and trust process. A policy receipt does not prove that the kernel, hypervisor or external service enforced that policy.

## 9. Thermodynamic and performance separation

Physical thermodynamics belongs to a separate measurement/accounting interface.

For a closed system, with heat positive into the system and work positive on the system:

**ΔU = Q + W_on**

Where work is defined positive by the system, translation is explicit: **W_on = −W_by**.

For an open control volume, declared matter-flow energy terms and relevant kinetic/potential energy terms are included. For a declared isolated total, **ΔS_total ≥ 0**. Local subsystem entropy may decrease while the complete isolated total satisfies the second law.

The scheduler's synthetic units, token counts, throughput, CPU utilization and monetary billing are not physical energy measurements. Neither heat nor entropy measures truth, accepted value, creativity or permission. The physical accounting adapter records boundary, units, temperatures, included reservoirs, method, uncertainty and provenance.

Sunken energy costs or completed work are not reasons to bypass cancellation or acceptance. The system should optimize avoidable waste while preserving safety, correctness, accessibility, privacy, resilience and user welfare.

## 10. Quantum workload boundary

A quantum or hybrid backend adapter may expose submission, calibration readiness, reservation, shot count, queue position, execution observation, cancellation request and measurement-complete events. Quantum-state preparation, evolution, probability and measurement validity remain owned by domain-specific quantum tooling and evidence.

Operational worker states are classical control-plane states. A queued QPU job is not a superposition of running and stopped; missing backend telemetry is not quantum uncertainty. A classical service test cannot claim physical QPU evidence.

## 11. Operator experience and accessibility

The operator surface exposes request, scope, gate state, worker/runtime identity, reservation and consumption, current observation, cancellation state, candidate count, persistence, independent evaluation and release status.

It must provide:
- literal textual states and reasons;
- keyboard-operable controls and focus handling;
- screen-reader labels and live-region behavior;
- reflow/zoom without loss of controls or status;
- non-color status encoding and adequate contrast;
- reduced-motion support;
- a nonvisual route for every essential action;
- privacy controls for sensitive output and tenant metadata.

“Active” must not collapse queued, starting, running and telemetry-unknown into one ambiguous indicator. Animation and color may reinforce a verified state but cannot establish it.

## 12. Interfaces and data flow

Public versioned adapters are proposed for:

1. Request intake and idempotency.
2. Readiness decisions.
3. Authorization and revocation.
4. Reservation and quota enforcement.
5. Scheduler and worker selection.
6. Process/container/VM supervisor.
7. Worker telemetry and termination observation.
8. Lifecycle event ledger.
9. Candidate artifact storage.
10. Independent evaluation and acceptance.
11. Physical energy measurement and performance accounting.
12. Publication/transfer/release control.

Each interface defines schema version, identity, scope, owner, expiry, failure semantics, evidence provenance, rate and resource bounds, and compatibility. Adapters may be replaced without changing the semantic contract. No adapter receives ambient access to unrelated tenants or systems.

## 13. Implementation sequence and exit gates

| Increment | Deliverable | Exit evidence |
|---|---|---|
| P0 — Contract | Request/run/gate/worker/observation/reservation/cancellation/candidate schemas | Schema review, negative fixtures and compatibility contract |
| P1 — Reference model | Deterministic state machine and thermodynamic helper isolated from runtime adapters | Unit tests, boundary tests, transition coverage and reproducible outputs |
| P2 — Local sandbox | Disposable isolated worker runtime with external supervision | Isolation review, process-tree termination proof, resource ceiling tests and cleanup evidence |
| P3 — Policy and budget adapters | Independent readiness, authorization, revocation and enforceable reservations | Negative authorization, expiry, revocation, overspend and adapter-failure tests |
| P4 — Queue and workflow | Bounded worker pool, fairness, retry policy and multi-tenant isolation | Concurrency, load, starvation, duplicate-effect and cascade tests |
| P5 — Evidence and candidates | Durable event ledger, candidate storage and independent evaluation handoff | Integrity, retention, replay, persistence and acceptance-separation tests |
| P6 — Operator surface | Accessible status, control and evidence presentation | Keyboard, screen-reader, zoom, reflow, contrast, non-color and privacy review |
| P7 — Portability and optional adapters | Provider-neutral manifests, migration and optional quantum/energy interfaces | Cross-provider compatibility and revalidation evidence |

No increment inherits acceptance from the previous one. Runtime deployment, public release and any external connection require explicit separate approval.

## 14. Required acceptance scenarios

The implementation test suite must include at least:
- missing or UNKNOWN readiness, authorization and budget;
- truthy non-Boolean gate values and stale/future decision timestamps;
- authorization revoked while queued, starting, running and paused;
- telemetry missing, stale, mismatched, duplicated and reordered;
- start command accepted while worker never starts;
- worker alive after cancellation and stale NOT_ALIVE messages;
- hard budget ceiling reached between steps;
- reservation expiry and resource broker outage;
- deadline expiry and uncooperative worker;
- pause/resume with authorization or budget changes;
- duplicate request, retry, replay and external side effect;
- partial workflow failure and unrelated-workflow cancellation isolation;
- recursive tool invocation and transitive privilege;
- persisted candidate incorrectly presented as accepted;
- migration with expired identity or revoked capability;
- thermodynamic boundary, sign convention and entropy completeness;
- interface state lost without color, animation or pointer;
- private data or secret leakage across tenant and public/private boundaries.

All findings must retain test ID, source revision, environment, input, expected result, actual result, logs or artifact digests, limitations and disposition.

## 15. Operational evidence and status vocabulary

Use separate values for implementation status, test status, evidence status, review status, owner acceptance, release authorization and runtime authorization. Suggested states include PROPOSED, IMPLEMENTED, TESTED, VERIFIED, UNVERIFIED, FAILED, UNRESOLVED, ACCEPTED and AUTHORIZATION_PENDING, with field-specific definitions.

Never compress these into one score or badge. “Tests passed” must name the exact suite and revision. “Worker stopped” requires the declared observation evidence. “Candidate accepted” requires an independent decision. “Released” requires its own release record.

## 16. Current disposition

This file establishes the proposed public product architecture for the service. It does not add runnable service code, schemas, operating-system hooks, policy adapters, resource brokers, worker pools or runtime dependencies. It does not authorize production execution, access to external systems, publication or deployment.

The linked research package supplies the public research questions, evidence requirements, thermodynamic distinctions, failure analysis and proposed tests. Product implementation may proceed only through reviewed requirements, explicit contracts, threat modelling, isolated tests and separate owner authorization.

**Research informs design. Evidence supports claims. Authorization governs consequential change.**
