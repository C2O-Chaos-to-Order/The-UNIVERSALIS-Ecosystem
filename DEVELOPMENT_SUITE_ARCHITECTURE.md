# Full-Spectrum Development Suite — UNIVERSALIS Open Architecture

**Date:** 2026-11-12  
**Owner:** UNIVERSALIS / open MotherThread ecosystem  
**Status:** Open architecture and portable contract foundation; candidates remain proposed, not adopted.

## 1. Purpose and public boundary

UNIVERSALIS provides inspectable, independently operable instruments for game development; music/audio; 3D/CAD; video; VR/AR; IDEs and version control; build and CI/CD; project management; and documentation.

The public implementation must operate without a C2O account, private policy service, credentials, authority tokens, signing keys, permit records, private project/media data, or C2O operational telemetry. C2O may privately deploy approved instances under separate governance, but private deployments and decisions are not public UNIVERSALIS services.

The seam is three versioned data contracts: project-format definitions, agent-capability manifests, and signed build-provenance receipts. MCP defines callable tools and interaction transport. It does not make native project files portable, establish semantic compatibility, or prove an artifact's origin. A manifest describes a capability and does not grant access. A signature verifies a signed statement under a trust policy, not artifact quality or safety.

Open-source status does not automatically imply offline operation, private hosting, air-gapped use, sovereign control, or commercial rights for bundled models/assets.

## 2. Candidate inventory

All named tools are candidates pending exact upstream, release, license, dependency, security, compatibility, local/hosted data-flow, and behavior verification.

### 2.1 Game development

NodeTool; Summer Engine; Blazium Engine; o3de-mcp; GladeKit MCP; Limina; Omniweft; OpenEngine; MORX GMS2 MCP; unikit-ai; GameForge MCP.

Current source corrections: o3de-mcp's README describes 96 tools across seven categories rather than 67/five. GladeKit's README describes 275 Unity tools and 115 Godot tools rather than 235/53. Summer Engine separates local engine tooling from hosted cloud MCP for services such as assets/analytics/publishing. Limina describes typed permissioned skills and a replayable hash-chained JSONL world log. Omniweft, OpenEngine, MORX GMS2 MCP, unikit-ai, and GameForge MCP need exact source pinning.

### 2.2 Music and audio

ReaperMCP; FL Studio MCP Server; ATRI_AGENT; Audio Plugin Coder; ConjureDSP; SongForge-MCP; songgeneration-mcp; Soundbox; ai-music-mcp; yovoice.

Current source corrections: FL Studio MCP's README describes 164 tools rather than 29. Soundbox's tool-count statements conflict (21 versus 24). Audio Plugin Coder documents JUCE 9 and does not imply all CLAP targets are enabled. SongForge-MCP wraps a local ACE-Step model, but model and generated-output rights are distinct from the wrapper license. ReaperMCP, ATRI_AGENT, ConjureDSP, songgeneration-mcp, and ai-music-mcp require exact upstream and current release confirmation.

### 2.3 3D graphics, modeling, and CAD

Blender MCP Bridge; VibeInc AI Art Team; Vibe CAD; ai-cad; cadx; Presidium Shape Studio; 3D Gen Studio; Limina.

The Blender MCP Bridge listing conflicts across sources (93/98/106 tools); no single count is adopted. Exact source and licensing for the remaining AI CAD/3D tools require pinning. Preserve parametric constraints, units, coordinate frames, tolerances, materials, source sketches and export settings in the project package.

### 2.4 Video

Kinocut; Framewright; OpenEdit.

Kinocut describes FFmpeg MCP operations, preflight validation and Video Receipts; a receipt is not inherently a digital signature or human publication approval. OpenEdit's pipeline is Apache-2.0 while its VEED HTML renderer is a separately licensed closed-source component; optional hosted transcription may upload audio. Framewright's current upstream, license and export fidelity remain unresolved.

### 2.5 VR and AR

Immersive Web SDK (IWSDK); XR Blocks; Three-Live; HERA; scenekit-xr.

IWSDK is an MIT Three.js/ECS WebXR framework. XR Blocks' repository states it is not an officially supported Google product; Gemini-backed authoring can send context to Google services. Three-Live has an open repository and MCP CLI, but Google's open-source blog likewise states it is not an officially supported Google product. HERA and scenekit-xr need exact upstream and conformance pinning.

XR camera, gaze, head/hand pose, room meshes, microphone and spatial mapping data require explicit consent, purpose limitation, minimization, short retention, and non-immersive fallback. Do not treat spatial telemetry as ordinary application logs.

### 2.6 IDEs, version control, and core engineering

