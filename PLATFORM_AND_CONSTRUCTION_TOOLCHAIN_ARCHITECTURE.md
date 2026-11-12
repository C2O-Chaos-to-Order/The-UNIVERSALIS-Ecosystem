# Platform and Construction Toolchain Architecture — UNIVERSALIS

**Boundary:** Public, open and independently inspectable UNIVERSALIS / MotherThread.  
**Owner:** The UNIVERSALIS Ecosystem.  
**Source inventory:** Twelfth owner-supplied toolchain inventory, with seven infrastructure domains.  
**Status:** Open architecture and portable contract proposal implemented on this branch; third-party tools remain candidates; no production platform is claimed integrated.

## 1. Architecture purpose

This layer supplies the substrate beneath and around UNIVERSALIS intelligence, knowledge, skills, capabilities, powers and security domains. The public repository publishes inspectable contracts, synthetic fixtures and reference architectures. It must not contain C2O-private specifications, policies, identities, secrets, datasets, signing keys, build records or operational telemetry.

The seven infrastructure domains are:
1. OS, kernel and runtime substrate.
2. Application development SDKs and app runtimes.
3. Workflow construction, blueprints and build orchestration.
4. DevOps and CI/CD.
5. Observability and lifecycle control.
6. Networking and agent gateways.
7. Storage, memory, evaluation and testing.

## 2. Open candidate inventory

### OS, kernel and runtime substrate

