"""Report the longest shared character run between public files and clause bodies.

The private corpus is expected to live outside this repository. This tool reads
it, reads one or more public paths, and reports how much character-level text
they share after whitespace normalisation. It never writes into the corpus and
it refuses a corpus path that is inside this repository.

A shared run is a leakage signal, not proof of copying: common formulaic
openings in a language will produce short shared runs by chance. The default
threshold of 40 characters sits far above that noise floor. The tool does not
decide whether a passage is a quotation, a paraphrase, or a coincidence; it
reports the longest run and the pair it was found in.

The comparison runs over two disjoint sets of targets, so text anywhere in the
corpus is covered without any passage being counted twice:

- each parsed clause body, using the same reader ``corpus_probe.py`` uses, so
  the two tools cannot disagree about where a clause begins;
- each file's text outside every clause body: the preamble, the clause heading
  lines, and anything between or after clauses.

A copied passage therefore lands on exactly one of them. Comparing clause
bodies and also whole files would report the same run twice at the same length,
which is a duplicate, not a second finding.

Exits non-zero when any pair exceeds the threshold.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from corpus_probe import (
    TECHNICAL_HINTS,
    is_inside,
    parse_side_file,
    residual_text,
    resolve_side_dirs,
    side_files,
)

DEFAULT_THRESHOLD = 40
# Repository root: this file is scaffold/tools/clause_leak_check.py.
REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_SUFFIXES = frozenset({".py", ".md", ".json", ".csv", ".txt", ".rst", ".toml", ".cfg"})
WHITESPACE = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Collapse every whitespace run to one space and strip the ends."""
    return WHITESPACE.sub(" ", text).strip()


MODULUS = (1 << 61) - 1
BASE = 1_000_003


def _rolling_hashes(text: str, width: int) -> list[int]:
    """Return a hash for every ``width``-character window of ``text``.

    Polynomial rolling hash modulo ``2**61 - 1``. Deterministic across runs,
    unlike the built-in ``hash``, so a reported result can be reproduced.
    """
    length = len(text)
    if width <= 0 or length < width:
        return []
    highest = pow(BASE, width - 1, MODULUS)
    hashes: list[int] = []
    value = 0
    for index in range(width):
        value = (value * BASE + ord(text[index])) % MODULUS
    hashes.append(value)
    for index in range(width, length):
        value = (
            (value - ord(text[index - width]) * highest) % MODULUS * BASE
            + ord(text[index])
        ) % MODULUS
        hashes.append(value)
    return hashes


def longest_common_run(left: str, right: str) -> str:
    """Return one longest substring shared by ``left`` and ``right``.

    Exact, but quadratic, so it is used only for small inputs and in tests. The
    comparison in :func:`check` uses the seeded approach in
    :func:`verify_run`, which is what makes a whole-corpus scan affordable.
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


def _extend(public_text: str, public_start: int, body: str, body_start: int, width: int) -> int:
    """Extend a match known to be at least ``width`` characters long."""
    left = 0
    while (
        public_start - left > 0
        and body_start - left > 0
        and public_text[public_start - left - 1] == body[body_start - left - 1]
    ):
        left += 1
    right = width
    while (
        public_start + right < len(public_text)
        and body_start + right < len(body)
        and public_text[public_start + right] == body[body_start + right]
    ):
        right += 1
    return left + right


# A pathological pair could share one very common k-gram thousands of times.
# Beyond this many verified position pairs the result is reported as a lower
# bound rather than spending unbounded time; the count is surfaced so a caller
# can see it happened.
MAX_VERIFICATIONS_PER_PAIR = 20_000


def longest_shared_run(
    public_text: str,
    body: str,
    width: int,
    shared: set[int],
) -> tuple[int, bool]:
    """Longest run shared by ``public_text`` and ``body`` that is at least ``width``.

    ``shared`` holds k-gram hashes known to occur in both sides, so only those
    windows are examined. Every occurrence is verified, not only the first: the
    same k-gram can appear more than once in either text and extend differently
    each time, and reporting only the first would understate a leak.

    Returns ``(length, complete)``. ``length`` is ``0`` when no run of ``width``
    characters or more exists. ``complete`` is ``False`` when the verification
    cap was reached.
    """
    if len(public_text) < width or len(body) < width or not shared:
        return 0, True
    body_index: dict[int, list[int]] = {}
    for start, digest in enumerate(_rolling_hashes(body, width)):
        if digest in shared:
            body_index.setdefault(digest, []).append(start)
    if not body_index:
        return 0, True
    best = 0
    verified = 0
    for start, digest in enumerate(_rolling_hashes(public_text, width)):
        positions = body_index.get(digest)
        if not positions:
            continue
        seed = public_text[start : start + width]
        for body_start in positions:
            if verified >= MAX_VERIFICATIONS_PER_PAIR:
                return best, False
            if body[body_start : body_start + width] != seed:
                continue  # hash collision
            verified += 1
            length = _extend(public_text, start, body, body_start, width)
            if length > best:
                best = length
    return best, True


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


def _candidate_bodies(corpus: Path) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Return ``(clause_bodies, residual_bodies)`` for the corpus.

    The two lists are complements of each other. ``clause_bodies`` are the
    parsed clause bodies. ``residual_bodies`` are each tablet file's text
    outside every clause body: preamble, clause heading lines, and inter-clause
    or trailing material. Because they do not overlap, a copied passage is
    reported on exactly one of them and can never be counted twice.
    """
    technical, human = resolve_side_dirs(corpus)
    clauses: list[tuple[str, str]] = []
    residual: list[tuple[str, str]] = []
    for side, directory in (("technical", technical), ("human", human)):
        for path in side_files(directory, side):
            for entry in parse_side_file(path, side):
                body = normalise(entry["body"])
                if body:
                    clauses.append((f"{path.name} clause {entry['clause_roman']}", body))
            outside = normalise(residual_text(path))
            if outside:
                residual.append((f"{path.name} outside clause bodies", outside))
    if not clauses and not residual:
        raise ValueError(f"CORPUS_EMPTY: no tablet files found in {corpus}")
    return clauses, residual


