
import unittest
from pathlib import Path

from engineering_doctor.analysis import (
    extract_mentioned_paths,
    readme_drift_findings,
    status_claim_findings,
)


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


class ReadmeDriftTests(unittest.TestCase):
    def test_extracts_relative_paths_only(self) -> None:
        text = (
            "See [guide](docs/guide.md) and `src/app.py` plus "
            "[remote](https://example.example/x) and `Random words`."
        )
        paths = extract_mentioned_paths(text)
        self.assertIn("docs/guide.md", paths)
        self.assertIn("src/app.py", paths)
        self.assertNotIn("https://example.example/x", paths)

    def test_missing_path_is_a_finding(self) -> None:
        findings = readme_drift_findings(
            "example-public",
            "See `docs/missing.md` and `README.md`.",
            ["README.md", "prototype/x.py"],
        )
        missing = [item for item in findings if "docs/missing.md" in item.evidence]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0].severity, "Medium")

    def test_url_encoded_spaces_are_unquoted(self) -> None:
        findings = readme_drift_findings(
            "example-public",
            "See [guide](docs/My%20Guide.md).",
            ["docs/My Guide.md"],
        )
        self.assertEqual(findings, [])

    def test_existing_path_is_not_a_finding(self) -> None:
        findings = readme_drift_findings(
            "demo",
            "See `README.md`.",
            ["README.md"],
        )
        self.assertEqual(findings, [])

    def test_not_started_status_versus_prototype_tree(self) -> None:
        readme = "Status: Documentation foundation initialized; product implementation not yet started."
        findings = readme_drift_findings(
            "example-public",
            readme,
            ["README.md", "prototype/foo.py", "scaffold/bar.py"],
        )
        kinds = [item.title for item in findings]
        self.assertTrue(any("not yet started" in title for title in kinds))
        self.assertEqual(findings[-1].severity, "High")


class StatusClaimTests(unittest.TestCase):
    def test_exa001_draft_versus_ratified_is_a_fixture_finding(self) -> None:
        draft = (FIXTURE_DIR / "EXA-001_DRAFT.md").read_text(encoding="utf-8")
        other = (FIXTURE_DIR / "EXA-001_CALLED_RATIFIED.md").read_text(encoding="utf-8")
        findings = status_claim_findings(
            [
                (str(FIXTURE_DIR / "EXA-001_DRAFT.md"), draft),
                (str(FIXTURE_DIR / "EXA-001_CALLED_RATIFIED.md"), other),
            ]
        )
        matched = [item for item in findings if item.related == "EXA-001"]
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0].severity, "High")
        self.assertIn("Draft Candidate", matched[0].evidence)
        self.assertIn("Ratified", matched[0].evidence)

    def test_consistent_draft_statuses_do_not_conflict(self) -> None:
        findings = status_claim_findings(
            [
                ("a.md", "# EXB-002\n**Status:** Draft\n"),
                ("b.md", "EXB-002 Status: Draft; not adopted\n"),
            ]
        )
        self.assertEqual(findings, [])