Eclipse Theia; Qt Creator 20; ThinkRail; Cline; joLink Runtime; Libra; AVCS; GitAgent; LogNexus MCP; TeamAI; RepoKeeper.

ThinkRail documents confirmation for non-read-only MCP calls; that does not eliminate repository-level trust/configuration risk. joLink Runtime surfaced as prerelease. TeamAI provides Git-managed skills, agents, rules and MCP configuration. RepoKeeper's hosted/paid feature boundaries must be separated from local functionality. Exact source and version for Libra, AVCS, GitAgent and LogNexus MCP remain unresolved.

### 2.7 Build and CI/CD

eforge; RepoLaunch; Genesis; agent-project-builder; Eclipse Atesor; shipmill; Hive; CiLydian; CIDRA; KiCI.

RepoLaunch's 78% success number is from a specified research benchmark and is not a universal build guarantee. Eclipse Atesor is in incubation; current documented RISC-V builds use QEMU/binfmt emulation, with native hardware described as future/in progress. KiCI retains a hosted webhook relay/dashboard while executing jobs on operator-controlled infrastructure; classify it as hybrid, not air-gapped. Exact source/release for Genesis, agent-project-builder, shipmill, Hive, CiLydian and CIDRA remain unresolved.

### 2.8 Project management and documentation

Agentic Project Management (APM); open-workmcp; Paca; OpenMac; CodiLay; Fidus; CodeWiki 2.0; OpenWiki; docsector-reader; devdocs-forge-agent.

APM is an ambiguous acronym; use the official documentation/package identity and do not merge unrelated projects by name. CodiLay and Fidus have public locators but package ownership, filesystem scope, and data flow still need review. Exact source/release for open-workmcp, Paca, OpenMac, CodeWiki 2.0, OpenWiki, docsector-reader, and devdocs-forge-agent remain unresolved.

## 3. Portable contract design

Shared files:
- schemas/development-suite/development-suite-contracts.v1.schema.json
- examples/development-suite/development-suite-fixtures.v1.json
- .github/scripts/development_suite_contract.py
- .github/workflows/development-suite-contract.yml

Three record families:
1. Project-format contract: domain, format/version, canonical upstream specification/schema references, serialization and canonicalization, project and asset digests, portability and declared runtime dependencies.
2. Agent-capability manifest: protocol/transport, deployment and data-residency classification, auth modes, operation effect, declared scope, approval mode and limitations.
3. Build-provenance receipt: in-toto Statement v1 with SLSA provenance v1 predicate, DSSE signature envelope and verifier metadata.

The contract is an envelope around native formats, not a replacement for them. Examples include replayable game logs or native engine projects; DAW session files plus MIDI/audio interchange; glTF/USD for 3D; OpenTimelineIO/FCPXML for editorial timelines; WebXR/OpenXR runtime profiles; Git object and commit identity for software; and versioned task/project/documentation manifests.

## 4. Evidence and validation

The synthetic fixture includes nine domain examples, three capability manifests (including local and hybrid classifications), and one DSSE/Ed25519 provenance receipt. The validator checks JSON Schema, capability scope/approval semantics, DSSE payload equality to canonical statement bytes, signature verification with a disposable fixture key, and chronology. Negative tests cover missing versions/scopes, unapproved high-impact capabilities, unsigned/tampered signatures, statement mismatch, missing builder identity and missing artifact digest.

The fixture public key is not a production trust root. The private test key is not stored. The workflow validates only contract fixtures and validator behavior; it does not build a real artifact or certify a third-party product.

## 5. Portability and safety requirements

- Preserve native files and editor-specific state; define lossless conversion requirements and declare unknown extensions/dependencies.
- Content-address assets and bind project revision, toolchain, models, plugins, inputs, outputs and sidecar test evidence.
- Preserve timebase, coordinate frame, units, color/audio profile, frame rate, sample rate, plugin versions, runtime feature profiles and codec dependencies where relevant.
- Distinguish local bridges from hosted model endpoints, hosted account systems, telemetry and hybrid orchestration services.
- Never publish private C2O secrets, policies, project content, signer identities, permits, or authority data.
- A successful test, CI run, discovered tool, or valid signature is not permission to release or deploy.

## 6. Adoption gates and limitations

Before adoption, pin source/release and license; inspect dependency/build scripts and plugin permissions; generate an SBOM; review filesystem and network access; identify hosted dependencies and telemetry; test isolation and rollback; verify model/asset rights; reproduce output; and record independent evidence. No candidate is installed, integrated, benchmarked, or certified by inclusion in this inventory.