- **khy-os:** hand-written C OS-kernel candidate combined with an agentic CLI and multi-provider AI gateway. The [PyPI project page](https://pypi.org/project/khy-os/) describes QEMU boot support and kernel/process primitives. Verify release artifacts, source repository, boot reproducibility, license, architecture and kernel security before use.
- **Agent-OS-Kernel:** owner-supplied conceptual/implementable pattern mapping OS scheduling, memory, process, storage and driver concepts onto agent infrastructure. Exact upstream source and implementation remain unpinned. Do not classify the conceptual analogy as a hardware OS kernel.
- **airisos:** owner-supplied open agent-company control-plane candidate with task orchestration, heartbeat/lifecycle, RBAC, budgets, secrets and plugin adapters. Exact canonical repository, license and deployment behavior remain unresolved.
- **MaragingLoop:** [GistNoesis/MaragingLoop](https://github.com/GistNoesis/MaragingLoop), described as a ReAct-style agent for bare-metal OS/kernel construction through compilation, VirtualBox lifecycle operations and visual inspection. It is a development tool, not itself the target OS. Any autonomous code/VM action needs sandboxing, scoped I/O and human review.

The inventory distinguishes bootable OS/kernel, OCI/container artifacts, agent runtime, agent-fleet supervisor and autonomous OS-development tooling. These are separate architectural roles.

### Application development

- **Vercel AI SDK 6:** open TypeScript development toolkit with reusable Agent and ToolLoopAgent abstractions. Review [AI SDK 6 release information](https://vercel.com/blog/ai-sdk-6) and [official documentation](https://vercel.com/ai-sdk).
- **Google Agent Development Kit (ADK):** open agent-development framework. Confirm language/runtime support against the [official documentation](https://google.github.io/adk-docs/) before pinning a TypeScript or Go version.
- **agentic-ai-sdk:** owner-supplied SDK described as built on Microsoft Agent Framework with declarative YAML, Python tool and pro-code modes. Exact package/repository, license and version need identification.
- **a2abase:** owner-supplied Python agent SDK candidate. Exact upstream, tool/integration inventory, supported providers and license need independent verification.

### Workflow construction and build orchestration

- **UnifAI:** [redhat-community-ai-tools/UnifAI](https://github.com/redhat-community-ai-tools/UnifAI), open orchestration candidate using graph/blueprint workflows, with LangGraph or Temporal execution patterns and MCP/A2A integration described by its project.
- **Primeagent:** candidate visual and code-first authoring environment. Exact project identity and release are unresolved; do not merge its identity with unrelated products named Prime.
- **AAMAD:** owner-supplied context-engineering and multi-agent framework candidate associated with claude-agent-sdk. Exact source and license remain unresolved.
- **Microsoft Agent Framework:** [microsoft/agent-framework](https://github.com/microsoft/agent-framework), open SDK/runtime candidate for building and orchestrating agents. Pin exact package, language and maturity of the selected feature.

A blueprint format is an interchange contract only after node, edge, condition, expression, state and error semantics are mapped. A generic YAML graph is not automatically executable by every workflow engine.

### DevOps and CI/CD

- **Harness MCP server:** [harness/mcp-server](https://github.com/harness/mcp-server), an MCP interface for Harness platform operations. Its use requires explicit tool allowlisting and scoped credentials.
- **Semaphore MCP server:** candidate CI/CD data/action interface. Pin the official implementation, permissions and supported operations before adoption.
- **DuploCloud:** agentic DevSecOps/infrastructure automation candidate. Treat its cloud/service components as external vendor integrations unless a verifiable self-hosted component is identified.
- **AWS DevOps Agent:** vendor-operated DevOps investigation/automation candidate. Its [MCP integration documentation](https://docs.aws.amazon.com/devopsagent/latest/userguide/configuring-integrations-and-knowledge-connecting-mcp-servers.html) specifies supported connectivity and authentication requirements. It is not an open, independently self-hosted runtime.

### Observability and lifecycle control

- **Riva:** [riva-labs-ai/riva](https://github.com/riva-labs-ai/riva), local-first discovery, lifecycle, resource and event observability candidate. The project explicitly says it observes agent behavior rather than executing agent actions.
- **AgentOps Replay** and **lumen-ai:** owner-supplied replay, causal-trace, failure and spend-observability candidates. Exact upstream project, license, replay semantics, data collection and export behavior remain unresolved.

Keep event observation, trace export, deterministic replay, causal reconstruction, process control and policy enforcement as separate capabilities.

### Networking and agent gateways

- **agentgateway:** open AI-native gateway project hosted under Linux Foundation/Agentic AI Foundation governance; supports gateway/data-plane patterns for model, MCP and A2A traffic. See [project information](https://www.solo.io/products/agentgateway) and [documentation](https://docs.solo.io/agentgateway/standalone/latest/documentation/about/introduction/). Comparative performance figures remain benchmark claims, not UNIVERSALIS acceptance criteria.
- **IBM ContextForge:** [IBM/mcp-context-forge](https://github.com/IBM/mcp-context-forge), open registry/proxy candidate federating MCP, A2A and REST/gRPC APIs with discovery, policy, authentication, rate limits and observability.

MCP tool calling and A2A agent interaction are complementary but distinct protocol surfaces. Neither protocol alone supplies trusted identity, authorization, consent or safe execution.

### Storage and memory

- **zleap-sag:** owner-supplied composable relational/vector storage candidate. Pin the exact package/repository, supported backends and license. Do not assume it is identical to the separate [Zleap-AI/SAG](https://github.com/Zleap-AI/SAG) repository without source evidence.
- **memg-core:** owner-supplied Qdrant/Kuzu vector-plus-graph storage candidate. Exact upstream and implementation remain unresolved.
- **Azure Cosmos DB:** managed cloud database candidate with vector search, semantic cache and application-state integrations. It is not open-source or self-hosted; record it as an external managed-service option rather than a UNIVERSALIS-owned storage implementation. See [Azure Cosmos DB vector search documentation](https://learn.microsoft.com/azure/cosmos-db/vector-search).

Storage abstraction must not erase differences in consistency, transactions, index freshness, vector metric, graph semantics, retention, deletion and exportability.

### Evaluation and testing

- **Strands Evals:** [strands-agents/evals](https://github.com/strands-agents/evals), open evaluation SDK candidate for output, trajectory, tool-use and interaction evaluation.
- **Inspect:** [UK AI Security Institute Inspect](https://inspect.aisi.org.uk/), open evaluation framework with agent/task/scorer abstractions and sandbox integrations.
- **MCPEval:** MCP-specific task generation and verification candidate. Pin exact canonical repository/release before treating it as a selected dependency.

Evaluation outputs should bind subject build digest, suite/version, dataset/version/digest, environment, parameters/seed, counts, result, evidence and reproducibility. A test harness is not a guarantee that an agent is safe or capable outside the tested distribution.

## 3. Shared interoperability contracts

The shared v1 schema defines nine sanitized portable record types:
1. OS/container artifact metadata, including bootable-versus-container distinction.
2. Runtime profile, isolation boundary, lifecycle and protocol set.
3. Agent Skills manifest reference and MCP tool-contract references.
4. Workflow blueprint graph, approval mode and execution-scope reference.
5. CI/CD event, source commit, test totals, artifact digest and provenance.
6. Redacted OpenTelemetry-compatible observation metadata.
7. Network route and MCP/A2A/HTTP/gRPC authentication, authorization and egress references.
8. Storage interface metadata for relational/vector/graph/object/document/cache/workflow-state backends.
9. Evaluation receipt with subject, artifact, dataset, environment, result counts and reproducibility.

The public fixtures use synthetic references only. They do not contain C2O private source, policy, identity, key, build, telemetry, incident or evaluation data.

## 4. Protocol and interoperability cautions

- OCI container image/artifact format is not a boot protocol and does not make a container image equivalent to a bootable OS.
- MCP provides tool/context interaction; A2A supports agent-to-agent task and collaboration patterns. A runtime may expose one, both or neither.
- Agent Skills `SKILL.md` describes a skill package and its instructions/metadata; it does not grant permission to execute its tools.
- Blueprint schema compatibility requires explicit engine adapters and semantic equivalence tests.
- OpenTelemetry schemas and trace IDs do not make raw telemetry safe to export. Apply data minimization and redaction.
- Vector, graph and relational storage interfaces need typed capability negotiation; a shared API cannot assume identical query or consistency semantics.
- Evaluation receipts are evidence about a bounded test run, not certifications or universal safety claims.

## 5. Source and claim discipline

Canonical source, version, license, maintenance, dependencies, security posture, data flow and compatibility must be pinned before adoption. Items explicitly marked unresolved are preserved as owner-supplied candidates, not silently replaced by similarly named projects.

Supplier or source-reported claims about download counts, numbers of integrations, framework coverage, latency, memory, throughput, test count or accuracy must be tied to exact releases and reproducible measurements before use as acceptance criteria.

## 6. Implementation status and limits

Implemented on this proposal branch:
- shared JSON Schema v1;
- nine synthetic positive contract records;
- semantic validator and ten negative cases;
- public CI workflow for contract validation.

Not implemented or claimed:
- no UNIVERSALIS bootable OS/kernel or operating-system build;
- no third-party SDK, agent OS, workflow engine, gateway or CI/CD product installed by this change;
- no live agent discovery, event replay or OTLP ingestion;
- no database or memory store provisioned;
- no production workflow or deployment executed;
- no external Strands/Inspect/MCPEval benchmark run;
- no digital signature creation/verification or production provenance service.

CI validates schemas and the synthetic semantic test cases only. It does not establish product suitability, runtime interoperability, production security, performance, compliance or deployment.