def check(
    corpus: Path,
    public: list[Path],
    threshold: int = DEFAULT_THRESHOLD,
) -> dict:
    """Compare every public file against every clause-body and residual target.

    A run is reported only when it reaches ``threshold + 1`` characters, so the
    k-gram width is set to that value: any reportable run contains a
    ``threshold + 1``-character window, so seeding at that width cannot miss
    one.

    The comparison is filtered before it is verified. Each target's k-gram
    hashes are computed once, and a public file is only examined against a
    target when the two share at least one window. Without that filter the scan
    is quadratic over whole files and does not finish on a real corpus.
    """
    corpus = corpus.resolve()
    if is_inside(corpus, REPO_ROOT):
        raise ValueError(
            "CORPUS_INSIDE_REPOSITORY: refusing to read a corpus path inside this "
            f"repository: {corpus}"
        )
    if not corpus.is_dir():
        raise ValueError(f"CORPUS_ABSENT: corpus directory does not exist: {corpus}")
    if not any((corpus / hint).is_dir() for hint in TECHNICAL_HINTS):
        raise ValueError(
            "CORPUS_FORMAT: no technical tablet directory under "
            f"{corpus} (looked for {', '.join(TECHNICAL_HINTS)})"
        )
    clause_bodies, residual_bodies = _candidate_bodies(corpus)
    width = threshold + 1
    prepared = []
    everything: set[int] = set()
    for axis, targets in (
        ("clause_body", clause_bodies),
        ("outside_clause_bodies", residual_bodies),
    ):
        for label, body in targets:
            hashes = set(_rolling_hashes(body, width))
            prepared.append((axis, label, body, hashes))
            everything |= hashes
    public_paths = public_files(public)
    findings: list[dict] = []
    worst = {"length": 0, "public": None, "clause": None}
    incomplete: list[str] = []
    for path in public_paths:
        public_text = normalise(path.read_text(encoding="utf-8", errors="ignore"))
        if not public_text:
            continue
        # One pass over the public file. If it shares no window with any target
        # at all, every pair would score zero and the whole file is skipped.
        public_hashes = set(_rolling_hashes(public_text, width))
        candidates = public_hashes & everything
        if not candidates:
            continue
        for axis, label, body, body_hashes in prepared:
            shared = candidates & body_hashes
            if not shared:
                continue
            length, complete = longest_shared_run(public_text, body, width, shared)
            if not complete:
                incomplete.append(f"{path} <- {label}")
            if length > worst["length"]:
                worst = {"length": length, "public": str(path), "clause": label}
            if length > threshold:
                findings.append(
                    {
                        "public": str(path),
                        "clause": label,
                        "length": length,
                        "axis": axis,
                    }
                )
    return {
        "corpus": str(corpus),
        "threshold": threshold,
        "public_files": len(public_paths),
        "clause_bodies": len(clause_bodies),
        "residual_bodies": len(residual_bodies),
        "worst": worst,
        "over_threshold": findings,
        "incomplete": incomplete,
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
    parser.add_argument(
        "--list",
        action="store_true",
        help="List every pair over the threshold, not only the worst.",
    )
    args = parser.parse_args(argv)
    try:
        report = check(Path(args.corpus), [Path(item) for item in args.public], args.threshold)
    except (ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    worst = report["worst"]
    print(
        f"compared {report['public_files']} public file(s) against "
        f"{report['clause_bodies']} clause body/bodies and "
        f"{report['residual_bodies']} outside-clause-body target(s)"
    )
    print(
        f"longest shared run: {worst['length']} characters "
        f"(threshold {report['threshold']})"
    )
    if worst["public"]:
        print(f"  between {worst['public']}")
        print(f"  and     {worst['clause']}")
    if args.list:
        for finding in report["over_threshold"]:
            print(
                f"  {finding['length']:>5} chars  {finding['public']}  <-  {finding['clause']}"
            )
    for finding in report["over_threshold"]:
        print(
            f"LEAK_SUSPECTED: {finding['length']} characters shared between "
            f"{finding['public']} and {finding['clause']} [{finding['axis']}]",
            file=sys.stderr,
        )
    if report["incomplete"]:
        print(
            f"WARNING: {len(report['incomplete'])} pair(s) hit the verification cap; "
            "their reported length is a lower bound",
            file=sys.stderr,
        )
    if not report["ok"]:
        return 1
    print("no shared run exceeds the threshold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
