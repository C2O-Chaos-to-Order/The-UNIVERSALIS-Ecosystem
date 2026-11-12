# UNIVERSALIS open simulation architecture

**Inventory:** 22nd toolchain source — Simulation (2026-11-12)  
**Role:** UNIVERSALIS MotherThread; open, inspectable and independently replayable simulation instruments.  
**Status:** candidate research plus portable contract prototype; no candidate is adopted by this inventory.

## 1. Open instrument inventory

### Agentic execution and RL
- **OpenEnv** — open framework with Gymnasium-style reset(), step(), state(), sync/async WebSocket support, Dockerized environments and a separate MCP production-tool mode; upstream currently advertises 40+ environments. The isolation policy of each Docker environment must be inspected.
- **Agent World Model (Snowflake Labs)** — ICML 2026 paper and source describe 1,000 executable SQL-backed synthetic tool-use environments exposed over MCP. This is controlled synthetic RL infrastructure, not external-world fidelity evidence.
- **YAIFS** — candidate for MCP-mediated agent-driven fog/continuum simulation; exact canonical upstream/release was not pinned, so it remains unresolved.

### Social and multi-agent
- **AgentSociety 2** — Apache-2.0, current v2.11.0 docs, async agent/social-science runtime and append-only JSONL replay. Documentation describes an MCP literature-search integration; that should not be inflated into a claim that all simulation controls are native MCP tools. Replay output and resume checkpoints are distinct.
- **GASim** — ACL 2026 paper on graph-accelerated hybrid LLM/ABM social simulation. The paper reports 9.94× speedup and less than 20% baseline token use for its evaluated setup; this is study-specific, not a general performance guarantee or proof of predictive validity.
- **AgoraSim** — 2026 paper-level hybrid ABM for scenario-oriented social reaction analysis and structured decisions. A maintained, authoritative public code release was not pinned in this review.
- **Concordia** — open-source generative social-simulation library; requires an LLM and an embedding configuration. The supplied 38-template no-code product claim was not verified in upstream documentation.

### Monte Carlo and decision analysis
- **simengine-mcp** — candidate described as an MCP Monte Carlo/decision server. Exact primary upstream, release and license were not independently pinned; the supplied tool count, zero-dependency claim, 2,819 historical forecasts and CVaR/chance-gate details remain unverified.

### Physics, PDE and FEM
- **openPASO** — current name for the project formerly published as OASiS; MIT MCP server with nine FEM/multiphysics solver integrations, verification support and cross-code coupling. OASiS is not a separate current platform.
- **AgentFEM** — open-source Python FEM workflow, Apache-2.0 package metadata and Python 3.11+; pin aligned package, docs and source versions.
- **PDE-Agents** — research prototype using local open LLMs, LangGraph, DOLFINx/FEniCSx and GraphRAG. Project-reported performance requires independent reproduction with exact solver, mesh, data and hardware.
- **PhysBox** — browser-based simulation tools with an MCP companion. Current website advertises 256 MCP tools across Volt, Mesh, Etch and Flux (Flux is preview); older README counts and availability differ. Preserve release/date when citing counts.
- **Genesis-Gemini-MCP** — adapter/prototype candidate; authoritative current upstream and release not pinned.
- **MCP World Model** — thermal/digital-twin and security-assessment candidate; exact authoritative upstream not resolved.

### Digital twins and manufacturing
- **MABDT Engine** — open research artifact for manufacturing digital twins using hierarchical statecharts, an MQTT event bridge, read-only state records, dashboards and LLM-assisted queries.
- **WorldSim AI** — exact canonical repository, license and release not established; supplied MIT, LSTM, anomaly, optimization and RL feature claims remain unresolved.

## 2. Portable simulation evidence contracts

schemas/simulation/simulation-contracts.v1.schema.json defines eight record families: simulation contract; provenance label; trace event; structured agent decision; signed replay receipt; uncertainty decision receipt; critic verdict; and external world-model validation.

The contract can bind model/environment/solver/geometry/parameters/boundary/inputs/outputs by digest; classify evidence as synthetic, simulated, observed, measured, derived, mixed or unknown; chain trace events; bind agent decisions to action events; sign replay metadata; record uncertainty constraints; and require independent, held-out observed/measured evidence before declaring validation within scope.

A hash, signature, MCP interface, critic verdict or successful replay proves only its declared property. A fully executable synthetic environment can still be an inaccurate representation of the world. FEM convergence verifies numerical behavior, not empirical material-model validity. Social replay does not establish human representativeness.

## 3. Acceptance criteria

Require pinned source/release/license, dependencies and SBOM, tool schemas, environment/container manifest, action/observation and reset semantics, model/solver versions, parameters, seed and determinism class, trace and replay, resource/egress/failure behavior, positive and negative tests, numerical convergence where applicable, sensitivity/uncertainty, independent empirical validation with non-leaking holdout, limitations and domain of validity. Any physical side effect requires separate authority and capability controls.

## 4. Public boundary

Only generic schemas, local validators, synthetic fixtures and public candidate references belong here. No C2O private policies, world models, geometry, measured datasets, model internals, authority state, permits, signing keys, identities, telemetry, incident data or private traces are included.

## 5. Non-claims

No third-party package was installed, no candidate simulator invoked and no live MCP server connected. No physical, industrial, social-policy, safety-critical or engineering-design simulation was performed. The portable schema is a proposal, not an industry standard or certification.
