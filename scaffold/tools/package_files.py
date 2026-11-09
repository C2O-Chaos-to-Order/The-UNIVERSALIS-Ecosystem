"""Package paths, SHA-256 locks, and release-classification declarations.

``declare_public`` writes ``PUBLICLY_CLEARED`` onto named paths. It does not
review file contents and it is not a clearance decision. ``new_programme``
uses it for the public template only. Do not point it at a private corpus.

``write_manifest`` refreshes hashes. It never changes classifications.

``INTERNAL_CANDIDATE`` (K02) marks an uncleared candidate. It is admitted only
by ``validate_programme.py --profile internal-candidate`` and is never
release-ready. ``PUBLICLY_CLEARED`` on its own does not authorize release:
``--profile public-release`` also requires a cited owner authorization.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

PUBLIC_CLASSIFICATION = "PUBLICLY_CLEARED"
#: K02: an uncleared candidate. Valid only under the internal-candidate
#: validation profile; never release-ready and never accepted by the default
#: or public-release gates.
INTERNAL_CANDIDATE_CLASSIFICATION = "INTERNAL_CANDIDATE"
CLASSIFICATIONS = frozenset({PUBLIC_CLASSIFICATION, INTERNAL_CANDIDATE_CLASSIFICATION})
MANIFEST_REL = "metadata/sha256_manifest.json"
CLASSIFICATION_REL = "metadata/classifications.json"
SKIP_DIR_NAMES = frozenset({"__pycache__", ".git"})
PLACEHOLDER_MANIFEST = {"_placeholder": "populate me"}


def package_root(path: Path) -> Path:
    return path.resolve()


def iter_package_files(root: Path) -> list[Path]:
    """Return sorted files in ``root``, skipping caches and VCS directories."""
    root = package_root(root)
    found: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in SKIP_DIR_NAMES for part in relative.parts):
            continue
        found.append(path)
    found.sort(key=lambda item: item.relative_to(root).as_posix())
    return found


def relative_posix(root: Path, path: Path) -> str:
    return path.resolve().relative_to(package_root(root)).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def package_relative_paths(root: Path) -> list[str]:
    root = package_root(root)
    return [relative_posix(root, path) for path in iter_package_files(root)]


def declare_public(root: Path, relative_paths: list[str]) -> dict:
    """Set ``PUBLICLY_CLEARED`` on the given relative paths and preserve other keys.

    Existing values that are not ``PUBLICLY_CLEARED`` are left unchanged so a
    non-public mark cannot be overwritten by this helper.
    """
    root = package_root(root)
    class_path = root / CLASSIFICATION_REL
    current: dict = {}
    if class_path.is_file():
        loaded = json.loads(class_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            current = loaded
    for rel in relative_paths:
        name = Path(rel).as_posix()
        if name.startswith("/") or ".." in Path(name).parts or name in {"", "."}:
            raise ValueError(f"refusing to classify a non-package path: {rel}")
        if name in current and current[name] != PUBLIC_CLASSIFICATION:
            continue
        current[name] = PUBLIC_CLASSIFICATION
    write_json(class_path, current)
    return current


def write_placeholder_manifest(root: Path) -> None:
    """Write a manifest that is intentionally not a finished lockfile."""
    write_json(package_root(root) / MANIFEST_REL, PLACEHOLDER_MANIFEST)


def write_manifest(root: Path) -> dict:
    """Hash every package file except the manifest and write the lockfile."""
    root = package_root(root)
    manifest: dict[str, str] = {}
    for path in iter_package_files(root):
        rel = relative_posix(root, path)
        if rel == MANIFEST_REL:
            continue
        manifest[rel] = sha256_file(path)
    write_json(root / MANIFEST_REL, manifest)
    return manifest


def rebuild_locks(root: Path, journal: list | None = None) -> dict:
    """Declare the current files public, write a placeholder manifest, then populate it.

    ``journal``, when provided, receives the placeholder object after it is
    written and before the real manifest replaces it.
    """
    root = package_root(root)
    declare_public(root, package_relative_paths(root))
    write_placeholder_manifest(root)
    if journal is not None:
        journal.append(json.loads((root / MANIFEST_REL).read_text(encoding="utf-8")))
    return write_manifest(root)


def manifest_matches_package(root: Path) -> list[str]:
    """Return human-readable problems, or an empty list when the manifest matches."""
    root = package_root(root)
    class_path = root / CLASSIFICATION_REL
    reasons: list[str] = []
    if not class_path.is_file():
        reasons.append(f"CLASSIFICATION_GATE: {CLASSIFICATION_REL} is missing")
        return reasons
    classifications = json.loads(class_path.read_text(encoding="utf-8"))
    files = set(package_relative_paths(root))
    if not isinstance(classifications, dict):
        reasons.append("CLASSIFICATION_GATE: classifications file must be a JSON object")
        return reasons
    missing = sorted(files - set(classifications))
    if missing:
        reasons.append(
            "CLASSIFICATION_GATE: refusing to refresh the manifest while files have no classification: "
            + ", ".join(missing)
        )
    bad = sorted(
        name for name, value in classifications.items() if value != PUBLIC_CLASSIFICATION
    )
    if bad:
        reasons.append(
            "CLASSIFICATION_GATE: refusing to refresh the manifest while non-public classifications remain: "
            + ", ".join(bad)
        )
    return reasons


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Refresh metadata/sha256_manifest.json. Does not change classifications "
            "and does not treat a hash refresh as clearance or validation."
        )
    )
    parser.add_argument("--manifest", required=True, help="Programme package directory")
    args = parser.parse_args(argv)
    root = Path(args.manifest)
    if not root.is_dir():
        print(f"PACKAGE_ABSENT: package directory does not exist: {root}", file=sys.stderr)
        return 2
    reasons = manifest_matches_package(root)
    if reasons:
        for reason in reasons:
            print(reason, file=sys.stderr)
        return 1
    write_manifest(root)
    print(f"manifest refreshed for {root.resolve()}")
    print(
        "A refreshed manifest is a hash lock, not research evidence, "
        "owner acceptance, or production validation."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
