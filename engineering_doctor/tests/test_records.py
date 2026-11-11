
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

VALID_SHA1 = "abc123def4567890abc123def4567890abc123de"
VALID_SHA256 = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


class RepoShaValidationTests(unittest.TestCase):
    def _valid_record(self, **overrides):
        started = datetime(2026, 11, 10, 20, 0, tzinfo=timezone.utc)
        payload = dict(
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
        payload.update(overrides)
        return build_record(**payload)

    def test_missing_repo_shas_field_is_rejected(self) -> None:
        record = self._valid_record()
        del record["repo_shas"]
        errors = validate_record(record)
        self.assertTrue(any("repo_shas" in item and "missing" in item for item in errors), errors)

    def test_empty_map_with_inventoried_repo_is_rejected(self) -> None:
        record = self._valid_record()
        record["inventory"] = [{"name": "example-public"}]
        errors = validate_record(record)
        self.assertTrue(
            any("empty" in item or "missing inventoried repository" in item for item in errors),
            errors,
        )

    def test_missing_inventoried_repo_is_rejected(self) -> None:
        record = self._valid_record(repo_shas={"other-public": VALID_SHA1})
        record["inventory"] = [{"name": "example-public"}]
        errors = validate_record(record)
        self.assertTrue(
            any("example-public" in item and "missing" in item for item in errors),
            errors,
        )

    def test_null_sha_is_rejected(self) -> None:
        record = self._valid_record()
        record["inventory"] = [{"name": "example-public"}]
        record["repo_shas"] = {"example-public": None}
        errors = validate_record(record)
        self.assertTrue(any("null" in item for item in errors), errors)

    def test_malformed_sha_is_rejected(self) -> None:
        record = self._valid_record()
        record["inventory"] = [{"name": "example-public"}]
        record["repo_shas"] = {"example-public": "not-a-sha"}
        errors = validate_record(record)
        self.assertTrue(any("hexadecimal" in item for item in errors), errors)
        record["repo_shas"] = {"example-public": "ABC123DEF4567890ABC123DEF4567890ABC123DE"}
        errors = validate_record(record)
        self.assertTrue(any("hexadecimal" in item for item in errors), errors)
        record["repo_shas"] = {"example-public": "abc123def4567890abc123def4567890abc123d"}
        errors = validate_record(record)
        self.assertTrue(any("hexadecimal" in item for item in errors), errors)

    def test_working_tree_string_is_rejected(self) -> None:
        record = self._valid_record()
        record["inventory"] = [{"name": "example-public"}]
        record["repo_shas"] = {"example-public": "working-tree"}
        errors = validate_record(record)
        self.assertTrue(any("working-tree" in item for item in errors), errors)
        record["repo_shas"] = {"example-public": "working_tree"}
        errors = validate_record(record)
        self.assertTrue(any("working-tree" in item for item in errors), errors)

    def test_valid_sha1_and_sha256_with_matching_inventory_are_accepted(self) -> None:
        record = self._valid_record(
            inventory=[{"name": "example-public"}],
            repo_shas={"example-public": VALID_SHA1},
        )
        self.assertEqual(validate_record(record), [])
        record["repo_shas"] = {"example-public": VALID_SHA256}
        self.assertEqual(validate_record(record), [])

    def test_unresolved_inventory_does_not_accept_null_or_working_tree(self) -> None:
        record = self._valid_record()
        record["inventory"] = [{"name": "example-public", "query_status": "UNKNOWN"}]
        record["unresolved_repo_shas"] = {
            "example-public": "default_sha was not resolved (query_status='UNKNOWN')"
        }
        self.assertEqual(validate_record(record), [])
        record["repo_shas"] = {"example-public": None}
        errors = validate_record(record)
        self.assertTrue(any("null" in item for item in errors), errors)
