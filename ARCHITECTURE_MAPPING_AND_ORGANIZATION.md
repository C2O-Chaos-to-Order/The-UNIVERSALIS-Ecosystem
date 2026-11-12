# Architecture Mapping, Matrices, Organization, and Repository Structure

**Status:** First portable architecture graph and deterministic semantic validator implemented in this branch. Tool descriptions and capability claims below preserve the supplied mapping document; products remain research candidates/reference patterns pending independent verification.

## 1. Architectural purpose and boundary

UNIVERSALIS needs open, inspectable mapping instruments. C2O needs private, deterministic, traceable maps that support impact analysis and authority-aware change review. Both need portable structural contracts, not shared private graph contents.

A map is a versioned evidence-bearing model, not a diagram alone. Source facts, inferred relationships, and proposed designs must remain distinguishable. Accepted architecture must be distinct from proposals under review.

## 2. Architectural mapping and visualization

**UNIVERSALIS candidates:** Kula (Git/RDF knowledge graph, Turtle/JSON-LD/SPARQL); reponova (persistent code graph and MCP query tools); AnaxiGraph/AnaxiMCP (semantic repository graph with source/inference/proposal distinction); GRASP (multimodal repository graph and architecture views); wikifier (agent-facing repo wiki and health/dependency map); FlowForge (evidence-cited LLM/MCP/API flow graph); MokuGraph (JSON-driven architecture visualization component).

**C2O candidates:** Velorum (private enterprise structure/dependency graph and impact system mapper); @datasynx/agentic-ai-cartography (read-only MCP system landscape); WorkBraid (local Git-backed proposal/review workbench separating proposals from accepted architecture).

## 3. Matrix and dependency tools

**UNIVERSALIS:** FlowForge critical-path matrix; wikifier file-health/dependency matrix; reponova impact/community analysis; Kula graph-diff and blast-radius analysis.

**C2O:** Velorum impact matrix; GRASP security/dependency matrix; agentic-flow dependency-graph partitioning for delegation and multi-agent task distribution.

## 4. Organizational structure and hierarchy

**UNIVERSALIS candidates:** Agentopology (.at declarative topology compiler); QuinnAI (worker/org tree and OKR cascade); agents_Inc (CEO/CoS/Lead/Worker contract-and-review pattern); Paperclip (multi-company org charts, budgets, governance, audit, rollback); AGI-Super-Team (portable role packs and outcome team manifests).

**C2O patterns:** Paperclip private org/cost control plane; QuinnAI private hierarchy and delegation; agents_Inc authority-and-review pattern. These require private policy and identity mapping at the C2O boundary.

## 5. Repository structure and taxonomy

**UNIVERSALIS candidates:** ai-native-repo-template (ANR v0.2), gitagent, omni-agents-cli.

**C2O patterns:** ANR context budget extended with authority and audit classes; gitagent for private version-controlled agent definitions and authority-gated tools.

## 6. Ecosystem mapping and discovery

**UNIVERSALIS candidates:** ai-ecosystem-map; VisualAgents; Agent Fabric / Agent Visualizer; Reco Graph; AgentFolio.

**C2O patterns:** private ai-ecosystem-map instance for governed capability sharing; VisualAgents for delegated-session observation; Reco Graph pattern for identity/permission/connection/action audit mapping.

## 7. Shared, scope-limited contracts

- MokuGraph JSON schema for rendering structural maps with ecosystem-specific data.
- Draw.io XML and the supplied @drawio/mcp integration pattern.
- WorkBraid proposal format; proposals and acceptance policy remain ecosystem-specific.
- Agentopology .at topology source, with ecosystem-specific compiler targets.
- Paperclip portable company template, with private C2O organization state excluded.
- Dependency-graph interchange schema (nodes, edges, weights, provenance).
- ai-ecosystem-map discovery schema; VisualAgents event format; Reco Graph identity/permission/action schema.

Shared contracts carry structural metadata only. They must never serialize C2O private credentials, authority tokens, policies, private source annotations, or restricted operational state.

## 8. Minimum architecture graph contract

The first executable increment is schemas/architecture/architecture-graph.v1.schema.json with a synthetic fixture in examples/architecture/architecture-graph.json and dependency-free checks in .github/scripts/architecture_graph_contract.py.

It records versioned snapshots, scope/visibility, typed nodes, typed provenance-bearing edges, matrix entries, and separate architecture proposals. It rejects dangling edges, duplicate IDs, public confidential/secret nodes, C2O Controlled authority in public graphs, unreviewed/self-approved accepted proposals, and credential-bearing fields.

## 9. Evidence and limitations

| Item | Status |
|---|---|
| Supplied mapping/matrix/org/repository/ecosystem candidate inventories | Documented |
| Portable graph schema and synthetic fixture | Implemented in this branch |
| Dependency-free validator and negative tests | Implemented in this branch; CI passed — see ARCHITECTURE_MAPPING_VALIDATION.md |
| Live repository/code/system discovery adapters | Not implemented |
| Matrix computation, impact analysis, topology compilation | Not implemented |
| Draw.io/MokuGraph integration | Not implemented |
| Candidate source/license/security/performance verification | Pending |
| Full JSON Schema 2020-12 validation | Pending |
