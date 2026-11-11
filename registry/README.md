# Tool Registry and Evidence Registry

Status: LIMITED

This directory holds versioned JSON Schemas, a fail-closed stdlib validator,
public tool records, and public evidence records. It is not a completed
product, an authorized release, or a scoreboard.

- Validate from the repository root: `python -m registry.validate`
- First tool: [`tools/tool-001.json`](tools/tool-001.json) (Engineering Doctor,
  LIMITED / PUBLIC_CANDIDATE). The owner field is the placeholder `owner`.
- Evidence recorded here is public and reproducible only: the core unittest
  suite and public GitHub Actions run
  [42900738045](https://github.com/C2O-Chaos-to-Order/The-UNIVERSALIS-Ecosystem/actions/runs/42900738045).
- Additional live-run evidence recorded by the private adapter that consumes
  this public core is not copied here. That adapter keeps its own private
  evidence record for `tool-001`.
- Records do not contain scores or confidence values.
- A pass is not authorization, scientific validation, or independent
  verification.

Requirement references `REQ-RUBY-01` and `REQ-ONYX-01` on `tool-001` are
public-safe statements of existing Engineering Doctor behaviour, with locators
to the tests that demonstrate that behaviour. They cite privately originated
principles only by the short labels Ruby and Onyx. They are not a
tablet-compliance claim, not authorization, and they do not change the
LIMITED status of this registry.
