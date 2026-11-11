"""Configurable repository allowlist and exclusion checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence


class ScopeError(ValueError):
    """A requested repository is outside the configured scope."""


def is_excluded(name: str, excluded: Sequence[str]) -> bool:
    return name.strip() in set(excluded)


def is_allowlisted(name: str, allowlist: Sequence[str]) -> bool:
    return name in set(allowlist)


def load_name_file(path: Path) -> list[str]:
    """Load repository names from a JSON list or a newline-separated text file."""

    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    raw_names: list[str]
    if stripped.startswith("[") or stripped.startswith("{"):
        payload = json.loads(text)
        if isinstance(payload, dict):
            payload = payload.get("repos", payload.get("allowlist"))
        if not isinstance(payload, list):
            raise ScopeError(
                "allowlist file JSON must be a list of names or an object "
                "with a repos or allowlist list"
            )
        raw_names = [str(item) for item in payload]
    else:
        raw_names = []
        for line in text.splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                raw_names.append(line)
    names: list[str] = []
    seen: set[str] = set()
    for raw in raw_names:
        name = raw.strip()
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


def validate_requested_repos(
    names: list[str] | tuple[str, ...] | None,
    *,
    allowlist: Sequence[str] = (),
    excluded: Sequence[str] = (),
) -> list[str]:
    """Return the repositories to inventory, or raise ScopeError.

    An empty request returns the configured allowlist, which is empty by
    default. If the operator passes explicit names and no allowlist is
    configured, those names are accepted unless they are excluded. If an
    allowlist is configured, every requested name must appear on it.
    """

    excluded_set = frozenset(excluded)
    allow_set = frozenset(allowlist)
    if not names:
        return list(allowlist)
    accepted: list[str] = []
    refused: list[str] = []
    seen: set[str] = set()
    for raw in names:
        name = raw.strip()
        if not name or name in seen:
            continue
        seen.add(name)
        if name in excluded_set:
            refused.append(f"{name} (explicitly excluded; out of scope)")
            continue
        if allow_set and name not in allow_set:
            refused.append(f"{name} (not on the configured allowlist)")
            continue
        accepted.append(name)
    if refused:
        joined = "; ".join(refused)
        raise ScopeError("Refused repository request(s): " + joined + ".")
    return accepted
