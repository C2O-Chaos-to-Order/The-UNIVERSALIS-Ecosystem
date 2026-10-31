"""Corpus probe: read outside the repository, never write into the corpus.

Every fixture here is invented. Tablet numbers, gemstone tokens, clause titles
and clause bodies are placeholders written for these tests. No real tablet text
appears in this file.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
PROBE = TOOLS / "corpus_probe.py"
sys.path.insert(0, str(TOOLS))

from corpus_probe import build_index, clause_heading, roman_to_int

EM = "\u2014"
# The opt-in integration test reads a corpus only when the caller names one.
# Nothing here knows any machine's directory layout, so the test cannot depend
# on a path that happens to exist on one workstation.
CORPUS_ENV = "C2O_CORPUS_ROOT"


def _technical(number: int, gem: str, titles: list[str], body: str = "Placeholder technical body.") -> str:
    lines = [f"# {number:02d} {EM} The {gem.title()} Tablet", ""]
    for index, title in enumerate(titles):
        lines.append(f"### {_ROMANS[index]} {EM} {title}")
        lines.append("")
        lines.append(body)
        lines.append("")
    return "\n".join(lines)


def _human(number: int, gem: str, titles: list[str], bold: bool = True) -> str:
    lines = [f"# {number:02d} {EM} The {gem.title()} Tablet {EM} Human Version", ""]
    for index, title in enumerate(titles):
        if bold:
            lines.append(f"**{_ROMANS[index]} {EM} {title}.**  ")
        else:
            lines.append(f"### {_ROMANS[index]} {EM} {title}")
        lines.append("")
        lines.append("Placeholder human body.")
        lines.append("")
    return "\n".join(lines)


_ROMANS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"]
TITLES = [f"Of the placeholder number {index}" for index in range(1, 14)]


def _make_corpus(root: Path, tablets: int = 1, human_bold: bool = True) -> tuple[Path, Path]:
    technical = root / "C2O Tablets" / "tablets"
    human = root / "Human Tablets" / "tablets"
    technical.mkdir(parents=True)
    human.mkdir(parents=True)
    gems = ["Fixturegem", "Placeholdite", "Teststone"]
    for number in range(tablets):
        gem = gems[number % len(gems)]
        (technical / f"{number:02d}_{gem.upper()}_TABLET.md").write_text(
            _technical(number, gem, TITLES), encoding="utf-8"
        )
        (human / f"{number:02d}_{gem.upper()}_HUMAN.md").write_text(
            _human(number, gem, TITLES, bold=human_bold), encoding="utf-8"
        )
    return technical, human


class ClauseHeadingTests(unittest.TestCase):
    def test_level_three_heading_is_a_clause(self):
        self.assertEqual(clause_heading(f"### I {EM} SYNTHETIC CLAUSE TITLE"), ("I", "SYNTHETIC CLAUSE TITLE"))

    def test_bold_human_heading_is_a_clause(self):
        self.assertEqual(clause_heading(f"**I {EM} SYNTHETIC CLAUSE TITLE.**"), ("I", "SYNTHETIC CLAUSE TITLE"))

    def test_title_need_not_begin_with_of(self):
        # Requiring a leading "Of" was the defect that caused false mismatches.
        self.assertEqual(clause_heading(f"### V {EM} Distinction"), ("V", "Distinction"))
        self.assertEqual(clause_heading(f"**V {EM} Distinction.**"), ("V", "Distinction"))

    def test_non_numeral_heading_is_not_a_clause(self):
        self.assertIsNone(clause_heading("### SYNTHETIC FRONT MATTER HEADING"))
        self.assertIsNone(clause_heading("## SYNTHETIC DEDICATION HEADING"))
        self.assertIsNone(clause_heading("### Glossary"))

    def test_roman_numerals_convert(self):
        for text, expected in (
            ("I", 1), ("IV", 4), ("IX", 9), ("XIII", 13), ("XX", 20), ("XIV", 14),
        ):
            self.assertEqual(roman_to_int(text), expected, text)


class ProbeIndexTests(unittest.TestCase):
    def test_thirteen_clauses_per_file_are_reported(self):
        """A correctly formatted synthetic directory yields 13 clauses per file."""
        with tempfile.TemporaryDirectory() as tmp:
            technical, human = _make_corpus(Path(tmp), tablets=1)
            index = build_index(technical, human)
            self.assertEqual(index["technical_files"], 1)
            self.assertEqual(index["human_files"], 1)
            self.assertEqual(index["technical_clauses"], 13)
            self.assertEqual(index["human_clauses"], 13)
            self.assertEqual(index["clause_count"], 26)
            pair = index["pairs"][0]
            self.assertEqual(pair["technical_clauses"], 13)
            self.assertEqual(pair["human_clauses"], 13)
            self.assertTrue(pair["paired"])
            self.assertEqual(index["problems"], [])

    def test_human_level_three_style_also_yields_thirteen(self):
        with tempfile.TemporaryDirectory() as tmp:
            technical, human = _make_corpus(Path(tmp), tablets=1, human_bold=False)
            index = build_index(technical, human)
            self.assertEqual(index["human_clauses"], 13)
            self.assertEqual(index["problems"], [])

    def test_a_paired_collection_reconciles(self):
        with tempfile.TemporaryDirectory() as tmp:
            technical, human = _make_corpus(Path(tmp), tablets=3)
            index = build_index(technical, human)
            self.assertEqual(index["tablet_count"], 3)
            self.assertEqual(index["paired_tablets"], 3)
            self.assertEqual(index["clause_count"], 78)
            self.assertEqual(index["problems"], [])

    def test_the_index_does_not_carry_clause_bodies(self):
        with tempfile.TemporaryDirectory() as tmp:
            technical, human = _make_corpus(Path(tmp), tablets=1)
            index = build_index(technical, human)
            for clause in index["clauses"]:
                self.assertNotIn("body", clause)
                self.assertNotIn("Placeholder technical body", json.dumps(clause))

    def test_a_clause_count_mismatch_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            technical, human = _make_corpus(Path(tmp), tablets=1)
            path = human / "00_FIXTUREGEM_HUMAN.md"
            path.write_text(_human(0, "Fixturegem", TITLES[:12]), encoding="utf-8")
            index = build_index(technical, human)
            self.assertTrue(
                any("CLAUSE_MISMATCH" in problem for problem in index["problems"]),
                index["problems"],
            )

    def test_an_unpaired_tablet_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            technical, human = _make_corpus(Path(tmp), tablets=1)
            (human / "00_FIXTUREGEM_HUMAN.md").unlink()
            index = build_index(technical, human)
            self.assertTrue(any("UNPAIRED" in problem for problem in index["problems"]))

    def test_a_gemstone_mismatch_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            technical, human = _make_corpus(Path(tmp), tablets=1)
            (human / "00_FIXTUREGEM_HUMAN.md").rename(human / "00_OTHERGEM_HUMAN.md")
            index = build_index(technical, human)
            self.assertTrue(
                any("GEMSTONE_MISMATCH" in problem for problem in index["problems"]),
                index["problems"],
            )

    def test_a_human_heading_without_a_number_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            technical, human = _make_corpus(Path(tmp), tablets=1)
            path = human / "00_FIXTUREGEM_HUMAN.md"
            text = path.read_text(encoding="utf-8")
            text = text.replace(
                f"# 00 {EM} The Fixturegem Tablet {EM} Human Version",
                f"# The Fixturegem Tablet {EM} Human Version",
                1,
            )
            path.write_text(text, encoding="utf-8")
            index = build_index(technical, human)
            self.assertEqual(index["problems"], [])

    def test_a_technical_heading_without_a_number_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            technical, human = _make_corpus(Path(tmp), tablets=1)
            path = technical / "00_FIXTUREGEM_TABLET.md"
            text = path.read_text(encoding="utf-8").replace(
                f"# 00 {EM} The Fixturegem Tablet", f"# The Fixturegem Tablet", 1
            )
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(ValueError) as caught:
                build_index(technical, human)
            self.assertIn("technical heading must carry the tablet number", str(caught.exception))


class ProbeCliTests(unittest.TestCase):
    def test_absent_directory_exits_nonzero_and_is_not_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "absent-corpus"
            proc = subprocess.run(
                [sys.executable, str(PROBE), str(target)], capture_output=True, text=True
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("CORPUS_ABSENT", proc.stderr)
            self.assertIn(str(target), proc.stderr)
            self.assertFalse(target.exists())

    def test_cli_indexes_a_corpus_root_and_writes_outside_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            corpus = base / "corpus"
            _make_corpus(corpus, tablets=2)
            output = base / "index.json"
            proc = subprocess.run(
                [sys.executable, str(PROBE), str(corpus), "--output", str(output)],
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            index = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(index["paired_tablets"], 2)
            self.assertEqual(index["clause_count"], 52)

    def test_digest_is_stable_across_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            corpus = base / "corpus"
            _make_corpus(corpus, tablets=2)
            first = base / "a.json"
            second = base / "b.json"
            for target in (first, second):
                proc = subprocess.run(
                    [sys.executable, str(PROBE), str(corpus), "--output", str(target)],
                    capture_output=True, text=True,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(
                json.loads(first.read_text())["corpus_digest"],
                json.loads(second.read_text())["corpus_digest"],
            )

    def test_refuses_to_write_inside_the_corpus(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            corpus = base / "corpus"
            _make_corpus(corpus, tablets=1)
            before = sorted(p.as_posix() for p in corpus.rglob("*"))
            proc = subprocess.run(
                [sys.executable, str(PROBE), str(corpus), "--output", str(corpus / "index.json")],
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 3)
            self.assertIn("CORPUS_WRITE_REFUSED", proc.stderr)
            self.assertEqual(before, sorted(p.as_posix() for p in corpus.rglob("*")))

    def test_never_writes_into_the_corpus(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            corpus = base / "corpus"
            _make_corpus(corpus, tablets=2)
            before = {
                path.name: path.read_bytes()
                for path in corpus.rglob("*")
                if path.is_file()
            }
            subprocess.run(
                [sys.executable, str(PROBE), str(corpus), "--output", str(base / "out.json")],
                capture_output=True, text=True,
            )
            after = {
                path.name: path.read_bytes()
                for path in corpus.rglob("*")
                if path.is_file()
            }
            self.assertEqual(before, after)

    def test_a_wrong_file_name_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            corpus = base / "corpus"
            _make_corpus(corpus, tablets=1)
            (corpus / "C2O Tablets" / "tablets" / "00_FIXTUREGEM_TABLET.md").rename(
                corpus / "C2O Tablets" / "tablets" / "tablet-0-technical.md"
            )
            proc = subprocess.run(
                [sys.executable, str(PROBE), str(corpus)], capture_output=True, text=True
            )
            # The old convention is not a tablet file, so it is not picked up
            # and the tablet reads as unpaired.
            self.assertNotEqual(proc.returncode, 0)
            payload = json.loads(proc.stdout)
            self.assertTrue(any("UNPAIRED" in problem for problem in payload["problems"]))

    def test_a_symlinked_tablet_file_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            corpus = base / "corpus"
            technical, human = _make_corpus(corpus, tablets=1)
            real = technical / "00_FIXTUREGEM_TABLET.md"
            link = technical / "01_FIXTUREGEM_TABLET.md"
            link.symlink_to(real)
            (human / "01_FIXTUREGEM_HUMAN.md").write_text(
                _human(1, "Fixturegem", TITLES), encoding="utf-8"
            )
            proc = subprocess.run(
                [sys.executable, str(PROBE), str(corpus)], capture_output=True, text=True
            )
            self.assertEqual(proc.returncode, 1)
            self.assertIn("CORPUS_SYMLINK_REFUSED", proc.stderr)

    def test_the_old_invented_convention_no_longer_appears_in_the_probe(self):
        source = (TOOLS / "corpus_probe.py").read_text(encoding="utf-8")
        self.assertNotIn("tablet-(\\d+)-(technical|human)", source)
        self.assertNotIn("must start with a '# Tablet", source)

    def test_non_recursive_and_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            corpus = base / "corpus"
            technical, human = _make_corpus(corpus, tablets=1)
            nested = technical / "nested"
            nested.mkdir()
            (nested / "99_FIXTUREGEM_TABLET.md").write_text(
                _technical(99, "Fixturegem", TITLES), encoding="utf-8"
            )
            index = build_index(technical, human)
            self.assertEqual(index["technical_files"], 1)
            self.assertEqual(index["tablet_count"], 1)


class RealCorpusIntegrationTests(unittest.TestCase):
    """Opt-in check against the real private corpus.

    This test needs a corpus that is not part of the repository, so it skips
    cleanly when that corpus is absent rather than failing.
    """

    def test_real_corpus_parses_with_thirteen_clauses_per_file(self):
        root = os.environ.get(CORPUS_ENV)
        if not root:
            self.skipTest(f"set {CORPUS_ENV} to a private corpus root to run this")
        technical = Path(root) / "C2O Tablets" / "tablets"
        human = Path(root) / "Human Tablets" / "tablets"
        # Checked at run time rather than at class-definition time, so the test
        # still skips cleanly when the named root has no corpus in it.
        if not (technical.is_dir() and human.is_dir()):
            self.skipTest(f"{CORPUS_ENV} does not name a root containing both tablet sets")
        index = build_index(technical, human)
        self.assertEqual(index["problems"], [])
        self.assertEqual(
            index["technical_clauses"], index["human_clauses"]
        )
        for pair in index["pairs"]:
            self.assertTrue(pair["paired"])
            self.assertEqual(pair["technical_clauses"], 13, pair["technical_file"])
            self.assertEqual(pair["human_clauses"], 13, pair["human_file"])


if __name__ == "__main__":
    unittest.main()
