
"""Automated leak test: hashed denylist against the public tree."""

from __future__ import annotations

import unittest
from pathlib import Path

from engineering_doctor.tests.leakscan import (
    candidates_from_text,
    digest,
    load_denylist,
    scan_text,
    scan_tree,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DENYLIST_PATH = Path(__file__).resolve().parent / "leak_denylist.sha256"


class LeakScanTests(unittest.TestCase):
    def test_denylist_contains_only_hex_digests(self) -> None:
        hashes = load_denylist(DENYLIST_PATH)
        self.assertGreaterEqual(len(hashes), 8)
        for item in hashes:
            self.assertRegex(item, r"^[0-9a-f]{64}$")

    def test_scanner_detects_an_injected_synthetic_phrase(self) -> None:
        phrase = "leaky-fixture-token-zzqx"
        hashed = digest(phrase)
        hits = scan_text(f"prefix {phrase} suffix", {hashed})
        self.assertEqual(hits, [hashed])
        self.assertIn(phrase, candidates_from_text(f"prefix {phrase} suffix"))

    def test_scanner_ignores_unrelated_text(self) -> None:
        phrase = "leaky-fixture-token-zzqx"
        hashed = digest(phrase)
        self.assertEqual(scan_text("completely unrelated public documentation", {hashed}), [])

    def test_public_tree_has_no_denied_phrases(self) -> None:
        """Scan Doctor files and other non-prototype/scaffold paths."""
        denylist = load_denylist(DENYLIST_PATH)
        findings = scan_tree(REPO_ROOT, denylist)
        if findings:
            summary = "; ".join(
                f"{path} matched {len(hits)} digest(s)" for path, hits in findings
            )
            self.fail(
                "Public tree matched one or more hashed denylist digests. "
                "The denylist stores only SHA-256 digests of normalized private "
                "phrases (repository names, collection names, corpus path "
                f"fragments, and internal classification words). Hits: {summary}"
            )
