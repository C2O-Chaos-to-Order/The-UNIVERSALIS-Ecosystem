# Multi-Layer Agent, OS and AI Unification Architecture

**Inventory:** 24th owner-supplied inventory — Agent, OS and AI Unification  
**Date:** 2026-11-12  
**Role:** UNIVERSALIS MotherThread — open, inspectable and independently operable architecture.  
**Status:** Source-qualified proposal; no candidate is adopted by inclusion.

## Design objective

Make heterogeneous operating systems, models, frameworks, execution surfaces and hardware resources interoperable through explicit adapters and versioned contracts. This is not a claim that one runtime can already make every OS, model, accelerator or agent behave identically. Kernel semantics, hardware features, modalities, lifecycle, security boundaries, cost and failure behavior remain different.

**Unification means composable interoperability without false equivalence.** UNIVERSALIS should publish pluggable interfaces and compatibility profiles tested for specific producer/consumer versions.

## Four layers

| Layer | Function | Public candidate examples | Hard limit |
|---|---|---|---|
| Runtime/substrate | Host, isolate and expose runtime capabilities | Qualixar OS, khy-os, Formicx, SleekAI Cortex | OCI artifacts do not create universal kernels, drivers, hypervisors or accelerator equivalence. |
| Orchestration/composition | Coordinate agents, harnesses, skills, workflows and state | Omnigent, Agno AgentOS, LAR-OS; AgentOS/nexus unresolved | Adapters do not prove equivalent state, lifecycle, tools or zero-change portability. |
| Model gateway/routing | Normalize inference access, route requests and meter budgets | OmniRoute, Glob.AI OS, g8e | API compatibility does not establish model parity, privacy, residency or sovereignty. |
| Local execution/computer use | Connect agents to host tools, desktops, browsers and fleets | aevra, OmniPilot, Shinken | MCP is not permission; computer-use action schemas are not OS ABIs or security boundaries. |

## Protocol semantics

| Interface | Actual role | Not equivalent to |
|---|---|---|
| OCI image/runtime | Container artifact and runtime configuration/lifecycle | Host-kernel independence, arbitrary OS virtualization or accelerator equivalence |
| MCP | Client/server tools, resources and prompts using JSON-RPC; stdio and Streamable HTTP | A2A delegation or execution authorization |
| A2A | Agent-to-agent discovery, tasks, collaboration and artifacts | MCP tool-server semantics |
| ACP | Agent-to-client integration | A2A |
| Agent Protocol REST | Client-to-agent runs, tasks, steps and artifacts | MCP, A2A or Agno Python adapter |
| Agno AgentProtocol | Agno-specific Python framework adapter interface | Neutral cross-vendor wire protocol |
| OpenAI-compatible inference API | Selected model-access operations | Model/feature parity, privacy, data residency or sovereignty |
| Qualixar Universal Command Protocol | Qualixar product command surface | External standard adopted by all runtimes |
| g8e GovernanceEnvelope | g8e project-specific transaction/governance binding | Universal cryptographic interchange standard |
| Shinken ACI | Shinken-specific computer-use action/observation format | OS ABI, safety certification or permission |

MCP is client-to-server tool access; A2A is agent-to-agent collaboration; ACP is agent-to-client. The Agno Python interface and Agent Protocol REST project are separate again.

## Candidate qualifications

### Runtime/substrate
- **Qualixar OS:** upstream describes 15 providers, 13 topologies and 25 CLI commands; these are version-sensitive maintainer claims. Its changelog records FSL-1.1-ALv2, a source-available license with competing-use restrictions; do not call it unrestricted OSI-open source.
- **khy-os:** PyPI describes a hand-written C kernel, agentic CLI and 16-backend gateway. It is Beta/source-available with non-commercial terms absent written permission; not an unrestricted commercial OSS dependency.
- **Formicx:** PyPI identifies MIT, version 0.1.0 and Alpha. Linux-oriented agent process/control layer with PID mapping, ACL, mDNS and MCP claims; not a universal kernel.
- **SleekAI Cortex:** package description describes model/harness dispatch, budgets/context, DAG execution and validation. Pin release/license/platform before adoption; no universal OS or hardware abstraction established.

### Orchestration/composition
- **Omnigent:** independent Apache-2.0 open meta-harness; distinct from Databricks' managed service.
- **Agno AgentOS:** Agno runtime/API/MCP service with adapters for selected frameworks. Multi-framework support was announced as Beta; Agno AgentProtocol is Agno-specific.
- **AgentOS (nexus-agentos):** canonical source, owner, release and license not established; keep unresolved.
- **LAR-OS:** located MIT Hugging Face artifact describes Anthropic-to-Gemini tool-call translation. Broader multi-node/delegation claims need distinct source evidence.

### Gateway/routing
- **OmniRoute:** MIT public gateway; upstream currently advertises 375 providers and 1,400+ models. Catalog counts are not conformance measures; compression savings require workload-specific measurement.
- **Glob.AI OS:** commercial Globant offering announced 2026-10-27; vendor reports multi-model governance, identity, lifecycle, budgets and audit. Not an open-source router; own-cloud deployment alone does not prove sovereignty.
- **g8e:** public project describes a Gateway/Operator model and signed governance envelope. Treat as a project-specific reference pending independent security review and release-pinned tests.

### Local execution/computer use
- **aevra:** public local MCP execution/aggregation gateway with path/command policy, approval and audit; tool counts and full-host mediation must be tested.
- **OmniPilot:** MIT public computer-use agent claiming Windows/macOS/Linux and risk-tiered actions; not an OS virtualization layer.
- **Shinken:** typed ACI, scoped sandbox and checkpoint/fork/resume design. Its design distinguishes local/reference implementation from future production hardening and broader cross-OS fleet support.

## Shared contract and acceptance

The schema and synthetic fixture describe runtime/platforms, framework adapters, orchestration profiles, model gateways, local execution, protocol bindings, component-assimilation proposals and conformance evidence. Every portable record has authority_effect = none. Product interfaces remain product interfaces; only formally defined protocols are labelled standards.

Accept a component only after canonical source, immutable release/commit, license, SBOM/dependencies, OS/architecture coverage, feature matrix, lifecycle/error/cancellation semantics, external tool/action scoping, credential isolation, egress/revocation, budgets, failure behavior, positive/negative fixtures, compatibility tests and independent review.

Container image portability is not host-kernel compatibility. Accelerator profiles need device-specific numerical, memory, scheduling and transfer tests. Model profiles need modality, tool-call, structured-output, streaming, context and cancellation tests. Computer use needs host/session scope, human takeover and independent containment. Sovereign operation needs data-flow/residency, provider-egress, identity, enforcement and revocation evidence.

## Non-claims

No candidate is declared installed or integrated. No OS/kernel was booted, model downloaded, private deployment run, remote fleet controlled, QPU job submitted or robot actuated as part of this inventory. Portable schema/fixture/validator authorship does not prove product behavior, security, interoperability or authority.