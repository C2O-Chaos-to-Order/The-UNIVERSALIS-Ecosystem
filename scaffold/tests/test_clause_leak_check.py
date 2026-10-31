"""Clause leak check: synthetic placeholders only, never real clause text."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from clause_leak_check import check, longest_common_run, normalise

LEAK_CHECK = TOOLS / "clause_leak_check.py"

# A synthetic body. It is invented for this test and is not manuscript text.
PLACEHOLDER_BODY = (
    "PLACEHOLDER BODY ALPHA. This sentence exists only to give the overlap "
    "detector something long enough to match against a public fixture."
)


def _write_tablet(corpus: Path, body: str = PLACEHOLDER_BODY) -> None:
    corpus.mkdir(parents=True, exist_ok=True)
    (corpus / "tablet-0-technical.md").write_text(
        "# Tablet 0 Technical\n\n"
        "## Clause 1: PLACEHOLDER TITLE ALPHA\n\n"
        f"{body}\n",
        encoding="utf-8",
    )


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


class LeakCheckTests(unittest.TestCase):
    def test_short_overlap_passes_and_long_overlap_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            corpus = base / "private-corpus"
            _write_tablet(corpus)
            public_dir = base / "public"
            public_dir.mkdir()

            clean = public_dir / "clean.md"
            clean.write_text(
                "A corpus-agnostic note that shares only short formulaic runs.\n",
                encoding="utf-8",
            )
            passing = check(corpus, [clean], threshold=40)
            self.assertTrue(passing["ok"])
            self.assertEqual(passing["over_threshold"], [])
            self.assertLessEqual(passing["worst"]["length"], 40)

            leaky = public_dir / "leaky.md"
            leaky.write_text(
                "Here is a copied passage: " + PLACEHOLDER_BODY + "\n",
                encoding="utf-8",
            )
            failing = check(corpus, [leaky], threshold=40)
            self.assertFalse(failing["ok"])
            self.assertEqual(len(failing["over_threshold"]), 1)
            self.assertEqual(failing["over_threshold"][0]["clause"], "clause 1")
            self.assertGreater(failing["over_threshold"][0]["length"], 40)

    def test_threshold_is_configurable(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            corpus = base / "private-corpus"
            _write_tablet(corpus, body="SHORT PLACEHOLDER RUN HERE")
            public = base / "public.md"
            public.write_text("SHORT PLACEHOLDER RUN HERE\n", encoding="utf-8")
            self.assertTrue(check(corpus, [public], threshold=40)["ok"])
            self.assertFalse(check(corpus, [public], threshold=10)["ok"])

    def test_cli_exits_nonzero_above_threshold_and_zero_below(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            corpus = base / "private-corpus"
            _write_tablet(corpus)
            public = base / "public.md"
            public.write_text(PLACEHOLDER_BODY + "\n", encoding="utf-8")
            over = subprocess.run(
                [sys.executable, str(LEAK_CHECK), str(corpus), str(public)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(over.returncode, 1, over.stdout + over.stderr)
            self.assertIn("LEAK_SUSPECTED", over.stderr)

            under = subprocess.run(
                [sys.executable, str(LEAK_CHECK), str(corpus), str(public), "--threshold", "5000"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(under.returncode, 0, under.stdout + under.stderr)
            self.assertIn("no shared run exceeds the threshold", under.stdout)

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
            corpus = base / "private-corpus"
            _write_tablet(corpus)
            public = base / "public.md"
            public.write_text(PLACEHOLDER_BODY + "\n", encoding="utf-8")
            before = {path.name: path.read_bytes() for path in corpus.iterdir()}
            subprocess.run(
                [sys.executable, str(LEAK_CHECK), str(corpus), str(public)],
                capture_output=True,
                text=True,
            )
            after = {path.name: path.read_bytes() for path in corpus.iterdir()}
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
