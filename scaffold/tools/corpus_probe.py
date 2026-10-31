"""Index a private tablet corpus without writing into it.

The corpus is expected to live outside this repository. This tool reads
markdown files, prints or writes an index somewhere else, and exits non-zero
when the directory is absent. It does not contain tablet text. See CORPUS.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

TABLET_FILE_RE = re.compile(r"^tablet-(\d+)-(technical|human)\.md$", re.IGNORECASE)
H1_RE = re.compile(r"^#[ \t]+Tablet[ \t]+(\d+)\b", re.IGNORECASE)
CLAUSE_RE = re.compile(
    r"^##[ \t]+(?:Clause[ \t]+)?(\d+)[ \t]*[:.\u2014\u2013\-][ \t]+(.+?)[ \t]*$"
)


def is_inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def parse_tablet(path: Path) -> list[dict]:
    match = TABLET_FILE_RE.match(path.name)
    if match is None:
        raise ValueError(
            f"CORPUS_FORMAT: {path.name} does not match tablet-<number>-<technical|human>.md"
        )
    if path.is_symlink():
        raise ValueError(f"CORPUS_SYMLINK_REFUSED: refusing to follow symlink {path.name}")
    tablet_number = int(match.group(1))
    side = match.group(2).lower()
    text = normalize_newlines(path.read_text(encoding="utf-8"))
    lines = text.split("\n")
    h1 = next((line for line in lines if line.startswith("# ")), "")
    h1_match = H1_RE.match(h1)
    if h1_match is None:
        raise ValueError(
            f"CORPUS_FORMAT: {path.name} must start with a '# Tablet <number>' heading"
        )
    if int(h1_match.group(1)) != tablet_number:
        raise ValueError(
            f"CORPUS_FORMAT: {path.name} tablet number does not match its heading"
        )
    clauses: list[dict] = []
    current: dict | None = None
    body_lines: list[str] = []

    def flush() -> None:
        nonlocal current, body_lines
        if current is None:
            return
        body = "\n".join(body_lines).strip("\n")
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        current["character_count"] = len(body)
        current["sha256"] = digest
        clauses.append(current)
        current = None
        body_lines = []

    for line in lines:
        heading = CLAUSE_RE.match(line)
        if heading:
            flush()
            current = {
                "tablet_number": tablet_number,
                "side": side,
                "clause_number": int(heading.group(1)),
                "clause_title": heading.group(2).strip(),
            }
            body_lines = []
            continue
        if current is not None:
            body_lines.append(line)
    flush()
    if not clauses:
        raise ValueError(f"CORPUS_FORMAT: {path.name} contains no clause headings")
    numbers = [item["clause_number"] for item in clauses]
    if len(numbers) != len(set(numbers)):
        raise ValueError(f"CORPUS_FORMAT: {path.name} repeats a clause number")
    return clauses


def corpus_digest(clauses: list[dict]) -> str:
    lines = []
    ordered = sorted(
        clauses,
        key=lambda item: (
            item["tablet_number"],
            0 if item["side"] == "technical" else 1,
            item["clause_number"],
        ),
    )
    for item in ordered:
        lines.append(
            json.dumps(
                {
                    "character_count": item["character_count"],
                    "clause_number": item["clause_number"],
                    "clause_title": item["clause_title"],
                    "sha256": item["sha256"],
                    "side": item["side"],
                    "tablet_number": item["tablet_number"],
                },
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
        )
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_index(corpus: Path) -> dict:
    clauses: list[dict] = []
    tablet_files = sorted(
        path for path in corpus.iterdir() if path.is_file() and path.suffix.lower() == ".md"
    )
    if not tablet_files:
        raise ValueError(
            f"CORPUS_EMPTY: no tablet markdown files found in {corpus}"
        )
    for path in tablet_files:
        clauses.extend(parse_tablet(path))
    clauses.sort(
        key=lambda item: (
            item["tablet_number"],
            0 if item["side"] == "technical" else 1,
            item["clause_number"],
        )
    )
    return {
        "corpus_digest": corpus_digest(clauses),
        "clause_count": len(clauses),
        "clauses": clauses,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read a private tablet directory and emit a clause index. "
            "Does not write into the corpus directory."
        )
    )
    parser.add_argument("corpus", help="Directory of tablet markdown files")
    parser.add_argument(
        "--output",
        help="Write the index JSON here. Refused when the path is inside the corpus. Default: stdout.",
    )
    args = parser.parse_args(argv)
    corpus = Path(args.corpus)
    if not corpus.exists():
        print(
            f"CORPUS_ABSENT: corpus directory does not exist: {corpus}",
            file=sys.stderr,
        )
        return 2
    if not corpus.is_dir():
        print(
            f"CORPUS_NOT_A_DIRECTORY: corpus path is not a directory: {corpus}",
            file=sys.stderr,
        )
        return 2
    if args.output and args.output != "-":
        destination = Path(args.output)
        if is_inside(destination, corpus):
            print(
                f"CORPUS_WRITE_REFUSED: refusing to write inside the corpus directory: {destination}",
                file=sys.stderr,
            )
            return 3
    try:
        index = build_index(corpus.resolve())
    except UnicodeDecodeError as exc:
        print(f"CORPUS_FORMAT: unable to read corpus file as UTF-8 ({exc})", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    rendered = json.dumps(index, indent=2, ensure_ascii=False) + "\n"
    if args.output and args.output != "-":
        destination = Path(args.output)
        if is_inside(destination, corpus):
            print(
                f"CORPUS_WRITE_REFUSED: refusing to write inside the corpus directory: {destination}",
                file=sys.stderr,
            )
            return 3
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8")
        print(f"index written outside the corpus: {destination.resolve()}")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
