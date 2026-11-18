# UNIVERSALIS Construction Engine v0.1.0

A small, dependency-free construction engine for producing repository-owned tools from declarative JSON specifications.

## Boundary
- This engine is the reusable construction core in the public UNIVERSALIS ecosystem.
- It creates files only from explicit text templates in a reviewed JSON specification.
- It does not execute generated code, install dependencies, access credentials, publish releases, or grant authority.
- Private C2O policy and approval remain in the C2O ecosystem. See the C2O construction governance adapter/contract.

## Quick start
From the repository root:

```sh
python -m construction_engine build construction_engine/examples/hello-tool.json --output /tmp/universalis-build
python -m construction_engine verify /tmp/universalis-build
```

Python 3.10+; standard library only.

## Lifecycle
1. Parse and validate the specification.
2. Produce a deterministic build plan.
3. Render declared files into an output directory.
4. Verify required paths and SHA-256 manifest.
5. Emit a machine-readable build record.

A successful build is not authorization to merge, publish, deploy, or execute the generated tool. Promotion requires ecosystem-owner review and the applicable C2O governance controls.

## Status
v0.1.0 is an initial construction core. It is not a general-purpose compiler, sandbox, CI deployment system, or autonomous agent.
