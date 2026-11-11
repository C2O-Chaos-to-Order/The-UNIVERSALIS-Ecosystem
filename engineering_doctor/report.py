
"""Markdown brief rendering."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from .constants import BANNER, CLASSIFICATION, TOOL_NAME, TOOL_STATUS, TOOL_VERSION
from .findings import Finding, severity_counts

CHICAGO = ZoneInfo("America/Chicago")


def format_chicago(value: datetime) -> str:
    local = value.astimezone(CHICAGO)
    return local.strftime("%Y-%m-%d %I:%M:%S %p CT (America/Chicago)")


def render_brief(
    record: dict,
    findings: list[Finding],
    started_at: datetime,
    finished_at: datetime,
) -> str:
    counts = severity_counts(findings)
    inventory = record.get("inventory") or []
    suites = record.get("suites") or []
    unknown_repos = [
        item.get("name")
        for item in inventory
        if item.get("query_status") == "UNKNOWN"
    ]
    empty_repos = [item.get("name") for item in inventory if item.get("empty") is True]
    open_total = 0
    draft_total = 0
    for item in inventory:
        if isinstance(item.get("open_pr_count"), int):
            open_total += item["open_pr_count"]
        if isinstance(item.get("draft_pr_count"), int):
            draft_total += item["draft_pr_count"]

    tool_name = record.get("tool_name") or TOOL_NAME
    tool_version = record.get("tool_version") or TOOL_VERSION
    tool_status = record.get("tool_status") or TOOL_STATUS
    classification = record.get("classification") or CLASSIFICATION
    banner = record.get("banner") or BANNER
    lines = [
        f"# {tool_name} v{tool_version} brief",
        "",
        f"Status: {tool_status} / {classification}",
        "",
        f"> {banner}",
        "",
        f"- Run ID: `{record.get('run_id')}`",
        f"- Started: {format_chicago(started_at)}",
        f"- Finished: {format_chicago(finished_at)}",
        f"- Python: {record.get('python_version')}",
        f"- Inputs SHA-256: `{record.get('inputs_sha256')}`",
        f"- Findings: Critical {counts['Critical']}, High {counts['High']}, "
        f"Medium {counts['Medium']}, Low {counts['Low']}",
        "",
        "## Inventory",
        "",
        f"Allowlisted repositories queried: {len(inventory)}. "
        f"Empty: {len(empty_repos)}. UNKNOWN: {len(unknown_repos)}.",
        f"Open pull requests counted on successful inventories: {open_total} "
        f"({draft_total} drafts).",
        "",
        "| Repository | Status | Empty | Default SHA | Open PRs | Drafts | Error |",
        "| --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for item in inventory:
        sha = item.get("default_sha") or "—"
        if isinstance(sha, str) and len(sha) > 12:
            sha = sha[:12]
        empty = "yes" if item.get("empty") is True else ("no" if item.get("empty") is False else "UNKNOWN")
        open_prs = item.get("open_pr_count")
        drafts = item.get("draft_pr_count")
        error = (item.get("error") or "—").replace("|", "/")
        lines.append(
            "| {name} | {status} | {empty} | `{sha}` | {open_prs} | {drafts} | {error} |".format(
                name=item.get("name"),
                status=item.get("query_status"),
                empty=empty,
                sha=sha,
                open_prs=open_prs if open_prs is not None else "UNKNOWN",
                drafts=drafts if drafts is not None else "UNKNOWN",
                error=error,
            )
        )

    stacked = []
    for item in inventory:
        for pull in item.get("pull_requests") or []:
            if pull.get("stacked"):
                stacked.append((item.get("name"), pull))
    lines.extend(["", "## Stacked pull requests", ""])
    if not stacked:
        lines.append("No stacked open pull requests (base different from the default branch) were observed.")
    else:
        lines.append("| Repository | PR | Base | Behind | Check runs | Combined status |")
        lines.append("| --- | --- | --- | ---: | ---: | --- |")
        for repo_name, pull in stacked:
            behind = pull.get("behind_by")
            checks = pull.get("check_run_count")
            lines.append(
                "| {repo} | #{num} | {base} | {behind} | {checks} | {combined} |".format(
                    repo=repo_name,
                    num=pull.get("number"),
                    base=pull.get("base_ref"),
                    behind=behind if behind is not None else "UNKNOWN",
                    checks=checks if checks is not None else "UNKNOWN",
                    combined=pull.get("combined_status") or "UNKNOWN",
                )
            )

    lines.extend(["", "## Suite adapters", ""])
    lines.append("| Adapter | Repo | SHA | Status | Discovered | Passed | Failed | Errors | Skipped |")
    lines.append("| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |")
    for item in suites:
        sha = item.get("resolved_sha") or item.get("pinned_sha") or "—"
        if isinstance(sha, str) and len(sha) > 12:
            sha = sha[:12]
        def cell(key: str) -> object:
            value = item.get(key)
            return value if value is not None else "UNKNOWN"
        lines.append(
            "| {adapter} | {repo} | `{sha}` | {status} | {discovered} | {passed} | {failed} | {errors} | {skipped} |".format(
                adapter=item.get("adapter_id"),
                repo=item.get("repo"),
                sha=sha,
                status=item.get("status"),
                discovered=cell("discovered"),
                passed=cell("passed"),
                failed=cell("failed"),
                errors=cell("errors"),
                skipped=cell("skipped"),
            )
        )
    lines.extend(
        [
            "",
            f"> {banner}",
            "",
            "## Findings",
            "",
        ]
    )
    if not findings:
        lines.append("No findings were generated. That is not authorization or verification.")
    else:
        for item in findings:
            repo = f" ({item.repo})" if item.repo else ""
            related = f" / {item.related}" if item.related else ""
            lines.extend(
                [
                    f"### {item.finding_id} — {item.severity}{repo}{related}",
                    "",
                    item.title,
                    "",
                    f"Basis: {item.basis}",
                    "",
                    f"Evidence: {item.evidence}",
                    "",
                ]
            )

    lines.extend(["## Limitations", ""])
    for limitation in record.get("limitations") or []:
        lines.append(f"- {limitation}")
    lines.extend(["", f"> {banner}", ""])
    return "\n".join(lines)
