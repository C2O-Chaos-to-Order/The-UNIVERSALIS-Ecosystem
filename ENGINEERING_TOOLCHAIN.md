# Engineering Toolchain and Initial Build Plan

**Repository:** `C2O-Chaos-to-Order/The-UNIVERSALIS-Ecosystem`  
**Responsibility:** UNIVERSALIS Ecosystem / open MotherThread runtime  
**Status:** Initial executable foundation in this branch; specialized candidates remain proposed pending verification.  
**Boundary:** Open UNIVERSALIS / independently operable. Never include C2O-private credentials, policies, authority state, private research records, or operational data.

## Universal engineering foundation

- Least-privilege GitHub Actions CI, automated tests, and JSON contract/config validation.
- CodeQL/static analysis, secret scanning, dependency review, Dependabot, actionlint, and SBOM generation after settings and alert ownership are confirmed.
- CycloneDX/SPDX, OSV-Scanner, Trivy/Grype, Gitleaks, SLSA provenance, in-toto attestations, cosign signing, immutable releases, and reproducible-build comparison as staged controls.
- Pin toolchain versions and action references; retain specifications, fixtures, execution logs, provenance, and explicit limitations.

**Foundation candidates:** Secure SDLC Evidence Collector; repo-assurance; Chainguard Actions; cnspec SBOM Cataloger; CodeQL; actionlint; OSV-Scanner; Trivy/Grype; Gitleaks; SLSA/in-toto; cosign. Not yet verified as installed.

## Domain-specific candidate tools

Open immersive candidates: XARP for XR-agent callable tools/MCP; Meta Immersive Web SDK (IWSDK) for open Three.js/ECS WebXR; NWO MR for agent/robotic embodiment; Agent Hands and incarna for WebXR interaction/avatars. Spatial knowledge candidates: @unrdf/spatial-kg, Constellation, VisionFlow, LogseqXR. OpenEye is a procedural vision-verification candidate requiring strict camera consent, data minimization, human confirmation, and safety limits. Shared bridge candidates: kaptyorka, NeuralBridge, OllaBridge, AIBridge, linco-bridge, Crow. Expose only versioned public contracts; no C2O private policies, credentials, or authority tokens.

Verify canonical source, license, maintainer, release activity, security, compatibility, data flow, and evidence claims before adoption. XR camera, microphone, gaze, hand-tracking, and spatial data require explicit consent and minimization. Agent-to-agent delegation requires explicit boundary authorization.

## Initial executable implementation

- `.github/workflows/repository-quality.yml` runs on pushes and pull requests with read-only repository permissions.
- `.github/scripts/repository_quality_baseline.py` provides a dependency-free self-test and validates JSON in schema/manifest/contract/capability/skill directories plus `package.json` and `tsconfig.json`.
- This first gate does not yet implement XR scenes, spatial interaction, persistent research, bridge authorization, or device conformance.

## Next increments

1. Audit current runtime, API, device, data-flow, and repository boundaries.
2. Add portable manifests/contracts and device-independent fixtures.
3. Add browser/screen-reader and supported-device tests; provide non-immersive fallbacks.
4. Implement versioned MCP/A2A public interface contracts with authentication, scopes, expiry, revocation, and audit events at the boundary.
5. Record conformance, accessibility, privacy, performance, and safety limitations.

## Evidence status

| Item | Status |
|---|---|
| Tool candidates recorded | Documented |
| Baseline validator and CI authored | Implemented in this branch |
| GitHub Actions execution | Pending |
| Domain candidate verification | Pending |
| Specialized integration | Not yet implemented |

## OS provisioning and Golden Compass architecture

See `OS_PROVISIONING_ARCHITECTURE.md` for the open, independently operable virtualization stack, runtime-selection rules, and guest conformance sequence. See `UNIVERSALIN_GUARDIAN_GOLDEN_COMPASS.md` for the non-personal grid, Guardian layers, and decentralized provenance/verification protocol. Tool names are owner-supplied candidates pending source, license, security, and compatibility review.

## Powers energy architecture register — 2026-11-12

Powers treat energy efficiency as a measurable, enforceable, auditable capacity—not only a permission or evaluation. In the current UNIVERSALIS repository set, the canonical implementation is maintained in the Intelligence Powers repository.

- **Canonical open architecture:** [UNIVERSALIS Powers energy architecture](https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Intelligence-Powers/blob/implementation/repository-foundation-2026-11-12/POWERS_ENERGY_ARCHITECTURE.md).
- **Shared v1 contract:** [Powers energy schema](https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Intelligence-Powers/blob/implementation/repository-foundation-2026-11-12/schemas/powers/powers-energy-contracts.v1.schema.json).
- **Executed checks and limitations:** [Powers validation record](https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Intelligence-Powers/blob/implementation/repository-foundation-2026-11-12/POWERS_ENERGY_VALIDATION.md).

The open implementation is local-first and independently operable. Measurement, forecasting, receipts, and synergy calculation do not require a central database or truth authority. It keeps actual workload telemetry and local policy in the operator's chosen environment. The shared contract excludes private credentials and policy values. PDU/RAPL/Kepler/GPU layers require overlap reconciliation; synergy comparisons require matched workload cohorts and SLO profiles. External tools and their advertised savings remain candidates until independently verified.
