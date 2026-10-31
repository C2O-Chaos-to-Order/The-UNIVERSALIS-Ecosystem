"""Corpus probe: read outside the repository, never write into the corpus."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

PROBE = Path(__file__).resolve().parents[1] / "tools" / "corpus_probe.py"


def _tablet(number: int, side: str, clauses: list[tuple[int, str, str]]) -> str:
    lines = [f"# Tablet {number} {side.title()}", ""]
    for clause_number, title, body in clauses:
        lines.append(f"## Clause {clause_number}: {title}")
        lines.append("")
        lines.append(body)
        lines.append("")
    return "\n".join(lines)


class CorpusProbeTests(unittest.TestCase):
    def test_absent_directory_exits_nonzero_and_is_not_created(self):
        missing = Path(self.id().replace(".", "_"))
        # Use a path that does not exist under the system temp via the test's private path.
        target = Path("/tmp/universalis-corpus-absent-probe")
        if target.exists():
            raise AssertionError("test path already exists")
        proc = subprocess.run([sys.executable, str(PROBE), str(target)], capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("CORPUS_ABSENT", proc.stderr)
        self.assertIn(str(target), proc.stderr)
        self.assertFalse(target.exists())

    def test_index_digest_and_no_write_into_corpus(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "private-corpus"
            corpus.mkdir()
            technical = _tablet(
                0,
                "technical",
                [(1, "EXAMPLE PLACEHOLDER ALPHA", "placeholder body one")],
            )
            human = _tablet(
                0,
                "human",
                [(1, "EXAMPLE PLACEHOLDER BETA", "placeholder body two")],
            )
            (corpus / "tablet-0-technical.md").write_text(technical, encoding="utf-8")
            (corpus / "tablet-0-human.md").write_text(human, encoding="utf-8")
            before = {path.name: path.read_bytes() for path in corpus.iterdir()}
            output = Path(tmp) / "index.json"
            proc = subprocess.run(
                [sys.executable, str(PROBE), str(corpus), "--output", str(output)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            after = {path.name: path.read_bytes() for path in corpus.iterdir()}
            self.assertEqual(before, after)
            index = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(index["clause_count"], 2)
            self.assertEqual(index["clauses"][0]["tablet_number"], 0)
            self.assertEqual(index["clauses"][0]["clause_number"], 1)
            self.assertEqual(index["clauses"][0]["clause_title"], "EXAMPLE PLACEHOLDER ALPHA")
            self.assertEqual(index["clauses"][0]["character_count"], len("placeholder body one"))
            self.assertEqual(
                index["clauses"][0]["sha256"],
                hashlib.sha256(b"placeholder body one").hexdigest(),
            )
            again = subprocess.run(
                [sys.executable, str(PROBE), str(corpus), "--output", str(Path(tmp) / "index-again.json")],
                capture_output=True,
                text=True,
            )
            self.assertEqual(again.returncode, 0, again.stderr)
            self.assertEqual(
                index["corpus_digest"],
                json.loads((Path(tmp) / "index-again.json").read_text(encoding="utf-8"))["corpus_digest"],
            )

    def test_refuses_to_write_inside_the_corpus(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "private-corpus"
            corpus.mkdir()
            (corpus / "tablet-0-technical.md").write_text(
                _tablet(0, "technical", [(1, "EXAMPLE PLACEHOLDER", "placeholder body")]),
                encoding="utf-8",
            )
            before = sorted(path.name for path in corpus.iterdir())
            proc = subprocess.run(
                [sys.executable, str(PROBE), str(corpus), "--output", str(corpus / "index.json")],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("CORPUS_WRITE_REFUSED", proc.stderr)
            self.assertEqual(before, sorted(path.name for path in corpus.iterdir()))


if __name__ == "__main__":
    unittest.main()
