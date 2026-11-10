
"""Orchestrate one Engineering Doctor run."""

from __future__ import annotations

import platform
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .allowlist import ScopeError, validate_requested_repos
from .analysis import readme_drift_findings, status_claim_findings
from .config import RuntimeConfig
from .findings import Finding, severity_counts
from .github_client import GitHubClient, discover_token
from .inventory import RepoInventory, findings_from_inventory, inventory_repo
from .records import allocate_run_dir, build_record, write_record
from .report import format_chicago, render_brief
from .suites import (
    SuiteResult,
    findings_from_suites,
    run_registered_suites,
    skipped_suite_placeholders,
)


def default_output_dir() -> Path:
    return Path(tempfile.gettempdir()) / "engineering-doctor-runs"


def default_limitations(
    *,
    skip_suites: bool,
    authenticated: bool,
    config: RuntimeConfig,
) -> list[str]:
    adapter_ids = [str(adapter.get("id")) for adapter in config.suite_adapters]
    return [
        f"{config.tool_name} v{config.tool_version} is {config.tool_status} / {config.classification}.",
        config.banner,
        "The default repository allowlist is empty. Inventory covers only operator-configured names.",
        "Excluded names, if configured, are refused rather than inventoried.",
        "Inventory uses GitHub GET requests only. Write, comment, merge, label, and schedule APIs are not used.",
        (
            "GitHub requests used a credentialed token discovered from the environment or gh."
            if authenticated
            else "No GitHub token was discovered; unauthenticated API limits apply and private repositories may be UNKNOWN."
        ),
        "README-versus-tree and status-claim checks scan default-branch content reachable through the read-only API, not every feature branch.",
        "Behind-counts and stacked-PR check inspections are recorded as UNKNOWN when the compare or checks API fails.",
        (
            "Suite adapters were skipped in this invocation (NOT_RUN)."
            if skip_suites
            else (
                "Suite adapters ran as configured"
                + (f" ({', '.join(adapter_ids)})." if adapter_ids else ".")
            )
        ),
        "Public demo adapters, when used, may run only already-public prototype and scaffold unittest suites.",
        "This run awards no programme credit and does not treat a pass as authorization.",
        "No readiness percentage or confidence score is computed.",
        *config.extra_limitations,
    ]


def _renumber(findings: list[Finding]) -> list[Finding]:
    renamed: list[Finding] = []
    for index, item in enumerate(findings, start=1):
        prefix = item.finding_id.split("-", 1)[0]
        renamed.append(
            Finding(
                finding_id=f"{prefix}-{index:03d}",
                severity=item.severity,
                title=item.title,
                basis=item.basis,
                evidence=item.evidence,
                repo=item.repo,
                related=item.related,
            )
        )
    return renamed


@dataclass
class RunRequest:
    output_dir: Path
    repos: list[str] | None = None
    skip_suites: bool = False
    skip_inventory: bool = False
    compare_behind: bool = True
    documents: list[tuple[str, str]] | None = None
    client: GitHubClient | None = None
    cloner: Callable | None = None
    python_executable: str | None = None
    scratch_root: Path | None = None
    config: RuntimeConfig | None = None


