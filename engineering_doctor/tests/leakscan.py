
"""Hashed-denylist scanner used by the leak test.

Forbidden phrases are stored only as SHA-256 digests of their normalized
forms. This module never needs the plaintext list: it hashes identifiers
and sliding word n-grams from each file and compares those digests to the
denylist.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import unquote

_WORD = re.compile(r"[^a-z0-9_-]+")
SKIP_DIR_NAMES = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".venv", "venv"}
# Pre-existing public trees that already carry their own clause-leak tooling.
# This Doctor leak test does not rewrite them.
SKIP_TOP_LEVEL = {"prototype", "scaffold"}


def normalize_text(text: str) -> str:
    text = unquote(text)
    text = text.lower()
    text = _WORD.sub(" ", text)
    return " ".join(text.split())


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def candidates_from_text(text: str) -> set[str]:
    """Return identifiers and sliding word n-grams (length 2-6)."""

    normalized = normalize_text(text)
    if not normalized:
        return set()
    words = normalized.split()
    out = set(words)
    for length in range(2, 7):
        if length > len(words):
            break
        for index in range(len(words) - length + 1):
            out.add(" ".join(words[index : index + length]))
    return out


def load_denylist(path: Path) -> set[str]:
    hashes: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if not re.fullmatch(r"[0-9a-f]{64}", line):
            raise ValueError(f"denylist line is not a SHA-256 hex digest: {line[:20]!r}")
        hashes.add(line)
    return hashes


def scan_text(text: str, denylist: set[str]) -> list[str]:
    """Return matching digests found in text (not the plaintext phrases)."""

    hits: list[str] = []
    seen: set[str] = set()
    for candidate in candidates_from_text(text):
        hashed = digest(candidate)
        if hashed in denylist and hashed not in seen:
            seen.add(hashed)
            hits.append(hashed)
    return hits


def iter_public_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if relative.parts and relative.parts[0] in SKIP_TOP_LEVEL:
            continue
        files.append(path)
    return files


def scan_tree(root: Path, denylist: set[str]) -> list[tuple[str, list[str]]]:
    """Scan a tree. Returns (relative path, matching digests) pairs."""

    findings: list[tuple[str, list[str]]] = []
    for path in iter_public_files(root):
        relative = path.relative_to(root).as_posix()
        # Always scan the path string itself so a leaked filename is caught.
        material = [relative]
        try:
            raw = path.read_bytes()
        except OSError as exc:
            findings.append((relative, [f"unreadable:{exc}"]))
            continue
        if b"\x00" in raw:
            text = raw.decode("utf-8", errors="ignore")
        else:
            text = raw.decode("utf-8", errors="replace")
        material.append(text)
        hits: list[str] = []
        for chunk in material:
            hits.extend(scan_text(chunk, denylist))
        # Preserve order, drop duplicates.
        unique: list[str] = []
        seen: set[str] = set()
        for item in hits:
            if item not in seen:
                seen.add(item)
                unique.append(item)
        if unique:
            findings.append((relative, unique))
    return findings
