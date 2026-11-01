"""Index a private tablet corpus without writing into it.

The corpus is expected to live outside this repository. This tool reads the
markdown files of one paired tablet collection, prints or writes an index
somewhere else, and exits non-zero with a ``CORPUS_*`` message when the
directory is absent or the layout is not the expected one. It does not contain
tablet text. See CORPUS.md for the reading convention.

A *pair* is one technical tablet and the human companion written for the same
number. The two sides live in separate directories, use different file-name
patterns, and mark their clauses differently. All three differences are
handled here; see CORPUS.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# <NN>_<GEMSTONE>_TABLET.md  and  <NN>_<GEMSTONE>_HUMAN.md
TECHNICAL_FILE_RE = re.compile(r"^(\d{1,3})_([A-Z][A-Z0-9_]*)_TABLET\.md$")
HUMAN_FILE_RE = re.compile(r"^(\d{1,3})_([A-Z][A-Z0-9_]*)_HUMAN\.md$")
# "# 00 \u2014 The <Gemstone> Tablet"  and  "# 00 \u2014 The <Gemstone> Tablet \u2014 Human Version"
H1_RE = re.compile(r"^#[ \t]+(?:(\d{1,3})[ \t]*\u2014[ \t]*)?(\S.*?)[ \t]*$")
HUMAN_H1_SUFFIX_RE = re.compile(r"[ \t]*\u2014[ \t]*Human[ \t]+Version[ \t]*$", re.IGNORECASE)
# "### I — <title>" on either side.
H3_CLAUSE_RE = re.compile(r"^###[ \t]+([IVXLCDM]+)[ \t]*\u2014[ \t]*(\S.*?)[ \t]*$")
# "**I — <title>.**" on the human side.
BOLD_CLAUSE_RE = re.compile(r"^\*\*[ \t]*([IVXLCDM]+)[ \t]*\u2014[ \t]*(\S.*?)[ \t]*\*\*[ \t]*$")

ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
# Where the two sides sit under a corpus root.
TECHNICAL_HINTS = (
    "C2O Tablets/tablets",
    "C2O_Tablets/tablets",
    "tablets/technical",
    "technical",
    "tech",
)
HUMAN_HINTS = (
    "Human Tablets/tablets",
    "Human_Tablets/tablets",
    "tablets/human",
    "human",
    "humans",
)


def is_inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def normalise_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def roman_to_int(value: str) -> int:
    """Convert an additive-or-subtractive Roman numeral to an integer."""
    total = 0
    previous = 0
    for character in reversed(value.upper()):
        amount = ROMAN_VALUES.get(character)
        if amount is None:
            raise ValueError(f"CORPUS_FORMAT: {value!r} is not a Roman numeral")
        if amount < previous:
            total -= amount
        else:
            total += amount
            previous = amount
    return total


def strip_heading_period(title: str) -> str:
    """Drop one trailing period, which the bold clause style uses before the asterisks."""
    title = title.strip()
    return title[:-1].rstrip() if title.endswith(".") else title


def clause_heading(line: str) -> tuple[str, str] | None:
    """Return ``(roman, title)`` when ``line`` is a clause heading, else ``None``.

    Both sides and both human styles are accepted:

    - ``### I — Title`` on either side
    - ``**I — Title.**`` on the human side

    A level-3 heading whose first token is not a Roman numeral is not a clause
    heading; front matter uses such headings and is skipped rather than counted.
    """
    match = H3_CLAUSE_RE.match(line)
    if match:
        return match.group(1), strip_heading_period(match.group(2))
    match = BOLD_CLAUSE_RE.match(line)
    if match:
        return match.group(1), strip_heading_period(match.group(2))
    return None


def file_identity(path: Path, side: str) -> tuple[int, str]:
    """Return ``(tablet_number, gemstone)`` from a file name, or raise CORPUS_FORMAT."""
    pattern = TECHNICAL_FILE_RE if side == "technical" else HUMAN_FILE_RE
    match = pattern.match(path.name)
    if match is None:
        expected = "<number>_<GEMSTONE>_TABLET.md" if side == "technical" else "<number>_<GEMSTONE>_HUMAN.md"
        raise ValueError(f"CORPUS_FORMAT: {path.name} does not match {expected}")
    return int(match.group(1)), match.group(2)


def parse_side_file(path: Path, side: str) -> list[dict]:
    """Parse one tablet file into clauses.

    Each returned dict carries ``body`` for in-process comparison. The index
    written out strips ``body`` so the tool cannot become a way to copy corpus
    text into a file.
    """
    if path.is_symlink():
        raise ValueError(f"CORPUS_SYMLINK_REFUSED: refusing to follow symlink {path.name}")
    tablet_number, gemstone = file_identity(path, side)
    text = normalise_newlines(path.read_text(encoding="utf-8"))
    lines = text.split("\n")
    h1 = next((line for line in lines if line.startswith("# ")), "")
    h1_match = H1_RE.match(h1)
    if h1_match is None:
        raise ValueError(
            f"CORPUS_FORMAT: {path.name} must start with a '# <number> \u2014 <title>' heading"
        )
    # The number is taken from the file name. A heading that also carries one
    # must agree; the human side does not always repeat it.
    if h1_match.group(1) is not None and int(h1_match.group(1)) != tablet_number:
        raise ValueError(
            f"CORPUS_FORMAT: {path.name} tablet number does not match its heading"
        )
    if side == "technical" and h1_match.group(1) is None:
        raise ValueError(
            f"CORPUS_FORMAT: {path.name} technical heading must carry the tablet number"
        )
    raw_title = h1_match.group(2)
    heading_title = HUMAN_H1_SUFFIX_RE.sub("", raw_title) if side == "human" else raw_title
    if side == "human" and not HUMAN_H1_SUFFIX_RE.search(raw_title):
        raise ValueError(
            f"CORPUS_FORMAT: {path.name} is on the human side but its heading does not "
            "end with 'Human Version'"
        )

    clauses: list[dict] = []
    current: dict | None = None
    body_lines: list[str] = []

    def flush() -> None:
        nonlocal current, body_lines
        if current is None:
            return
        body = "\n".join(body_lines).strip("\n")
        current["body"] = body
        current["character_count"] = len(body)
        current["sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
        clauses.append(current)
        current = None
        body_lines = []

    for line in lines:
        heading = clause_heading(line.rstrip())
        if heading is not None:
            flush()
            roman, title = heading
            current = {
                "tablet_number": tablet_number,
                "gemstone": gemstone,
                "side": side,
                "clause_roman": roman.upper(),
                "clause_number": roman_to_int(roman),
                "clause_title": title,
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
    if numbers != sorted(numbers):
        raise ValueError(f"CORPUS_FORMAT: {path.name} clause numbers are out of order")
    if heading_title and clauses:
        clauses[0]["tablet_heading_title"] = heading_title
    return clauses


def residual_text(path: Path) -> str:
    """Return the file's text outside every clause body.

    This is the complement of the clause bodies: the preamble, the clause
    heading lines, and anything between or after clauses. A leak check compares
    both this and the clause bodies, so text that sits outside a clause body is
    still caught and the two comparisons cannot report the same passage twice.
    """
    if path.is_symlink():
        raise ValueError(f"CORPUS_SYMLINK_REFUSED: refusing to follow symlink {path.name}")
    kept: list[str] = []
    inside = False
    for line in normalise_newlines(path.read_text(encoding="utf-8")).split("\n"):
        if clause_heading(line.rstrip()) is not None:
            inside = True
            kept.append(line)
            continue
        if not inside:
            kept.append(line)
    return "\n".join(kept)


def resolve_side_dirs(root: Path) -> tuple[Path, Path]:
    """Find the technical and human tablet directories under ``root``.

    Explicit known locations are tried in order. The tree is not walked
    recursively, so an unrelated directory cannot be picked up by accident.
    """
    def first_existing(hints: tuple[str, ...]) -> Path | None:
        for hint in hints:
            candidate = root / hint
            if candidate.is_dir():
                return candidate
        return None

    technical = first_existing(TECHNICAL_HINTS)
    human = first_existing(HUMAN_HINTS)
    if technical is None:
        raise ValueError(
            "CORPUS_FORMAT: no technical tablet directory under "
            f"{root} (looked for {', '.join(TECHNICAL_HINTS)})"
        )
    if human is None:
        raise ValueError(
            "CORPUS_FORMAT: no human tablet directory under "
            f"{root} (looked for {', '.join(HUMAN_HINTS)})"
        )
    return technical, human


def side_files(directory: Path, side: str) -> list[Path]:
    """Immediate tablet files in ``directory``. Does not recurse."""
    pattern = TECHNICAL_FILE_RE if side == "technical" else HUMAN_FILE_RE
    if directory.is_symlink():
        raise ValueError(f"CORPUS_SYMLINK_REFUSED: refusing to follow symlink {directory}")
    found = sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and pattern.match(path.name)
    )
    return found


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


def build_index(technical: Path, human: Path) -> dict:
    """Parse both sides and reconcile them pair by pair."""
    technical_files = side_files(technical, "technical")
    human_files = side_files(human, "human")
    if not technical_files and not human_files:
        raise ValueError(
            f"CORPUS_EMPTY: no tablet files found in {technical} or {human}"
        )

    clauses: list[dict] = []
    by_number: dict[int, dict] = {}
    for path in technical_files:
        parsed = parse_side_file(path, "technical")
        clauses.extend(parsed)
        by_number.setdefault(parsed[0]["tablet_number"], {})["technical"] = (path, parsed)
    for path in human_files:
        parsed = parse_side_file(path, "human")
        clauses.extend(parsed)
        by_number.setdefault(parsed[0]["tablet_number"], {})["human"] = (path, parsed)

    pairs = []
    problems: list[str] = []
    for number in sorted(by_number):
        entry = by_number[number]
        technical_entry = entry.get("technical")
        human_entry = entry.get("human")
        pair = {
            "tablet_number": number,
            "technical_file": technical_entry[0].name if technical_entry else None,
            "human_file": human_entry[0].name if human_entry else None,
            "technical_clauses": len(technical_entry[1]) if technical_entry else 0,
            "human_clauses": len(human_entry[1]) if human_entry else 0,
            "paired": bool(technical_entry and human_entry),
        }
        if technical_entry is None:
            problems.append(f"UNPAIRED: tablet {number} has no technical file")
        if human_entry is None:
            problems.append(f"UNPAIRED: tablet {number} has no human file")
        if technical_entry and human_entry:
            gems = {technical_entry[1][0]["gemstone"], human_entry[1][0]["gemstone"]}
            if len(gems) > 1:
                problems.append(
                    f"GEMSTONE_MISMATCH: tablet {number} technical "
                    f"{technical_entry[1][0]['gemstone']} vs human {human_entry[1][0]['gemstone']}"
                )
            technical_numbers = [item["clause_number"] for item in technical_entry[1]]
            human_numbers = [item["clause_number"] for item in human_entry[1]]
            if technical_numbers != human_numbers:
                missing_pairs = sorted(
                    set(technical_numbers) ^ set(human_numbers)
                )
                problems.append(
                    f"CLAUSE_MISMATCH: tablet {number} technical has "
                    f"{len(technical_numbers)} clauses and human has {len(human_numbers)}; "
                    f"unmatched clause numbers {missing_pairs}"
                )
            if len(technical_numbers) != len(set(technical_numbers)):
                problems.append(f"DUPLICATE_CLAUSE: tablet {number} technical")
        pair["problems"] = [item for item in problems if f"tablet {number}" in item]
        pairs.append(pair)

    clauses.sort(
        key=lambda item: (
            item["tablet_number"],
            0 if item["side"] == "technical" else 1,
            item["clause_number"],
        )
    )
    public_clauses = [
        {key: value for key, value in item.items() if key != "body"}
        for item in clauses
    ]
    return {
        "corpus_digest": corpus_digest(clauses),
        "tablet_count": len(by_number),
        "paired_tablets": sum(1 for pair in pairs if pair["paired"]),
        "clause_count": len(clauses),
        "technical_clauses": sum(1 for item in clauses if item["side"] == "technical"),
        "human_clauses": sum(1 for item in clauses if item["side"] == "human"),
        "technical_files": len(technical_files),
        "human_files": len(human_files),
        "problems": problems,
        "pairs": pairs,
        "clauses": public_clauses,
    }


def iter_clause_bodies(technical: Path, human: Path) -> list[dict]:
    """Return clauses with their ``body``, for in-process comparison only."""
    bodies: list[dict] = []
    for path in side_files(technical, "technical"):
        bodies.extend(parse_side_file(path, "technical"))
    for path in side_files(human, "human"):
        bodies.extend(parse_side_file(path, "human"))
    return bodies


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read a private tablet collection and emit a clause index. "
            "Does not write into the corpus directory."
        )
    )
    parser.add_argument(
        "corpus",
        help=(
            "Corpus root containing both tablet directories, or the technical "
            "directory when --human is given"
        ),
    )
    parser.add_argument("--human", help="Human tablet directory")
    parser.add_argument("--technical", help="Technical tablet directory")
    parser.add_argument(
        "--output",
        help="Write the index JSON here. Refused when the path is inside the corpus. Default: stdout.",
    )
    args = parser.parse_args(argv)
    corpus = Path(args.corpus)
    if not corpus.exists():
        print(f"CORPUS_ABSENT: corpus directory does not exist: {corpus}", file=sys.stderr)
        return 2
    if not corpus.is_dir():
        print(f"CORPUS_NOT_A_DIRECTORY: corpus path is not a directory: {corpus}", file=sys.stderr)
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
        if args.technical and args.human:
            technical = Path(args.technical).resolve()
            human = Path(args.human).resolve()
            for side in (technical, human):
                if not side.is_dir():
                    raise ValueError(f"CORPUS_ABSENT: tablet directory does not exist: {side}")
        else:
            technical, human = resolve_side_dirs(corpus.resolve())
        index = build_index(technical, human)
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
    return 0 if not index["problems"] else 1


if __name__ == "__main__":
    sys.exit(main())
