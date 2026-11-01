"""Instantiate an empty programme package from the public template.

The package starts with empty ledgers, zero counts, and owner acceptance
PENDING. A placeholder manifest is written and then replaced with SHA-256
locks. Nothing in this step is a research result or an acceptance.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from package_files import package_relative_paths, rebuild_locks

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "programme"
PROGRAMME_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
EDITION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,31}$")


def substitute_tokens(root: Path, programme_id: str, edition: str) -> None:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix == ".pyc" or "__pycache__" in path.parts:
            continue
        data = path.read_bytes()
        if b"{{PROGRAMME_ID}}" not in data and b"{{EDITION}}" not in data:
            continue
        text = data.decode("utf-8")
        text = text.replace("{{PROGRAMME_ID}}", programme_id).replace("{{EDITION}}", edition)
        path.write_text(text, encoding="utf-8")


def instantiate(target: Path, programme_id: str, edition: str, journal: list | None = None) -> Path:
    """Copy the template into ``target`` and lock the new package.

    ``target`` must not already contain files. Returns the resolved target.
    """
    if not PROGRAMME_ID_RE.fullmatch(programme_id):
        raise ValueError(
            "programme id must be 1-64 characters of letters, digits, '.', '_' or '-'"
        )
    if not EDITION_RE.fullmatch(edition):
        raise ValueError("edition must be 1-32 characters of letters, digits, '.', '_', '+' or '-'")
    template = TEMPLATE
    if not template.is_dir():
        raise FileNotFoundError(f"programme template is missing: {template}")
    target = target.resolve()
    if target.exists():
        if not target.is_dir() or any(target.iterdir()):
            raise FileExistsError(f"TARGET_NONEMPTY: {target}")
        for item in template.iterdir():
            dest = target / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(template, target)
    substitute_tokens(target, programme_id, edition)
    # Declare every template file, write a placeholder manifest, then populate it.
    rebuild_locks(target, journal=journal)
    # Touch the path list so a caller can see the locked set without rereading.
    package_relative_paths(target)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create an empty programme package. Counts are zero and acceptance is PENDING. "
            "This does not produce research evidence."
        )
    )
    parser.add_argument("--target", required=True, help="Directory to create")
    parser.add_argument("--programme-id", required=True, help="Public programme identifier")
    parser.add_argument("--edition", default="0.0.0", help="Package edition label")
    args = parser.parse_args(argv)
    try:
        destination = instantiate(Path(args.target), args.programme_id, args.edition)
    except (ValueError, FileExistsError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"programme package written: {destination}")
    print(
        "Status is PENDING with zero research records, zero simulations, "
        "zero reviews, zero accepted credits, and production validation NOT_PERFORMED. "
        "Run validate_programme.py for a consistency check. "
        "That check does not accept the programme or award credit."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
