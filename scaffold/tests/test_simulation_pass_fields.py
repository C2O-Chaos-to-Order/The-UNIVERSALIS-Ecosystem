"""The four Plan simulation-pass fields and their constraints.

The Plan requires execution_timestamp, failure_policy, known_answer_check and
mcse_or_precision_note on every simulation pass. These tests mutate one field
at a time on an otherwise valid package and assert that validation fails for
that field's own reason.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

from package_files import rebuild_locks
from support import build_executed, run_validator


def _mutated(mutate) -> tuple[int, dict, str]:
    with tempfile.TemporaryDirectory() as tmp:
        package = build_executed(Path(tmp) / "programme")
        result_path = package / "results" / "SIM-001.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        mutate(result)
        result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        rebuild_locks(package)
        return run_validator(package)


def _execution_reasons(payload: dict) -> str:
    for check in payload["checks"]:
        if check["check"] == "execution_evidence":
            return "\n".join(check["reasons"])
    return ""


class SimulationPassFieldTests(unittest.TestCase):
    def test_baseline_package_carries_all_four_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = build_executed(Path(tmp) / "programme")
            result = json.loads(
                (package / "results" / "SIM-001.json").read_text(encoding="utf-8")
            )
            for field in (
                "execution_timestamp",
                "failure_policy",
                "known_answer_check",
                "mcse_or_precision_note",
            ):
                self.assertIn(field, result)
                self.assertTrue(result[field], f"{field} must be populated honestly")
            self.assertTrue(result["failure_policy"].strip())
            self.assertTrue(result["mcse_or_precision_note"].strip())
            self.assertEqual(
                set(result["known_answer_check"]), {"included", "case_id", "detail"}
            )

    def test_a_naive_execution_timestamp_is_refused(self):
        def mutate(result):
            result["execution_timestamp"] = result["execution_timestamp"].split("+")[0].rstrip("Z")

        code, payload, _ = _mutated(mutate)
        self.assertNotEqual(code, 0)
        self.assertIn(
            "SIM-001 execution_timestamp is missing, malformed, or has no explicit "
            "numeric offset or Z",
            _execution_reasons(payload),
        )

    def test_execution_timestamp_must_fall_inside_the_recorded_interval(self):
        def mutate(result):
            result["execution_timestamp"] = "2000-01-01T00:00:00+00:00"

        code, payload, _ = _mutated(mutate)
        self.assertNotEqual(code, 0)
        self.assertIn(
            "SIM-001 execution_timestamp falls outside the recorded "
            "started_at..ended_at interval",
            _execution_reasons(payload),
        )

    def test_a_blank_failure_policy_is_refused(self):
        def mutate(result):
            result["failure_policy"] = "   "

        code, payload, _ = _mutated(mutate)
        self.assertNotEqual(code, 0)
        self.assertIn(
            "SIM-001 failure_policy must state what is recorded on a crash or "
            "non-convergence",
            _execution_reasons(payload),
        )

    def test_an_absent_known_answer_case_must_explain_why(self):
        def mutate(result):
            result["known_answer_check"] = {
                "included": False,
                "case_id": None,
                "detail": "  ",
            }

        code, payload, _ = _mutated(mutate)
        self.assertNotEqual(code, 0)
        self.assertIn(
            "SIM-001 known_answer_check.detail must state why no known-answer or "
            "negative-control case applies",
            _execution_reasons(payload),
        )

    def test_an_included_known_answer_case_must_name_it(self):
        def mutate(result):
            result["known_answer_check"] = {
                "included": True,
                "case_id": "",
                "detail": "A known-answer case was included.",
            }

        code, payload, _ = _mutated(mutate)
        self.assertNotEqual(code, 0)
        self.assertIn(
            "SIM-001 known_answer_check.included is true but case_id is empty",
            _execution_reasons(payload),
        )

    def test_a_known_answer_case_id_must_be_null_when_not_included(self):
        def mutate(result):
            result["known_answer_check"] = {
                "included": False,
                "case_id": "KA-001",
                "detail": "No known-answer case applies to this fixture.",
            }

        code, payload, _ = _mutated(mutate)
        self.assertNotEqual(code, 0)
        self.assertIn(
            "SIM-001 known_answer_check.case_id must be null when included is false",
            _execution_reasons(payload),
        )

    def test_a_deterministic_model_must_say_so_in_the_precision_note(self):
        def mutate(result):
            result["mcse_or_precision_note"] = ""

        code, payload, _ = _mutated(mutate)
        self.assertNotEqual(code, 0)
        self.assertIn(
            "SIM-001 mcse_or_precision_note must be a non-empty string that says so "
            "explicitly when the model is deterministic or single-run",
            _execution_reasons(payload),
        )

    def test_started_at_and_ended_at_do_not_satisfy_execution_timestamp(self):
        """The extra execution detail does not replace the Plan field."""
        def mutate(result):
            result.pop("execution_timestamp")

        code, payload, _ = _mutated(mutate)
        self.assertNotEqual(code, 0)
        reasons = _execution_reasons(payload)
        self.assertIn("missing required field execution_timestamp", reasons)
        self.assertIn("execution_timestamp is missing, malformed", reasons)

        # The other timestamps survive in the runner's output, so the record is
        # not simply missing all time information: execution_timestamp is a
        # separate required field and the others do not stand in for it.
        runner = (
            ROOT / "templates" / "programme" / "simulations" / "run_one.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"started_at": started.isoformat()', runner)
        self.assertIn('"ended_at": ended.isoformat()', runner)
        self.assertIn('"execution_timestamp": started.isoformat()', runner)
        self.assertIn('"duration_seconds"', runner)


if __name__ == "__main__":
    unittest.main()
