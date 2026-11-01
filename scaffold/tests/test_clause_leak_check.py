"""Clause leak check: synthetic placeholders only, never real clause text.

Every tablet number, gemstone token, clause title and clause body in this file
is invented for the test. No real corpus text appears here.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from clause_leak_check import (
    _rolling_hashes,
    check,
    longest_common_run,
    longest_shared_run,
    normalise,
)

LEAK_CHECK = TOOLS / "clause_leak_check.py"
EM = "\u2014"

# A synthetic body. It is invented for this test and is not manuscript text.
PLACEHOLDER_BODY = (
    "PLACEHOLDER BODY ALPHA. This sentence exists only to give the overlap "
    "detector something long enough to match against a public fixture."
)
# Synthetic preamble that sits outside every clause body.
PLACEHOLDER_PREAMBLE = (
    "PREAMBLE FILLER OUTSIDE EVERY CLAUSE BODY. Written only to test that text "
    "between the heading and the first clause is still compared."
)


def _make_corpus(root: Path, body: str = PLACEHOLDER_BODY, preamble: str = "") -> Path:
    technical = root / "C2O Tablets" / "tablets"
    human = root / "Human Tablets" / "tablets"
    technical.mkdir(parents=True)
    human.mkdir(parents=True)
    head = f"# 00 {EM} The Fixturegem Tablet\n\n"
    if preamble:
        head += preamble + "\n\n"
    (technical / "00_FIXTUREGEM_TABLET.md").write_text(
        head + f"### I {EM} Of the placeholder\n\n{body}\n", encoding="utf-8"
    )
    (human / "00_FIXTUREGEM_HUMAN.md").write_text(
        f"# 00 {EM} The Fixturegem Tablet {EM} Human Version\n\n"
        f"**I {EM} Of the placeholder.**\n\nPlaceholder human body.\n",
        encoding="utf-8",
    )
    return root


class LongestRunTests(unittest.TestCase):
    def test_whitespace_is_normalised_before_comparison(self):
        self.assertEqual(normalise("  a   b\n\nc\t"), "a b c")
        self.assertEqual(
            longest_common_run(normalise("a   b\nc"), normalise("a b c")), "a b c"
        )

    def test_no_overlap_returns_empty(self):
        self.assertEqual(longest_common_run("abcdef", "ghijkl"), "")

    def test_longest_run_is_returned(self):
        self.assertEqual(longest_common_run("xxABCDEFGxx", "yyABCDEFGyy"), "ABCDEFG")


class FastPathEquivalenceTests(unittest.TestCase):
    """The seeded fast path must agree with the exact quadratic algorithm.

    The fast path only looks at k-grams present in both texts. An earlier
    version deduplicated those seeds by hash and so under-reported runs that
    occurred more than once and extended differently each time. These tests
    pin the equivalence, including that repeated-seed case.
    """

    def _compare(self, left: str, right: str, width: int) -> None:
        exact = len(longest_common_run(left, right))
        expected = exact if exact >= width else 0
        shared = set(_rolling_hashes(left, width)) & set(_rolling_hashes(right, width))
        got, complete = longest_shared_run(left, right, width, shared)
        self.assertTrue(complete)
        self.assertEqual(got, expected, f"width={width} left={left!r} right={right!r}")

    def test_repeated_seed_extending_differently_is_not_under_reported(self):
        # "ab" occurs twice in the right side, and only the second occurrence
        # continues into the long run. Reporting the first occurrence only
        # would return 2 instead of 6.
        self._compare("xxabcdefxx", "abYYabcdefYY", 2)
        self._compare("zzabcdezz", "abQabcdeQ", 2)

    def test_random_cases_agree_with_the_exact_algorithm(self):
        import random

        rng = random.Random(20261031)
        alphabet = "abc ."
        for _ in range(60):
            left = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 60)))
            right = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 60)))
            for width in (1, 2, 4, 9):
                self._compare(left, right, width)

    def test_a_run_shorter_than_the_width_is_not_reported(self):
        self._compare("abcd" * 3, "abcde" * 2, 10)


class LeakCheckTests(unittest.TestCase):
    def test_short_overlap_passes_and_long_overlap_fails(self):
        """One copied clause body is ONE finding, not two.

        The same run is present in the clause body and in the whole file. Both
        are compared, so a naive implementation reports it twice. The two axes
        are disjoint by construction, so it must be reported exactly once, on
        the clause-body axis and at the full length of the copied body.
        """
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            corpus = _make_corpus(base / "corpus")

            clean = base / "clean.md"
            clean.write_text(
                "A corpus-agnostic note that shares only short formulaic runs.\n",
                encoding="utf-8",
            )
            passing = check(corpus, [clean], threshold=40)
            self.assertTrue(passing["ok"])
            self.assertEqual(passing["over_threshold"], [])
            self.assertLessEqual(passing["worst"]["length"], 40)

            leaky = base / "leaky.md"
            leaky.write_text("Here is a copied passage: " + PLACEHOLDER_BODY + "\n", encoding="utf-8")
            failing = check(corpus, [leaky], threshold=40)
            self.assertFalse(failing["ok"])
            self.assertEqual(
                len(failing["over_threshold"]),
                1,
                f"expected one finding, got {failing['over_threshold']}",
            )
            finding = failing["over_threshold"][0]
            self.assertEqual(finding["clause"], "00_FIXTUREGEM_TABLET.md clause I")
            self.assertEqual(finding["axis"], "clause_body")
            self.assertEqual(finding["length"], len(PLACEHOLDER_BODY))

    def test_text_outside_every_clause_body_is_still_caught(self):
        """A leak in the preamble is outside every clause body.

        This is the test that proves de-duplication did not quietly disable the
        whole-file comparison: the copied text is in no clause body, so only
        the outside-clause-body axis can find it.
        """
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            corpus = _make_corpus(base / "corpus", preamble=PLACEHOLDER_PREAMBLE)
            public = base / "preamble.md"
            public.write_text(PLACEHOLDER_PREAMBLE + "\n", encoding="utf-8")

            report = check(corpus, [public], threshold=40)
            self.assertFalse(report["ok"])
            self.assertEqual(
                len(report["over_threshold"]),
                1,
                f"expected one finding, got {report['over_threshold']}",
            )
            finding = report["over_threshold"][0]
            self.assertEqual(finding["axis"], "outside_clause_bodies")
            self.assertEqual(finding["clause"], "00_FIXTUREGEM_TABLET.md outside clause bodies")
            self.assertEqual(finding["length"], len(PLACEHOLDER_PREAMBLE))
            # It is genuinely outside every clause body, which is why only this
            # axis can see it.
            self.assertFalse(
                any(
                    item["axis"] == "clause_body"
                    for item in report["over_threshold"]
                )
            )

    def test_threshold_is_configurable(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            corpus = _make_corpus(base / "corpus", body="SHORT PLACEHOLDER RUN HERE")
            public = base / "public.md"
            public.write_text("SHORT PLACEHOLDER RUN HERE\n", encoding="utf-8")
            self.assertTrue(check(corpus, [public], threshold=40)["ok"])
            self.assertFalse(check(corpus, [public], threshold=10)["ok"])

    def test_cli_exits_nonzero_above_threshold_and_zero_below(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            corpus = _make_corpus(base / "corpus")
            public = base / "public.md"
            public.write_text(PLACEHOLDER_BODY + "\n", encoding="utf-8")
            over = subprocess.run(
                [sys.executable, str(LEAK_CHECK), str(corpus), str(public)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(over.returncode, 1, over.stdout + over.stderr)
            self.assertIn("LEAK_SUSPECTED", over.stderr)
            self.assertIn("[clause_body]", over.stderr)

            under = subprocess.run(
                [sys.executable, str(LEAK_CHECK), str(corpus), str(public), "--threshold", "5000"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(under.returncode, 0, under.stdout + under.stderr)
            self.assertIn("no shared run exceeds the threshold", under.stdout)

    def test_cli_reports_that_short_runs_were_not_measured(self):
        """A clean run must not claim zero overlap; it never looked that far down."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            corpus = _make_corpus(base / "corpus")
            public = base / "public.md"
            public.write_text(PLACEHOLDER_BODY + "\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(LEAK_CHECK),
                    str(corpus),
                    str(public),
                    "--threshold",
                    "5000",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("search width: 5001 characters", result.stdout)
            self.assertIn("no run of 5001 characters or more was found", result.stdout)
            self.assertIn("are not measured", result.stdout)
            self.assertNotIn("longest shared run: 0 characters", result.stdout)

    def test_refuses_a_corpus_inside_the_repository(self):
        repo = Path(__file__).resolve().parents[2]
        fake_corpus = repo / "scaffold" / "not-a-real-corpus"
        fake_corpus.mkdir(exist_ok=True)
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as handle:
                handle.write("public fixture\n")
                public = Path(handle.name)
            try:
                with self.assertRaises(ValueError) as caught:
                    check(fake_corpus, [public])
                self.assertIn("CORPUS_INSIDE_REPOSITORY", str(caught.exception))
                proc = subprocess.run(
                    [sys.executable, str(LEAK_CHECK), str(fake_corpus), str(public)],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(proc.returncode, 2)
                self.assertIn("CORPUS_INSIDE_REPOSITORY", proc.stderr)
            finally:
                public.unlink()
        finally:
            fake_corpus.rmdir()

    def test_never_writes_into_the_corpus(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            corpus = _make_corpus(base / "corpus")
            public = base / "public.md"
            public.write_text(PLACEHOLDER_BODY + "\n", encoding="utf-8")
            before = {
                path.name: path.read_bytes()
                for path in corpus.rglob("*")
                if path.is_file()
            }
            subprocess.run(
                [sys.executable, str(LEAK_CHECK), str(corpus), str(public)],
                capture_output=True,
                text=True,
            )
            after = {
                path.name: path.read_bytes()
                for path in corpus.rglob("*")
                if path.is_file()
            }
            self.assertEqual(before, after)

    def test_absent_corpus_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            public = base / "public.md"
            public.write_text("fixture\n", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(LEAK_CHECK), str(base / "missing"), str(public)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("CORPUS_ABSENT", proc.stderr)
            self.assertFalse((base / "missing").exists())


if __name__ == "__main__":
    unittest.main()
