"""Empty programme instantiation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEW_PROGRAMME = ROOT / "tools" / "new_programme.py"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

from new_programme import instantiate
from support import run_validator


class NewProgrammeTests(unittest.TestCase):
    def test_placeholder_manifest_is_replaced_and_package_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "programme"
            journal = []
            instantiate(target, "EXAMPLE-PROGRAMME", "0.0.0", journal=journal)
            self.assertEqual(journal[0], {"_placeholder": "populate me"})
            manifest = json.loads((target / "metadata" / "sha256_manifest.json").read_text(encoding="utf-8"))
            self.assertNotIn("_placeholder", manifest)
            readme_hash = manifest["README.md"]
            self.assertEqual(len(readme_hash), 64)
            status = json.loads((target / "metadata" / "programme_status.json").read_text(encoding="utf-8"))
            self.assertEqual(status["programme"], "EXAMPLE-PROGRAMME")
            self.assertEqual(status["evidence_status"], "planned")
            self.assertEqual(status["authorization_status"], "NOT_AUTHORIZED")
            self.assertEqual(status["owner_acceptance"], "PENDING")
            self.assertEqual(status["research_records"], 0)
            self.assertEqual(status["owner_accepted_research_credits"], 0)
            code, payload, stderr = run_validator(target)
            self.assertEqual(code, 0, stderr)
            self.assertTrue(payload["ok"])
            self.assertIn("does not prove", payload["scope"])
            self.assertTrue(all(item["outcome"] == "PASS" for item in payload["checks"]))

    def test_cli_refuses_a_nonempty_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "programme"
            target.mkdir()
            (target / "README.md").write_text("already here\n", encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(NEW_PROGRAMME),
                    "--target",
                    str(target),
                    "--programme-id",
                    "EXAMPLE-PROGRAMME",
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("TARGET_NONEMPTY", proc.stderr)

    def test_report_template_has_the_ten_items_in_order(self):
        text = (ROOT / "templates" / "programme" / "reports" / "_TEMPLATE_report.md").read_text(encoding="utf-8")
        headings = [
            "## 1. Task and scope",
            "## 2. Source of truth",
            "## 3. Method",
            "## 4. Evidence",
            "## 5. Findings",
            "## 6. Execution status",
            "## 7. Build status",
            "## 8. Risk and governance",
            "## 9. Repository disposition",
            "## 10. Next action",
        ]
        cursor = 0
        for heading in headings:
            found = text.find(heading, cursor)
            self.assertGreaterEqual(found, 0, heading)
            cursor = found + len(heading)


if __name__ == "__main__":
    unittest.main()
