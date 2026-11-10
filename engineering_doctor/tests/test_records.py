
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from engineering_doctor.constants import BANNER
from engineering_doctor.findings import Finding
from engineering_doctor.records import (
    allocate_run_dir,
    build_record,
    sha256_text,
    validate_record,
    verify_record_sidecar,
    write_record,
)


def _sample_finding() -> Finding:
    return Finding(
        finding_id="T-001",
        severity="Low",
        title="example",
        basis="Low because this is a test fixture.",
        evidence="n/a",
    )


class RecordTests(unittest.TestCase):
    def test_record_includes_banner_and_rejects_scores(self) -> None:
        started = datetime(2026, 11, 10, 20, 0, tzinfo=timezone.utc)
        record = build_record(
            run_id="test-run",
            started_at=started,
            finished_at=started,
            python_version="3.14.10",
            inputs={"tool_version": "0.1.0"},
            inventory=[],
            suites=[],
            findings=[_sample_finding()],
            limitations=["test"],
            repo_shas={},
        )
        self.assertEqual(record["banner"], BANNER)
        self.assertEqual(record["tool_status"], "LIMITED")
        self.assertEqual(record["classification"], "PUBLIC_CANDIDATE")
        self.assertNotIn("confidence", record)
        self.assertNotIn("readiness_percent", record)
        broken = dict(record)
        broken["confidence"] = 93
        errors = validate_record(broken)
        self.assertTrue(any("confidence" in item for item in errors))

    def test_tampered_inputs_hash_is_detected(self) -> None:
        started = datetime(2026, 11, 10, 20, 0, tzinfo=timezone.utc)
        record = build_record(
            run_id="test-run",
            started_at=started,
            finished_at=started,
            python_version="3.14.10",
            inputs={"a": 1},
            inventory=[],
            suites=[],
            findings=[_sample_finding()],
            limitations=["test"],
            repo_shas={},
        )
        record["inputs"] = {"a": 2}
        errors = validate_record(record)
        self.assertTrue(any("inputs_sha256" in item for item in errors))

    def test_writes_are_immutable(self) -> None:
        started = datetime(2026, 11, 10, 20, 0, tzinfo=timezone.utc)
        record = build_record(
            run_id="test-run",
            started_at=started,
            finished_at=started,
            python_version="3.14.10",
            inputs={"a": 1},
            inventory=[],
            suites=[],
            findings=[_sample_finding()],
            limitations=["test"],
            repo_shas={},
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "runs"
            run_id, run_dir = allocate_run_dir(output, started)
            paths = write_record(run_dir, record, "# brief\n")
            self.assertTrue(paths["record"].is_file())
            verify_record_sidecar(run_dir)
            with self.assertRaises(FileExistsError):
                write_record(run_dir, record, "# brief\n")
            payload = paths["record"].read_text(encoding="utf-8")
            paths["sha256"].write_text("0" * 64 + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                verify_record_sidecar(run_dir)
            self.assertEqual(sha256_text(payload), sha256_text(payload))

    def test_record_preserves_run_id_and_repo_shas(self) -> None:
        started = datetime(2026, 11, 10, 20, 0, tzinfo=timezone.utc)
        repo_shas = {"example-public": "abc123def4567890abc123def4567890abc123de"}
        record = build_record(
            run_id="test-run-exact",
            started_at=started,
            finished_at=started,
            python_version="3.14.10",
            inputs={"tool_version": "0.1.0"},
            inventory=[],
            suites=[],
            findings=[_sample_finding()],
            limitations=["test"],
            repo_shas=repo_shas,
        )
        self.assertEqual(record["run_id"], "test-run-exact")
        self.assertEqual(record["repo_shas"], repo_shas)
        self.assertRegex(record["inputs_sha256"], r"^[a-f0-9]{64}$")
        self.assertEqual(record["banner"], BANNER)
