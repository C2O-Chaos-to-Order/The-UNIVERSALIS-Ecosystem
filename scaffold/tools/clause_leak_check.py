"""Report the longest shared character run between public files and clause bodies.

The private corpus is expected to live outside this repository. This tool reads
it, reads one or more public paths, and reports how much character-level text
they share after whitespace normalisation. It never writes into the corpus and
it refuses a corpus path that is inside this repository.

A shared run is a leakage signal, not proof of copying: common formulaic
openings in a language will produce short shared runs by chance. The default
threshold of 40 characters is far above that noise floor. The tool does not
decide whether a passage is a quotation, a paraphrase, or a coincidence; it
reports the longest run and the files it was found in.

Exits non-zero when any pair exceeds the threshold.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from corpus_probe import build_index, is_inside

DEFAULT_THRESHOLD = 40
# Repository root: this file is scaffold/tools/clause_leak_check.py.
REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_SUFFIXES = frozenset({".py", ".md", ".json", ".csv", ".txt", ".rst", ".toml", ".cfg"})
WHITESPACE = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Collapse every whitespace run to one space and strip the ends."""
    return WHITESPACE.sub(" ", text).strip()


def longest_common_run(left: str, right: str) -> str:
    """Return one longest substring shared by ``left`` and ``right``.

    Linear-space dynamic programming over suffixes: two rows of the classic LCS
    table, tracking the best match. Ties return the earliest match found, which
    is enough to report the extent of an overlap.
    """
    if not left or not right:
        return ""
    best_length = 0
    best_end_in_left = 0
    previous = [0] * (len(right) + 1)
    for i, left_char in enumerate(left, start=1):
        current = [0] * (len(right) + 1)
        for j, right_char in enumerate(right, start=1):
            if left_char == right_char:
                current[j] = previous[j - 1] + 1
                if current[j] > best_length:
                    best_length = current[j]
                    best_end_in_left = i
        previous = current
    if best_length == 0:
        return ""
    return left[best_end_in_left - best_length : best_end_in_left]


def public_files(paths: list[Path]) -> list[Path]:
    """Expand public paths to files, skipping caches and VCS directories."""
    found: list[Path] = []
    for item in paths:
        item = Path(item)
        if item.is_file():
            found.append(item)
            continue
        if not item.is_dir():
            raise FileNotFoundError(f"PUBLIC_PATH_ABSENT: {item}")
        for path in sorted(item.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(item)
            if any(part in {".git", "__pycache__"} for part in relative.parts):
                continue
            if path.suffix not in PUBLIC_SUFFIXES:
                continue
            found.append(path)
    return found


def clause_bodies(corpus: Path) -> list[dict]:
    """Return one dict per clause with its identifier and its body text."""
    bodies: list[dict] = []
    for path in sorted(corpus.iterdir()):
        if not path.is_file() or path.suffix.lower() != ".md" or path.is_symlink():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").replace("\r\n", "\n")
        # Bodies are read from the same heading split the probe uses, so the
        # two tools cannot disagree about where a clause begins.
        current = None
        buffer: list[str] = []
        for line in text.replace("\r", "\n").split("\n"):
            heading = re.match(r"^##[ \t]+(?:Clause[ \t]+)?(\d+)\b", line)
            if heading:
                if current is not None:
                    bodies.append({"clause": current, "body": "\n".join(buffer)})
                current = heading.group(1)
                buffer = []
                continue
            if current is not None:
                buffer.append(line)
        if current is not None:
            bodies.append({"clause": current, "body": "\n".join(buffer)})
    return bodies


def check(corpus: Path, public: list[Path], threshold: int = DEFAULT_THRESHOLD) -> dict:
    """Compare every public file against every clause body.

    Returns a report with the worst shared run and every pair over threshold.
    """
    corpus = corpus.resolve()
    if is_inside(corpus, REPO_ROOT):
        raise ValueError(
            "CORPUS_INSIDE_REPOSITORY: refusing to read a corpus path inside this "
            f"repository: {corpus}"
        )
    if not corpus.is_dir():
        raise ValueError(f"CORPUS_ABSENT: corpus directory does not exist: {corpus}")
    # The probe's index is built first so a malformed corpus fails the same way
    # it does for the probe, rather than silently yielding no bodies.
    build_index(corpus)
    bodies = [
        (f"clause {entry['clause']}", normalise(entry["body"]))
        for entry in clause_bodies(corpus)
        if normalise(entry["body"])
    ]
    findings = []
    worst = {"length": 0, "public": None, "clause": None, "run": ""}
    for path in public_files(public):
        public_text = normalise(path.read_text(encoding="utf-8", errors="ignore"))
        if not public_text:
            continue
        for label, body in bodies:
            run = longest_common_run(public_text, body)
            if len(run) > worst["length"]:
                worst = {
                    "length": len(run),
                    "public": str(path),
                    "clause": label,
                    "run": run,
                }
            if len(run) > threshold:
                findings.append(
                    {
                        "public": str(path),
                        "clause": label,
                        "length": len(run),
                        "run": run,
                    }
                )
    return {
        "corpus": str(corpus),
        "threshold": threshold,
        "public_files": len(public_files(public)),
        "clauses": len(bodies),
        "worst": worst,
        "over_threshold": findings,
        "ok": not findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Report the longest shared character run between public files and private "
            "clause bodies. Never writes into the corpus."
        )
    )
    parser.add_argument("corpus", help="Private corpus directory, outside this repository")
    parser.add_argument("public", nargs="+", help="Public file or directory paths")
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD,
        help=f"Shared-run length that fails the check (default {DEFAULT_THRESHOLD})",
    )
    args = parser.parse_args(argv)
    try:
        report = check(Path(args.corpus), [Path(item) for item in args.public], args.threshold)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    worst = report["worst"]
    print(
        f"compared {report['public_files']} public file(s) against "
        f"{report['clauses']} clause body/bodies"
    )
    print(
        f"longest shared run: {worst['length']} characters "
        f"(threshold {report['threshold']})"
    )
    if worst["public"]:
        print(f"  between {worst['public']} and {worst['clause']}")
    for finding in report["over_threshold"]:
        print(
            f"LEAK_SUSPECTED: {finding['length']} characters shared between "
            f"{finding['public']} and {finding['clause']}",
            file=sys.stderr,
        )
    if not report["ok"]:
        return 1
    print("no shared run exceeds the threshold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
