
"""README-versus-tree drift and status-claim mismatch checks."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

from .findings import Finding

_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_BACKTICK = re.compile(r"`([^`]+)`")
_ARTIFACT_ID = re.compile(r"\b([A-Z]{2,6}-\d{3})\b")
_STATUS_FIELD = re.compile(
    r"^\*\*(?:Authority )?Status:\*\*\s*(.+?)\s*$",
    re.MULTILINE | re.IGNORECASE,
)
_INLINE_STATUS = re.compile(
    r"\b([A-Z]{2,6}-\d{3})\b[^\n]{0,80}?\bStatus:\s*([^\n<]+)",
    re.IGNORECASE,
)
_NOT_STARTED = re.compile(
    r"product implementation not yet started",
    re.IGNORECASE,
)
_OWNER_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_PATHISH_SUFFIXES = (
    ".md",
    ".py",
    ".txt",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".cfg",
    ".ini",
    ".csv",
)


def _looks_like_path(value: str) -> bool:
    text = value.strip().strip("\"'")
    if not text or text.startswith(("http://", "https://", "mailto:", "#")):
        return False
    if " " in text and "/" not in text:
        return False
    if any(ch in text for ch in "*?<>|"):
        return False
    if _OWNER_REPO.match(text) and not text.lower().endswith(_PATHISH_SUFFIXES):
        return False
    has_slash = "/" in text
    has_suffix = text.lower().endswith(_PATHISH_SUFFIXES)
    if not (has_slash or has_suffix):
        return False
    if text.startswith("/"):
        return False
    return True


def extract_mentioned_paths(markdown: str) -> list[str]:
    """Return conservative relative path mentions from Markdown."""

    found: list[str] = []
    seen: set[str] = set()
    candidates: list[str] = []
    for match in _LINK.finditer(markdown):
        raw = match.group(1).strip()
        if raw.startswith("<") and ">" in raw:
            raw = raw[1 : raw.index(">")]
        raw = raw.split()[0] if raw else raw
        candidates.append(raw)
    for match in _BACKTICK.finditer(markdown):
        candidates.append(match.group(1).strip())
    for item in candidates:
        if not _looks_like_path(item):
            continue
        path = unquote(item.split("#", 1)[0].split("?", 1)[0])
        path = path.lstrip("./")
        if not path or path in seen:
            continue
        seen.add(path)
        found.append(path)
    return found


def path_exists_in_tree(path: str, tree_paths: list[str]) -> bool:
    normalized = path.rstrip("/")
    tree = set(tree_paths)
    if normalized in tree:
        return True
    prefix = normalized + "/"
    return any(item == normalized or item.startswith(prefix) for item in tree_paths)


def readme_drift_findings(
    repo: str,
    readme_text: str | None,
    tree_paths: list[str] | None,
    readme_status: str = "ok",
) -> list[Finding]:
    findings: list[Finding] = []
    if readme_text is None and readme_status != "ok":
        findings.append(
            Finding(
                finding_id="DOC-000",
                title=f"{repo} README could not be read",
                severity="Medium",
                basis=(
                    "Medium because an unreadable README is not treated as "
                    "agreement with the tree."
                ),
                evidence=readme_status,
                repo=repo,
            )
        )
        return findings
    if not readme_text or tree_paths is None:
        return findings
    missing = []
    for path in extract_mentioned_paths(readme_text):
        if not path_exists_in_tree(path, tree_paths):
            missing.append(path)
    for index, path in enumerate(missing, start=1):
        findings.append(
            Finding(
                finding_id=f"DOC-{index:03d}",
                severity="Medium",
                title=f"{repo} README names a path that is not in the default-branch tree",
                basis=(
                    "Medium because a named path that does not exist is a "
                    "documentation-to-tree drift, not a runtime crash."
                ),
                evidence=f"named path {path!r} was not present in the default-branch tree",
                repo=repo,
            )
        )
    if _NOT_STARTED.search(readme_text):
        implementation_dirs = [
            name
            for name in ("prototype", "scaffold", "implementation", "src")
            if path_exists_in_tree(name, tree_paths)
        ]
        if implementation_dirs:
            findings.append(
                Finding(
                    finding_id="DOC-STATUS-001",
                    severity="High",
                    title=f"{repo} README says product implementation is not yet started",
                    basis=(
                        "High because a status sentence that implementation has not "
                        "started conflicts with tracked implementation directories. "
                        "Readers can take the README as current state."
                    ),
                    evidence=(
                        "README matches 'product implementation not yet started' "
                        f"while the tree contains: {', '.join(implementation_dirs)}"
                    ),
                    repo=repo,
                )
            )
    return findings


def _normalize_status(value: str) -> str:
    text = value.strip().strip(".,;")
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def _status_kind(value: str) -> str:
    normalized = _normalize_status(value)
    if "not ratified" in normalized or "unratified" in normalized:
        return "not_ratified"
    if "ratif" in normalized:
        return "ratified"
    if "draft" in normalized or "proposed" in normalized or "not adopted" in normalized:
        return "draft"
    return "other"


def collect_declared_statuses(text: str, default_id: str | None = None) -> dict[str, set[str]]:
    """Map artifact IDs to status strings declared in a document."""

    declared: dict[str, set[str]] = {}
    heading_ids = _ARTIFACT_ID.findall(text.split("\n", 1)[0]) if text else []
    file_ids = list(heading_ids)
    if default_id:
        file_ids.append(default_id)
    field_matches = _STATUS_FIELD.findall(text)
    for artifact_id in file_ids:
        for raw in field_matches:
            declared.setdefault(artifact_id, set()).add(raw.strip())
    for artifact_id, raw in _INLINE_STATUS.findall(text):
        declared.setdefault(artifact_id, set()).add(raw.strip())
    return declared


def status_claim_findings(documents: list[tuple[str, str]]) -> list[Finding]:
    """Compare declared statuses for the same artifact ID across documents.

    ``documents`` is a list of (label, markdown_text) pairs. A header that
    says Draft (or Not Ratified) while another document calls the same ID
    Ratified is reported as a mismatch.
    """

    by_id: dict[str, list[tuple[str, str]]] = {}
    for label, text in documents:
        default_id = None
        name = Path(label).name
        name_match = _ARTIFACT_ID.search(name)
        if name_match:
            default_id = name_match.group(1)
        declared = collect_declared_statuses(text, default_id=default_id)
        for artifact_id, statuses in declared.items():
            for status in statuses:
                by_id.setdefault(artifact_id, []).append((label, status))

    findings: list[Finding] = []
    seq = 0
    for artifact_id, declarations in sorted(by_id.items()):
        kinds = {(_status_kind(status), label, status) for label, status in declarations}
        kind_names = {item[0] for item in kinds if item[0] != "other"}
        conflicting = "ratified" in kind_names and (
            "draft" in kind_names or "not_ratified" in kind_names
        )
        if not conflicting:
            continue
        seq += 1
        evidence_parts = [
            f"{label}: {status}" for _, label, status in sorted(kinds, key=lambda item: item[1])
        ]
        findings.append(
            Finding(
                finding_id=f"CLM-{seq:03d}",
                severity="High",
                title=f"{artifact_id} has conflicting status language",
                basis=(
                    "High because an artifact header that presents a draft or "
                    "unratified status while another document calls it Ratified "
                    "can be mistaken for authorization. A validator-style label "
                    "is not ratification."
                ),
                evidence="; ".join(evidence_parts),
                related=artifact_id,
            )
        )
    return findings


def findings_from_documents(documents: list[tuple[str, str]]) -> list[Finding]:
    return status_claim_findings(documents)
