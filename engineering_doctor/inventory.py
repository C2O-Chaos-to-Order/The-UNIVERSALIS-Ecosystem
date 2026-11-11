
"""Read-only repository and pull-request inventory."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from .constants import DEFAULT_GITHUB_OWNER
from .findings import Finding
from .github_client import GitHubClient, GitHubError


@dataclass
class PullRequestRecord:
    number: int
    title: str
    is_draft: bool
    state: str
    html_url: str
    head_ref: str
    head_sha: str
    base_ref: str
    created_at: str | None
    updated_at: str | None
    age_days: float | None
    behind_by: int | None
    ahead_by: int | None
    compare_status: str
    check_run_count: int | None
    combined_status: str | None
    stacked: bool
    checks_unknown: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RepoInventory:
    name: str
    owner: str
    full_name: str
    query_status: str
    empty: bool | None
    default_branch: str | None
    default_sha: str | None
    visibility: str | None
    html_url: str | None
    open_pr_count: int | None
    draft_pr_count: int | None
    error: str | None = None
    pull_requests: list[PullRequestRecord] = field(default_factory=list)
    readme_text: str | None = None
    tree_paths: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _age_days(created_at: str | None, now: datetime) -> float | None:
    parsed = _parse_iso(created_at)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return round((now - parsed).total_seconds() / 86400.0, 3)


def inventory_repo(
    client: GitHubClient,
    name: str,
    owner: str = DEFAULT_GITHUB_OWNER,
    now: datetime | None = None,
    include_readme_tree: bool = True,
    compare_behind: bool = True,
    inspect_checks_for_stacked: bool = True,
) -> RepoInventory:
    """Inventory one configured repository. Errors become UNKNOWN, never pass."""

    clock = now or datetime.now(timezone.utc)
    full_name = f"{owner}/{name}"
    base = RepoInventory(
        name=name,
        owner=owner,
        full_name=full_name,
        query_status="UNKNOWN",
        empty=None,
        default_branch=None,
        default_sha=None,
        visibility=None,
        html_url=None,
        open_pr_count=None,
        draft_pr_count=None,
    )
    try:
        repo, _ = client.get(f"/repos/{owner}/{name}")
    except GitHubError as exc:
        base.error = str(exc)
        base.query_status = "UNKNOWN"
        return base

    if not isinstance(repo, dict):
        base.error = "repository payload was not an object"
        return base

    base.visibility = repo.get("visibility") or ("private" if repo.get("private") else "public")
    base.html_url = repo.get("html_url")
    base.default_branch = repo.get("default_branch")
    # GitHub REST does not expose isEmpty; an empty repo has no default branch SHA.
    try:
        if base.default_branch:
            ref, _ = client.get(f"/repos/{owner}/{name}/git/ref/heads/{base.default_branch}")
            if isinstance(ref, dict):
                obj = ref.get("object") or {}
                base.default_sha = obj.get("sha")
            base.empty = False
        else:
            base.empty = True
    except GitHubError as exc:
        if exc.status in {404, 409}:
            base.empty = True
            base.default_sha = None
        else:
            base.error = str(exc)
            base.query_status = "UNKNOWN"
            return base

    try:
        pulls = client.get_paginated(
            f"/repos/{owner}/{name}/pulls",
            {"state": "open", "per_page": 100},
        )
    except GitHubError as exc:
        base.error = str(exc)
        base.query_status = "UNKNOWN"
        return base

    records: list[PullRequestRecord] = []
    drafts = 0
    for item in pulls:
        if not isinstance(item, dict):
            continue
        head = item.get("head") or {}
        base_branch = item.get("base") or {}
        is_draft = bool(item.get("draft"))
        if is_draft:
            drafts += 1
        base_ref = base_branch.get("ref") or ""
        head_ref = head.get("ref") or ""
        head_sha = head.get("sha") or ""
        stacked = bool(base.default_branch and base_ref and base_ref != base.default_branch)
        behind_by = None
        ahead_by = None
        compare_status = "not_requested"
        if compare_behind and base_ref and head_sha:
            try:
                encoded_base = quote(base_ref, safe="")
                encoded_head = quote(head_sha, safe="")
                compare, _ = client.get(
                    f"/repos/{owner}/{name}/compare/{encoded_base}...{encoded_head}"
                )
                if isinstance(compare, dict):
                    behind_by = compare.get("behind_by")
                    ahead_by = compare.get("ahead_by")
                    compare_status = "ok"
                else:
                    compare_status = "UNKNOWN"
            except GitHubError:
                compare_status = "UNKNOWN"
        check_run_count = None
        combined_status = None
        checks_unknown = False
        if inspect_checks_for_stacked and stacked and head_sha:
            try:
                checks, _ = client.get(
                    f"/repos/{owner}/{name}/commits/{head_sha}/check-runs",
                    {"per_page": 100},
                )
                if isinstance(checks, dict) and isinstance(checks.get("check_runs"), list):
                    check_run_count = len(checks["check_runs"])
                else:
                    checks_unknown = True
            except GitHubError:
                checks_unknown = True
            try:
                status_payload, _ = client.get(
                    f"/repos/{owner}/{name}/commits/{head_sha}/status"
                )
                if isinstance(status_payload, dict):
                    combined_status = status_payload.get("state")
            except GitHubError:
                checks_unknown = True
        records.append(
            PullRequestRecord(
                number=int(item.get("number") or 0),
                title=str(item.get("title") or ""),
                is_draft=is_draft,
                state=str(item.get("state") or "open"),
                html_url=str(item.get("html_url") or ""),
                head_ref=head_ref,
                head_sha=head_sha,
                base_ref=base_ref,
                created_at=item.get("created_at"),
                updated_at=item.get("updated_at"),
                age_days=_age_days(item.get("created_at"), clock),
                behind_by=behind_by,
                ahead_by=ahead_by,
                compare_status=compare_status,
                check_run_count=check_run_count,
                combined_status=combined_status,
                stacked=stacked,
                checks_unknown=checks_unknown,
            )
        )

    base.pull_requests = records
    base.open_pr_count = len(records)
    base.draft_pr_count = drafts

    if include_readme_tree and base.empty is False:
        try:
            readme, _ = client.get(f"/repos/{owner}/{name}/readme")
            if isinstance(readme, dict) and readme.get("encoding") == "base64":
                import base64

                raw = readme.get("content") or ""
                compact = "".join(str(raw).split())
                base.readme_text = base64.b64decode(compact).decode("utf-8", errors="replace")
            elif isinstance(readme, dict) and isinstance(readme.get("content"), str):
                base.readme_text = readme["content"]
        except GitHubError as exc:
            if exc.status != 404:
                base.error = (base.error + "; " if base.error else "") + f"readme: {exc}"
        if base.default_sha:
            try:
                tree, _ = client.get(
                    f"/repos/{owner}/{name}/git/trees/{base.default_sha}",
                    {"recursive": "1"},
                )
                if isinstance(tree, dict) and isinstance(tree.get("tree"), list):
                    paths = []
                    for entry in tree["tree"]:
                        if isinstance(entry, dict) and entry.get("path"):
                            paths.append(str(entry["path"]))
                    base.tree_paths = paths
                    if tree.get("truncated"):
                        base.error = (
                            (base.error + "; " if base.error else "")
                            + "git tree listing was truncated; extra paths are UNKNOWN"
                        )
                else:
                    base.error = (
                        (base.error + "; " if base.error else "")
                        + "git tree payload was not an object"
                    )
            except GitHubError as exc:
                base.error = (base.error + "; " if base.error else "") + f"tree: {exc}"

    if base.error and (base.open_pr_count is None or (include_readme_tree and base.tree_paths is None and base.empty is False)):
        base.query_status = "UNKNOWN"
    else:
        base.query_status = "ok" if not base.error else "PARTIAL"
    return base


def findings_from_inventory(repos: list[RepoInventory]) -> list[Finding]:
    findings: list[Finding] = []
    seq = 0
    for repo in repos:
        if repo.query_status == "UNKNOWN":
            seq += 1
            findings.append(
                Finding(
                    finding_id=f"INV-{seq:03d}",
                    severity="High",
                    title=f"{repo.name} inventory is UNKNOWN",
                    basis=(
                        "High because a missing repository, API error, or unreadable "
                        "response is fail-closed: it must never be treated as an empty "
                        "or passing inventory."
                    ),
                    evidence=repo.error or "no further detail",
                    repo=repo.name,
                )
            )
            continue
        if repo.query_status == "PARTIAL":
            seq += 1
            findings.append(
                Finding(
                    finding_id=f"INV-{seq:03d}",
                    severity="Medium",
                    title=f"{repo.name} inventory is partial",
                    basis=(
                        "Medium because some fields were collected but at least one "
                        "requested resource failed; the gap is visible and not filled in."
                    ),
                    evidence=repo.error or "partial error without detail",
                    repo=repo.name,
                )
            )
        if repo.empty:
            seq += 1
            findings.append(
                Finding(
                    finding_id=f"INV-{seq:03d}",
                    severity="Low",
                    title=f"{repo.name} is empty",
                    basis=(
                        "Low because an empty placeholder is an inventory fact, not a "
                        "runtime failure. It is recorded so the allowlist stays complete."
                    ),
                    evidence="default-branch SHA was absent (GitHub empty-repository response)",
                    repo=repo.name,
                )
            )
        for pr in repo.pull_requests:
            if not pr.stacked:
                continue
            no_checks = (pr.check_run_count == 0) and (pr.combined_status in {None, "pending"})
            if pr.checks_unknown:
                seq += 1
                findings.append(
                    Finding(
                        finding_id=f"STK-{seq:03d}",
                        severity="Medium",
                        title=f"{repo.name}#{pr.number} is stacked and check status is UNKNOWN",
                        basis=(
                            "Medium because a stacked pull request (base is not the "
                            "default branch) could not have its checks read; that is "
                            "not treated as a pass."
                        ),
                        evidence=(
                            f"base={pr.base_ref!r} default={repo.default_branch!r} "
                            f"head={pr.head_sha[:12] if pr.head_sha else 'unknown'}"
                        ),
                        repo=repo.name,
                        related=f"#{pr.number}",
                    )
                )
                continue
            if no_checks or pr.check_run_count == 0:
                seq += 1
                findings.append(
                    Finding(
                        finding_id=f"STK-{seq:03d}",
                        severity="High",
                        title=f"{repo.name}#{pr.number} is stacked and reports no checks",
                        basis=(
                            "High because workflows that trigger only on pull requests "
                            "to the default branch do not run for a stacked PR, so the "
                            "absence of checks must not be read as a pass."
                        ),
                        evidence=(
                            f"base={pr.base_ref!r} default={repo.default_branch!r} "
                            f"title={pr.title!r} check_runs={pr.check_run_count} "
                            f"combined_status={pr.combined_status!r}"
                        ),
                        repo=repo.name,
                        related=f"#{pr.number}",
                    )
                )
    return findings