def execute(request: RunRequest) -> dict:
    started = datetime.now(timezone.utc)
    config = request.config or RuntimeConfig()
    refused: list[Finding] = []
    try:
        selected = validate_requested_repos(
            request.repos,
            allowlist=config.allowlist,
            excluded=config.excluded,
        )
    except ScopeError as exc:
        selected = []
        refused.append(
            Finding(
                finding_id="SCP-001",
                severity="High",
                title="Requested repository is outside scope",
                basis=(
                    "High because an out-of-scope or excluded name must be "
                    "refused rather than inventoried or treated as a pass."
                ),
                evidence=str(exc),
            )
        )

    client = request.client
    if client is None and not request.skip_inventory and selected:
        client = GitHubClient(token=discover_token())

    inventories: list[RepoInventory] = []
    if not request.skip_inventory and selected and client is not None:
        for name in selected:
            inventories.append(
                inventory_repo(
                    client,
                    name,
                    owner=config.github_owner,
                    compare_behind=request.compare_behind,
                )
            )

    suite_results: list[SuiteResult]
    if request.skip_suites:
        suite_results = skipped_suite_placeholders(config.suite_adapters)
    else:
        scratch = request.scratch_root or Path(tempfile.mkdtemp(prefix="engineering-doctor-scratch-"))
        scratch.mkdir(parents=True, exist_ok=True)
        suite_results = run_registered_suites(
            scratch_root=scratch,
            python_executable=request.python_executable,
            cloner=request.cloner,
            adapters=config.suite_adapters,
            known_skip_markers=config.known_skip_markers,
        )

    findings: list[Finding] = []
    findings.extend(refused)
    findings.extend(findings_from_inventory(inventories))
    findings.extend(findings_from_suites(suite_results))

    documents = list(request.documents or [])
    for repo in inventories:
        if repo.readme_text:
            documents.append((f"{repo.name}/README", repo.readme_text))
        findings.extend(
            readme_drift_findings(
                repo.name,
                repo.readme_text,
                repo.tree_paths,
                readme_status="ok" if repo.error is None or repo.readme_text is not None else repo.error,
            )
        )
    findings.extend(status_claim_findings(documents))
    findings = _renumber(findings)

    authenticated = bool(client and client.authenticated)
    inputs = {
        "allowlist": list(config.allowlist),
        "requested_repos": list(selected) if selected else list(request.repos or []),
        "excluded": list(config.excluded),
        "github_owner": config.github_owner,
        "suite_adapters": [
            {
                "id": adapter["id"],
                "owner": adapter.get("owner") or config.github_owner,
                "repo": adapter["repo"],
                "pinned_sha": adapter["pinned_sha"],
                "workdir": adapter["workdir"],
                "argv_suffix": list(adapter["argv_suffix"]),
            }
            for adapter in config.suite_adapters
        ],
        "skip_suites": request.skip_suites,
        "skip_inventory": request.skip_inventory,
        "compare_behind": request.compare_behind,
        "tool_version": config.tool_version,
        "classification": config.classification,
    }
    if config.extra_inputs:
        inputs["extra"] = config.extra_inputs
    repo_shas = {item.name: item.default_sha for item in inventories}
    for item in suite_results:
        if item.resolved_sha:
            repo_shas[f"{item.repo}@{item.adapter_id}"] = item.resolved_sha

    finished = datetime.now(timezone.utc)
    record = build_record(
        run_id="pending",
        started_at=started,
        finished_at=finished,
        python_version=platform.python_version(),
        inputs=inputs,
        inventory=[item.to_dict() for item in inventories],
        suites=[item.to_dict() for item in suite_results],
        findings=findings,
        limitations=default_limitations(
            skip_suites=request.skip_suites,
            authenticated=authenticated,
            config=config,
        ),
        repo_shas=repo_shas,
        notes=[
            f"{config.tool_name} invoked as {config.tool_status}/{config.classification}.",
            config.banner,
        ],
        config=config,
    )
    run_id, run_dir = allocate_run_dir(request.output_dir, started)
    record["run_id"] = run_id
    brief = render_brief(record, findings, started, finished)
    paths = write_record(run_dir, record, brief)
    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "paths": {key: str(value) for key, value in paths.items()},
        "record": record,
        "findings": findings,
        "brief": brief,
        "started_at": started,
        "finished_at": finished,
        "scope_refused": bool(refused),
    }


def print_summary(result: dict) -> None:
    record = result["record"]
    counts = severity_counts(result["findings"])
    banner = record.get("banner")
    print(banner)
    print(f"Status: {record.get('tool_status')} / {record.get('classification')}")
    print(f"Run ID: {result['run_id']}")
    print(f"Started: {format_chicago(result['started_at'])}")
    print(f"Finished: {format_chicago(result['finished_at'])}")
    print(f"Output: {result['run_dir']}")
    print(
        "Findings: "
        f"Critical {counts['Critical']}, High {counts['High']}, "
        f"Medium {counts['Medium']}, Low {counts['Low']}"
    )
    print(f"Brief: {record and result['paths'].get('brief')}")
    print(banner)
