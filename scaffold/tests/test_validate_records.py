"""Standalone record validation: one schema, one directory, no package.

``validate_programme.py`` validates a whole programme package. These tests
cover the narrower tool that validates a directory of record files on its own,
and they are written the way the rest of the suite is: every negative fixture
must fail for its own stated reason, and the assertion names the reason. A
fixture that fails for some other reason is a broken fixture, not a passing
test.

All field values here are synthetic placeholders. No record content is real.
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import validate_records as vrecords
from validate_records import (
    SCOPE,
    UNSPECIFIED,
    main,
    render_human,
    schema_file,
    schema_problems as validate_records_schema_problems,
    unspecified_paths,
    validate_directory,
)

TOOL = ROOT / "tools" / "validate_records.py"
SCHEMA = "simulation_result"


def _record(**overrides) -> dict:
    """A structurally conformant placeholder record.

    Every value is a synthetic placeholder. ``randomness`` is the one declared
    field left out, because it is the one optional field in the schema and a
    record without it must still pass.
    """
    record = {
        "record_id": "SIM-001",
        "programme_unit_id": "EXAMPLE-PROGRAMME",
        "pass_type": "executed_simulation",
        "checkpoint_id": "example-checkpoint",
        "objective_question": "example-question",
        "claim_class": "example-class",
        "relevant_dimensions": "example-dimension",
        "phase": "example-phase",
        "level": "example-level",
        "method_summary": "example-method",
        "sources_or_inputs": "example-input",
        "assumptions": "example-assumption",
        "acceptance_or_falsification_criteria": "example-criterion",
        "actual_conditions": "example-conditions",
        "outcome_summary": "example-outcome",
        "raw_evidence_location": "results/SIM-001.json",
        "uncertainty_and_limitations": "example-limitation",
        "review_note": "example-note",
        "evidence_status": "documented",
        "authorization_status": "NOT_AUTHORIZED",
        "regression_links": "example-link",
        "open_obligations": "example-obligation",
        "protocol_version": "EXAMPLE-PROTOCOL-1",
        "configuration": "value=1",
        "environment": {"python": "example-version", "platform": "example-platform"},
        "execution_timestamp": "2026-01-01T00:00:00+00:00",
        "failure_policy": "example-policy",
        "known_answer_check": {
            "included": False,
            "case_id": None,
            "detail": "example-detail",
        },
        "mcse_or_precision_note": "example-precision-note",
        "execution_outcome": "executed",
        "research_record_id": "RES-001",
        "input": {"value": 1},
        "expected": {"outcome": "RECORDED"},
        "actual": {"outcome": "RECORDED"},
        "expectation_matched": True,
        "execution_status": "COMPLETED",
        "outcome": "PASS",
        "error": None,
        "started_at": "2026-01-01T00:00:00+00:00",
        "ended_at": "2026-01-01T00:00:01+00:00",
        "duration_seconds": 1.0,
        "exit_code": 0,
        "code_path": "simulations/run_one.py",
        "code_sha256": "a" * 64,
        "fixtures_sha256": "b" * 64,
        "programme_credit": "NONE",
        "independent_review": "example-review-note",
        "release_classification": "PUBLICLY_CLEARED",
    }
    record.update(overrides)
    return record


def _write(directory: Path, name: str, payload) -> Path:
    path = directory / name
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _run(directory: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), str(directory), *extra],
        capture_output=True,
        text=True,
    )


def _kinds(report: dict) -> list[str]:
    return [problem["kind"] for problem in report["failures"]]


def _failure_for(report: dict, field: str) -> dict:
    matches = [item for item in report["failures"] if item["field"] == field]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one failure for {field!r}, got {matches}")
    return matches[0]


class ValidRecordTests(unittest.TestCase):
    def test_a_valid_record_passes_and_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record())
            report = validate_directory(directory, SCHEMA)
            self.assertTrue(report["ok"], report["failures"])
            self.assertEqual(report["records_checked"], 1)
            self.assertEqual(report["records_failed"], 0)
            self.assertEqual(report["failures"], [])
            self.assertIn("VERDICT: PASS", report["verdict"])
            proc = _run(directory)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("VERDICT: PASS", proc.stdout)

    def test_the_schema_reports_its_own_field_counts(self):
        """The counts come from the schema file, not from a number typed here."""
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record())
            report = validate_directory(directory, SCHEMA)
            schema = json.loads(
                (ROOT / "schemas" / "simulation_result.schema.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["required_fields"], len(schema["required"]))
            self.assertEqual(report["declared_fields"], len(schema["properties"]))
            # The fixture omits exactly the one optional field.
            self.assertEqual(
                set(schema["properties"]) - set(schema["required"]), {"randomness"}
            )

    def test_the_optional_field_may_be_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record(randomness="example-randomness"))
            report = validate_directory(directory, SCHEMA)
            self.assertTrue(report["ok"], report["failures"])

    def test_nested_declared_objects_are_checked_recursively(self):
        """``known_answer_check`` declares its own required fields."""
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(
                directory,
                "SIM-001.json",
                _record(known_answer_check={"included": False, "case_id": None}),
            )
            report = validate_directory(directory, SCHEMA)
            self.assertFalse(report["ok"])
            problem = _failure_for(report, "known_answer_check.detail")
            self.assertEqual(problem["kind"], "MISSING_REQUIRED")


class NestedValueTests(unittest.TestCase):
    """Declared nested objects are checked; unconstrained fields are not."""

    def test_a_nested_object_of_the_wrong_type_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(
                directory,
                "SIM-001.json",
                _record(known_answer_check="a string, not an object"),
            )
            report = validate_directory(directory, SCHEMA)
            self.assertFalse(report["ok"])
            problem = _failure_for(report, "known_answer_check")
            self.assertEqual(problem["kind"], "TYPE")
            self.assertIn("must be object, found string", problem["reason"])

    def test_an_unknown_field_inside_a_declared_object_is_reported_by_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(
                directory,
                "SIM-001.json",
                _record(environment={"python": "x", "platform": "y", "extra": "z"}),
            )
            report = validate_directory(directory, SCHEMA)
            self.assertFalse(report["ok"])
            problem = _failure_for(report, "environment.extra")
            self.assertEqual(problem["kind"], "UNKNOWN_FIELD")

    def test_a_field_the_schema_leaves_unconstrained_accepts_any_shape(self):
        """``input``, ``expected`` and ``actual`` declare no constraints.

        A schema that says nothing about a field's contents must not have
        contents invented for it by this tool.
        """
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            payload = {"anything": [1, 2, {"deep": True}], "other": None}
            _write(directory, "SIM-001.json", _record(input=payload))
            report = validate_directory(directory, SCHEMA)
            self.assertTrue(report["ok"], report["failures"])


class NegativeFixtureTests(unittest.TestCase):
    """Each fixture fails for its own stated reason and nothing else."""

    def test_a_missing_required_field_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            record = _record()
            del record["method_summary"]
            _write(directory, "SIM-001.json", record)
            report = validate_directory(directory, SCHEMA)
            self.assertFalse(report["ok"])
            self.assertEqual(_kinds(report), ["MISSING_REQUIRED"])
            problem = _failure_for(report, "method_summary")
            self.assertEqual(problem["reason"], "required field is missing")
            self.assertEqual(report["records_failed"], 1)
            self.assertIn("VERDICT: FAIL", report["verdict"])
            proc = _run(directory)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("FAIL MISSING_REQUIRED method_summary", proc.stdout)

    def test_an_unknown_extra_field_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record(reviewer_comment="not in the schema"))
            report = validate_directory(directory, SCHEMA)
            self.assertFalse(report["ok"])
            self.assertEqual(_kinds(report), ["UNKNOWN_FIELD"])
            problem = _failure_for(report, "reviewer_comment")
            self.assertIn("not declared by the schema", problem["reason"])
            proc = _run(directory)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("FAIL UNKNOWN_FIELD reviewer_comment", proc.stdout)

    def test_an_enum_violation_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record(evidence_status="approved"))
            report = validate_directory(directory, SCHEMA)
            self.assertFalse(report["ok"])
            self.assertEqual(_kinds(report), ["ENUM"])
            problem = _failure_for(report, "evidence_status")
            self.assertIn('"approved"', problem["reason"])
            self.assertIn("not one of the 8 permitted values", problem["reason"])
            proc = _run(directory)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("FAIL ENUM evidence_status", proc.stdout)

    def test_a_const_violation_fails(self):
        """``pass_type`` is a constant, checked on the same axis as an enum."""
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record(pass_type="research"))
            report = validate_directory(directory, SCHEMA)
            self.assertFalse(report["ok"])
            self.assertEqual(_kinds(report), ["CONST"])
            problem = _failure_for(report, "pass_type")
            self.assertIn("executed_simulation", problem["reason"])

    def test_a_wrong_type_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record(expectation_matched="yes"))
            report = validate_directory(directory, SCHEMA)
            self.assertFalse(report["ok"])
            self.assertEqual(_kinds(report), ["TYPE"])
            problem = _failure_for(report, "expectation_matched")
            self.assertIn("must be boolean", problem["reason"])
            self.assertIn("found string", problem["reason"])
            proc = _run(directory)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("FAIL TYPE expectation_matched", proc.stdout)

    def test_a_float_does_not_satisfy_an_integer(self):
        """``exit_code`` is an integer. ``1.5`` and ``true`` are both refused."""
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record(exit_code=1.5))
            report = validate_directory(directory, SCHEMA)
            self.assertFalse(report["ok"])
            problem = _failure_for(report, "exit_code")
            self.assertEqual(problem["kind"], "TYPE")
            self.assertIn("must be integer", problem["reason"])
            self.assertIn("found number", problem["reason"])

            _write(directory, "SIM-001.json", _record(exit_code=True))
            report = validate_directory(directory, SCHEMA)
            self.assertFalse(report["ok"])
            problem = _failure_for(report, "exit_code")
            self.assertIn("found boolean", problem["reason"])

    def test_an_integer_satisfies_a_declared_number(self):
        """``duration_seconds`` is a number, and an int is a number."""
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record(duration_seconds=2))
            report = validate_directory(directory, SCHEMA)
            self.assertTrue(report["ok"], report["failures"])

    def test_malformed_json_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "broken.json", '{"record_id": "SIM-001",\n')
            report = validate_directory(directory, SCHEMA)
            self.assertFalse(report["ok"])
            self.assertEqual(_kinds(report), ["NOT_JSON"])
            problem = _failure_for(report, "(record)")
            self.assertIn("not valid JSON", problem["reason"])
            self.assertIn("line 2", problem["reason"])
            self.assertEqual(report["records_failed"], 1)
            proc = _run(directory)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("FAIL NOT_JSON", proc.stdout)

    def test_a_json_value_that_is_not_an_object_fails(self):
        """A top-level array parses as JSON but is not a record."""
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "list.json", [{"record_id": "SIM-001"}])
            report = validate_directory(directory, SCHEMA)
            self.assertFalse(report["ok"])
            self.assertEqual(_kinds(report), ["NOT_OBJECT"])
            problem = _failure_for(report, "(record)")
            self.assertIn("must be a JSON object, found array", problem["reason"])

    def test_each_broken_record_is_counted_and_named(self):
        """A mixed directory reports every broken file, not just the first."""
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "a-valid.json", _record())
            missing = _record()
            del missing["review_note"]
            _write(directory, "b-missing.json", missing)
            _write(directory, "c-unknown.json", _record(extra_field="x"))
            _write(directory, "d-enum.json", _record(execution_outcome="finished"))
            _write(directory, "e-type.json", _record(execution_status=7))
            _write(directory, "f-broken.json", "{")
            report = validate_directory(directory, SCHEMA)
            self.assertEqual(report["records_checked"], 6)
            self.assertEqual(report["records_failed"], 5)
            self.assertEqual(
                sorted({item["file"] for item in report["failures"]}),
                [
                    "b-missing.json",
                    "c-unknown.json",
                    "d-enum.json",
                    "e-type.json",
                    "f-broken.json",
                ],
            )
            self.assertNotIn("a-valid.json", {item["file"] for item in report["failures"]})
            proc = _run(directory)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("records checked: 6 file(s)", proc.stdout)


class UnspecifiedTests(unittest.TestCase):
    """``UNSPECIFIED`` is a declared absence, not an invented value."""

    def test_unspecified_passes_but_is_reported_as_a_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(
                directory,
                "SIM-001.json",
                _record(
                    review_note=UNSPECIFIED,
                    regression_links=UNSPECIFIED,
                    open_obligations=UNSPECIFIED,
                ),
            )
            report = validate_directory(directory, SCHEMA)
            self.assertTrue(report["ok"], report["failures"])
            self.assertEqual(report["failures"], [])
            self.assertEqual(
                [item["field"] for item in report["warnings"]],
                ["open_obligations", "regression_links", "review_note"],
            )
            self.assertEqual(
                report["unspecified_counts"],
                {"open_obligations": 1, "regression_links": 1, "review_note": 1},
            )
            self.assertIn("3 unspecified warning(s)", report["verdict"])
            # Warnings alone still exit zero: nothing is structurally broken.
            proc = _run(directory)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("UNSPECIFIED values — warnings, not failures", proc.stdout)
            self.assertNotIn("FAIL", proc.stdout)

    def test_unspecified_counts_records_per_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record(review_note=UNSPECIFIED))
            _write(directory, "SIM-002.json", _record(record_id="SIM-002", review_note=UNSPECIFIED))
            _write(directory, "SIM-003.json", _record(record_id="SIM-003"))
            report = validate_directory(directory, SCHEMA)
            self.assertTrue(report["ok"], report["failures"])
            self.assertEqual(report["unspecified_counts"], {"review_note": 2})
            self.assertEqual(len(report["warnings"]), 2)

    def test_unspecified_is_refused_where_the_schema_enumerates_the_field(self):
        """The schema's vocabulary governs. This tool never widens it.

        ``evidence_status`` declares eight values and ``UNSPECIFIED`` is not
        one of them, so the record fails rather than warning. A record may
        decline to state a free-text value; it may not invent a ninth
        evidence state.
        """
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(
                directory,
                "SIM-001.json",
                _record(evidence_status=UNSPECIFIED, review_note=UNSPECIFIED),
            )
            report = validate_directory(directory, SCHEMA)
            self.assertFalse(report["ok"])
            problem = _failure_for(report, "evidence_status")
            self.assertEqual(problem["kind"], "ENUM")
            # The free-text field still warns, and the enumerated one is not
            # counted twice as both a failure and a warning.
            self.assertEqual([item["field"] for item in report["warnings"]], ["review_note"])
            self.assertEqual(report["unspecified_counts"], {"review_note": 1})

    def test_two_unspecified_sub_fields_in_one_record_count_once(self):
        """The count is records per field, not sentinel occurrences.

        ``known_answer_check`` holds two string sub-fields. A record that
        leaves both unspecified is one record with an unspecified
        ``known_answer_check``, not two.
        """
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(
                directory,
                "SIM-001.json",
                _record(
                    known_answer_check={
                        "included": False,
                        "case_id": UNSPECIFIED,
                        "detail": UNSPECIFIED,
                    }
                ),
            )
            report = validate_directory(directory, SCHEMA)
            self.assertTrue(report["ok"], report["failures"])
            self.assertEqual(report["unspecified_counts"], {"known_answer_check": 1})
            self.assertEqual(len(report["warnings"]), 2)

    def test_unspecified_detection_reaches_into_nested_values(self):
        found = unspecified_paths(
            {"a": UNSPECIFIED, "b": [{"c": UNSPECIFIED}], "d": "SPECIFIED"}
        )
        self.assertEqual(found, ["a", "b[0].c"])


class EmptyDirectoryTests(unittest.TestCase):
    """An empty directory is an error, not a pass.

    A gate that found nothing to check has cleared nothing. If an empty
    directory passed, a mistyped path or an empty checkout would read as a
    green light, which is the one failure mode this tool must not have. The
    tool exits 2, the same code ``validate_programme.py`` uses for a package
    directory that does not exist, so "nothing was checked" is never confused
    with "everything checked out".
    """

    def test_an_empty_directory_fails_with_code_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            proc = _run(directory)
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("NO_RECORDS", proc.stderr)
            self.assertIn("no *.json files found", proc.stderr)
            self.assertEqual(proc.stdout, "")

    def test_an_empty_directory_raises_rather_than_returning_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            with self.assertRaises(ValueError) as caught:
                validate_directory(directory, SCHEMA)
            self.assertIn("NO_RECORDS", str(caught.exception))

    def test_a_directory_of_only_other_suffixes_is_treated_as_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            (directory / "notes.md").write_text("not a record\n", encoding="utf-8")
            (directory / "data.txt").write_text("{}\n", encoding="utf-8")
            proc = _run(directory)
            self.assertEqual(proc.returncode, 2)
            self.assertIn("NO_RECORDS", proc.stderr)

    def test_an_absent_directory_fails_with_code_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = _run(Path(tmp) / "absent")
            self.assertEqual(proc.returncode, 2)
            self.assertIn("DIRECTORY_ABSENT", proc.stderr)


class SchemaSelectionTests(unittest.TestCase):
    def test_the_default_schema_is_the_simulation_result_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record())
            report = validate_directory(directory, SCHEMA)
            self.assertEqual(report["schema"], "simulation_result.schema.json")

    def test_the_short_name_and_the_file_name_select_the_same_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record())
            for name in ("simulation_result", "simulation_result.schema", "simulation_result.schema.json"):
                self.assertEqual(schema_file(name).name, "simulation_result.schema.json")

    def test_another_schema_can_be_selected(self):
        """The tool is not tied to one schema file."""
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            # A simulation result is not a research record: the schema is
            # selected by name, so the same file now fails.
            _write(directory, "SIM-001.json", _record())
            proc = _run(directory, "--schema", "research_record")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("FAIL CONST pass_type", proc.stdout)

    def test_a_schema_name_cannot_escape_the_schema_directory(self):
        for name in ("../simulation_result", "../../etc/passwd", "a/b", ".."):
            with self.assertRaises(ValueError) as caught:
                schema_file(name)
            self.assertIn("SCHEMA_NAME_INVALID", str(caught.exception))

    def test_an_unknown_schema_is_refused_by_name(self):
        with self.assertRaises(ValueError) as caught:
            schema_file("no_such_schema")
        self.assertIn("SCHEMA_ABSENT", str(caught.exception))
        self.assertIn("simulation_result", str(caught.exception))


class OutputTests(unittest.TestCase):
    def test_json_output_is_machine_readable_and_carries_the_same_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record(evidence_status="approved"))
            proc = _run(directory, "--json")
            self.assertEqual(proc.returncode, 1)
            payload = json.loads(proc.stdout)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["scope"], SCOPE)
            self.assertEqual(payload["records_checked"], 1)
            self.assertEqual(payload["records_failed"], 1)
            self.assertEqual(payload["failures"][0]["kind"], "ENUM")
            self.assertEqual(payload["failures"][0]["field"], "evidence_status")
            self.assertEqual(payload["failures"][0]["file"], "SIM-001.json")
            self.assertIn("VERDICT: FAIL", payload["verdict"])

    def test_the_scope_statement_denies_more_than_it_proves(self):
        """A pass is structural only, and the report says so.

        The old assertion checked for the words "pattern, minLength and minimum
        constraints are not applied here", which is now false: they are applied.
        It is replaced rather than deleted, so the denial cannot quietly widen
        while the test still passes.
        """
        for phrase in (
            "does not prove",
            "was conducted",
            "Unsupported schema keywords stop the run",
        ):
            self.assertIn(phrase, SCOPE)

    def test_the_human_report_names_the_file_and_the_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record(outcome="APPROVED"))
            proc = _run(directory)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("SIM-001.json", proc.stdout)
            self.assertIn("FAIL ENUM outcome", proc.stdout)

    def test_the_verdict_line_is_last(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record())
            proc = _run(directory)
            lines = [line for line in proc.stdout.splitlines() if line.strip()]
            self.assertTrue(lines[-1].startswith("VERDICT:"), lines[-1])


class DirectoryScopeTests(unittest.TestCase):
    def test_subdirectories_are_skipped_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            (directory / "nested").mkdir(parents=True)
            _write(directory, "SIM-001.json", _record())
            _write(directory / "nested", "SIM-002.json", _record(evidence_status="approved"))
            report = validate_directory(directory, SCHEMA)
            self.assertTrue(report["ok"], report["failures"])
            self.assertEqual(report["records_checked"], 1)

    def test_the_recursive_flag_reaches_subdirectories(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            (directory / "nested").mkdir(parents=True)
            _write(directory, "SIM-001.json", _record())
            _write(directory / "nested", "SIM-002.json", _record(evidence_status="approved"))
            proc = _run(directory, "--recursive")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("records checked: 2 file(s)", proc.stdout)
            self.assertIn("SIM-002.json", proc.stdout)


class RecursiveLabelTests(unittest.TestCase):
    def test_two_files_of_the_same_name_stay_distinguishable(self):
        """Recursive mode reports a path relative to the directory asked about.

        Two subdirectories each holding ``rec.json`` would otherwise produce
        the same label twice, and a reader could not tell which file failed.
        """
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            (directory / "a").mkdir(parents=True)
            (directory / "b").mkdir(parents=True)
            _write(directory / "a", "rec.json", _record())
            _write(directory / "b", "rec.json", _record(evidence_status="approved"))
            report = validate_directory(directory, SCHEMA, recursive=True)
            self.assertFalse(report["ok"])
            self.assertEqual([item["file"] for item in report["failures"]], ["b/rec.json"])

    def test_a_top_level_file_is_labelled_by_its_own_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record(evidence_status="approved"))
            report = validate_directory(directory, SCHEMA)
            self.assertEqual(report["failures"][0]["file"], "SIM-001.json")


class StdlibOnlyTests(unittest.TestCase):
    def test_the_tool_imports_only_the_standard_library_and_siblings(self):
        """The scaffold depends on the standard library alone."""
        module = ast.parse(TOOL.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(module):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                imported.add(node.module.split(".")[0])
        siblings = {
            path.stem for path in (ROOT / "tools").glob("*.py")
        }
        external = {
            name
            for name in imported
            if name not in sys.stdlib_module_names and name not in siblings
        }
        self.assertEqual(external, set(), f"non-stdlib imports: {sorted(external)}")

    def test_the_tool_reuses_the_package_validator_rather_than_redefining_it(self):
        """Type semantics and schema loading are imported, not copied."""
        source = TOOL.read_text(encoding="utf-8")
        self.assertIn("from validate_programme import", source)
        self.assertNotIn("def matches_type", source)
        self.assertNotIn("def load_schema", source)


def _quiet_main(argv: list[str]) -> int:
    """Call ``main`` without letting the report reach the test runner's output."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return main(argv)


class ExitCodeTests(unittest.TestCase):
    def test_main_returns_zero_for_a_clean_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record())
            self.assertEqual(_quiet_main([str(directory)]), 0)

    def test_main_returns_one_when_a_record_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record(evidence_status="approved"))
            self.assertEqual(_quiet_main([str(directory)]), 1)

    def test_main_returns_two_when_the_run_cannot_be_performed(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(_quiet_main([str(Path(tmp) / "absent")]), 2)
            empty = Path(tmp) / "empty"
            empty.mkdir()
            self.assertEqual(_quiet_main([str(empty)]), 2)


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# Constraint semantics.
#
# Each supported keyword gets a positive case, a negative case, and its
# boundary. The boundary cases are the ones that matter: a minimum of 0 must
# accept 0 and reject -1; a minLength of 1 must accept a one-character string
# and reject the empty one. A test that only checks the negative side would
# pass even if the constraint rejected everything.
# ---------------------------------------------------------------------------

class ConstraintSemanticsTests(unittest.TestCase):
    """JSON Schema constraint semantics, one keyword at a time."""

    def _fails_for(self, record: dict, kind: str, field: str) -> dict:
        """Validate one record and assert it fails for this kind on this field."""
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", record)
            report = validate_directory(directory, SCHEMA)
        self.assertFalse(report["ok"], f"expected a failure for {kind} on {field}")
        hits = [f for f in report["failures"] if f["kind"] == kind and f["field"] == field]
        self.assertTrue(
            hits,
            f"expected {kind} on {field}; got "
            + ", ".join(f"{f['kind']} {f['field']}" for f in report["failures"]),
        )
        return report

    def _passes(self, record: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", record)
            report = validate_directory(directory, SCHEMA)
        self.assertTrue(
            report["ok"],
            "expected a pass; got "
            + ", ".join(f"{f['kind']} {f['field']}" for f in report["failures"]),
        )
        return report

    # -- pattern -----------------------------------------------------------

    def test_pattern_accepts_a_conforming_id(self):
        self._passes(_record(record_id="SIM-001"))

    def test_pattern_accepts_a_longer_id(self):
        """``{3,}`` means three or more digits, so four must pass."""
        self._passes(_record(record_id="SIM-1234"))

    def test_pattern_rejects_too_few_digits(self):
        self._fails_for(_record(record_id="SIM-01"), "PATTERN", "record_id")

    def test_pattern_rejects_a_non_numeric_suffix(self):
        self._fails_for(_record(record_id="SIM-001x"), "PATTERN", "record_id")

    def test_pattern_is_a_substring_match_not_a_whole_string_match(self):
        """The specification says ``pattern`` searches, it does not anchor.

        ``record_id`` uses ``^...$`` so it is anchored either way. The
        timestamp pattern does not anchor its ends beyond its own groups, so a
        correct implementation must not add anchoring of its own. This asserts
        the primitive directly.
        """
        from validate_records import schema_problems

        node = {"type": "string", "pattern": "b"}
        self.assertEqual(schema_problems("abc", node, "f"), [])
        self.assertTrue(schema_problems("ac", node, "f"))

    def test_sha256_pattern_rejects_a_short_hash(self):
        self._fails_for(_record(code_sha256="a" * 63), "PATTERN", "code_sha256")

    def test_sha256_pattern_accepts_exactly_64(self):
        self._passes(_record(code_sha256="a" * 64))

    def test_sha256_pattern_rejects_uppercase_hex(self):
        """The pattern is ``[0-9a-f]``, so uppercase is not conformant."""
        self._fails_for(_record(code_sha256="A" * 64), "PATTERN", "code_sha256")

    # -- minLength ---------------------------------------------------------

    def test_minLength_one_rejects_the_empty_string(self):
        self._fails_for(_record(objective_question=""), "MIN_LENGTH", "objective_question")

    def test_minLength_one_accepts_a_single_character(self):
        """The boundary: length 1 satisfies ``minLength: 1``."""
        self._passes(_record(objective_question="q"))

    def test_minLength_counts_characters_not_bytes(self):
        """A one-character non-ASCII string has length 1, though several bytes."""
        self._passes(_record(objective_question="\u03a9"))

    def test_minLength_boundary_at_the_limit_passes(self):
        """``minLength: 1`` and a length of exactly 1: on the limit, must pass."""
        from validate_records import schema_problems

        node = {"type": "string", "minLength": 1}
        self.assertEqual(schema_problems("a", node, "f"), [])

    def test_minLength_boundary_one_under_the_limit_fails(self):
        from validate_records import schema_problems

        node = {"type": "string", "minLength": 1}
        problems = schema_problems("", node, "f")
        self.assertEqual([p["kind"] for p in problems], ["MIN_LENGTH"])

    # -- minimum -----------------------------------------------------------

    def test_minimum_zero_accepts_zero(self):
        """The boundary: 0 satisfies ``minimum: 0``."""
        self._passes(_record(programme_unit_id="EXAMPLE-PROGRAMME", input={"n": 0}))

    def test_minimum_zero_rejects_a_negative(self):
        self._fails_for(
            _record(duration_seconds=-0.001), "MINIMUM", "duration_seconds"
        )

    def test_minimum_accepts_a_positive(self):
        self._passes(_record(duration_seconds=0.001))

    def test_a_negative_exit_code_is_permitted_because_the_schema_sets_no_minimum(self):
        """A POSIX signal death reports a negative exit code.

        The schema declares ``type: integer`` for ``exit_code`` and no
        ``minimum``, so the validator must not invent one. This fixture exists
        because an earlier draft of these tests wrongly expected a failure here.
        """
        self._passes(_record(exit_code=-9))

    def test_duration_minimum_rejects_a_negative(self):
        self._fails_for(
            _record(duration_seconds=-0.5), "MINIMUM", "duration_seconds"
        )

    def test_duration_minimum_accepts_zero_float(self):
        self._passes(_record(duration_seconds=0.0))

    def test_minimum_boundary_at_the_limit_passes(self):
        """``minimum: 10`` and a value of exactly 10: on the limit, must pass."""
        from validate_records import schema_problems

        node = {"type": "number", "minimum": 10}
        self.assertEqual(schema_problems(10, node, "f"), [])

    def test_minimum_boundary_one_under_the_limit_fails(self):
        from validate_records import schema_problems

        node = {"type": "number", "minimum": 10}
        problems = schema_problems(9.999, node, "f")
        self.assertEqual([p["kind"] for p in problems], ["MINIMUM"])

    # -- maximum -----------------------------------------------------------
    #
    # No scaffold schema sets ``maximum``, so these fixtures drive the keyword
    # directly through ``schema_problems``. Testing it only through a schema
    # that does not use it would prove nothing.

    def test_maximum_boundary_at_the_limit_passes(self):
        """``maximum: 10`` and a value of exactly 10: on the limit, must pass."""
        from validate_records import schema_problems

        node = {"type": "number", "maximum": 10}
        self.assertEqual(schema_problems(10, node, "f"), [])

    def test_maximum_boundary_one_over_the_limit_fails(self):
        from validate_records import schema_problems

        node = {"type": "number", "maximum": 10}
        problems = schema_problems(10.001, node, "f")
        self.assertEqual([p["kind"] for p in problems], ["MAXIMUM"])

    def test_maximum_accepts_a_value_well_inside_the_limit(self):
        from validate_records import schema_problems

        node = {"type": "number", "maximum": 10}
        self.assertEqual(schema_problems(-5, node, "f"), [])
        self.assertEqual(schema_problems(0, node, "f"), [])

    def test_maximum_works_on_an_integer_bound_and_an_integer_value(self):
        from validate_records import schema_problems

        node = {"type": "integer", "maximum": 3}
        self.assertEqual(schema_problems(3, node, "f"), [])
        problems = schema_problems(4, node, "f")
        self.assertEqual([p["kind"] for p in problems], ["MAXIMUM"])

    def test_maximum_does_not_treat_a_boolean_as_a_number(self):
        """``True`` is an ``int`` in Python. ``maximum`` must not read it as 1.

        The bound here is 0, not 10, on purpose: ``True == 1`` and ``1 > 0``,
        so a validator that compared the boolean to the bound would report a
        ``MAXIMUM`` problem that the schema never asked for. With a bound of 10
        the same bug would be invisible, and an earlier version of this test
        used 10 and therefore could not fail.
        """
        from validate_records import schema_problems

        self.assertEqual(schema_problems(True, {"maximum": 0}, "f"), [])
        self.assertEqual(schema_problems(False, {"maximum": 0}, "f"), [])
        self.assertEqual(schema_problems(True, {"minimum": 5}, "f"), [])
        problems = schema_problems(True, {"type": "number", "maximum": 0}, "f")
        self.assertEqual([p["kind"] for p in problems], ["TYPE"])

    def test_maximum_is_ignored_for_a_non_numeric_value(self):
        """A bound applies to numbers only, as the specification requires."""
        from validate_records import schema_problems

        for value in ("not a number", None, [1], {"a": 1}, False):
            with self.subTest(value=value):
                self.assertEqual(schema_problems(value, {"maximum": 10}, "f"), [])

    # -- maxLength ---------------------------------------------------------
    #
    # ``clause_reference`` sets ``maxLength: 240`` on ``note``, so the keyword
    # is driven both directly and through a real schema file.

    def test_maxLength_boundary_at_the_limit_passes(self):
        """A string of exactly the limit satisfies ``maxLength``."""
        from validate_records import schema_problems

        node = {"type": "string", "maxLength": 5}
        self.assertEqual(schema_problems("abcde", node, "f"), [])

    def test_maxLength_boundary_one_over_the_limit_fails(self):
        from validate_records import schema_problems

        node = {"type": "string", "maxLength": 5}
        problems = schema_problems("abcdef", node, "f")
        self.assertEqual([p["kind"] for p in problems], ["MAX_LENGTH"])
        self.assertIn("at most 5 character(s)", problems[0]["reason"])
        self.assertIn("found 6", problems[0]["reason"])

    def test_maxLength_accepts_a_short_and_an_empty_string(self):
        from validate_records import schema_problems

        node = {"type": "string", "maxLength": 5}
        self.assertEqual(schema_problems("a", node, "f"), [])
        self.assertEqual(schema_problems("", node, "f"), [])

    def test_maxLength_zero_permits_only_the_empty_string(self):
        """The tightest boundary: ``maxLength: 0`` rejects a single character."""
        from validate_records import schema_problems

        node = {"type": "string", "maxLength": 0}
        self.assertEqual(schema_problems("", node, "f"), [])
        self.assertEqual(
            [p["kind"] for p in schema_problems("a", node, "f")], ["MAX_LENGTH"]
        )

    def test_maxLength_counts_characters_not_bytes(self):
        """A three-character non-ASCII string has length 3, though nine bytes."""
        from validate_records import schema_problems

        node = {"type": "string", "maxLength": 3}
        self.assertEqual(schema_problems("\u03a9\u03a9\u03a9", node, "f"), [])

    def test_maxLength_is_ignored_for_a_non_string_value(self):
        """A length bound applies to strings only, as the specification requires."""
        from validate_records import schema_problems

        for value in (123456789, None, [1, 2, 3], {"a": 1}, True):
            with self.subTest(value=value):
                self.assertEqual(schema_problems(value, {"maxLength": 1}, "f"), [])

    def test_maxLength_against_a_boolean_is_not_a_length_check(self):
        """``True`` has no length. The bound must not be applied to it."""
        from validate_records import schema_problems

        self.assertEqual(schema_problems(True, {"maxLength": 0}, "f"), [])

    def test_maxLength_through_the_clause_reference_schema(self):
        """The one real schema that uses ``maxLength``: ``note``, limit 240."""
        long_note = "n" * 241
        at_limit = "n" * 240
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()

            _write(
                directory,
                "at-limit.json",
                {
                    "clause_id": "01.E05",
                    "release_classification": "PUBLICLY_CLEARED",
                    "note": at_limit,
                },
            )
            report = validate_directory(directory, "clause_reference")
            self.assertTrue(report["ok"], report["failures"])

            _write(
                directory,
                "over-limit.json",
                {
                    "clause_id": "01.E05",
                    "release_classification": "PUBLICLY_CLEARED",
                    "note": long_note,
                },
            )
            report = validate_directory(directory, "clause_reference")
            self.assertFalse(report["ok"])
            problem = _failure_for(report, "note")
            self.assertEqual(problem["kind"], "MAX_LENGTH")
            self.assertIn("at most 240", problem["reason"])

    # -- type --------------------------------------------------------------

    def test_a_boolean_does_not_satisfy_an_integer(self):
        """``True`` is an ``int`` in Python; in JSON it is not an integer."""
        self._fails_for(_record(exit_code=True), "TYPE", "exit_code")

    def test_a_float_does_not_satisfy_an_integer(self):
        self._fails_for(_record(exit_code=1.0), "TYPE", "exit_code")

    def test_an_integer_satisfies_a_declared_number(self):
        self._passes(_record(duration_seconds=2))

    def test_a_string_does_not_satisfy_a_number(self):
        self._fails_for(_record(duration_seconds="1.0"), "TYPE", "duration_seconds")

    def test_an_integer_does_not_satisfy_a_boolean(self):
        self._fails_for(_record(expectation_matched=1), "TYPE", "expectation_matched")

    def test_null_satisfies_a_declared_nullable_field(self):
        self._passes(_record(error=None))

    # -- enum and const: type-aware comparison -----------------------------

    def test_enum_comparison_is_type_aware(self):
        """An integer must not match a string enum value by coercion."""
        from validate_records import matches_any_json

        self.assertFalse(matches_any_json(1, ["1", "2"]))
        self.assertTrue(matches_any_json("1", ["1", "2"]))

    def test_const_comparison_is_type_aware(self):
        from validate_records import json_equal

        self.assertFalse(json_equal(True, 1))
        self.assertFalse(json_equal(1, "1"))
        self.assertTrue(json_equal("PUBLICLY_CLEARED", "PUBLICLY_CLEARED"))

    def test_const_comparison_treats_an_integral_float_as_equal_to_an_integer(self):
        """JSON Schema says 1.0 and 1 are the same number, unlike 1 and true."""
        from validate_records import json_equal

        self.assertTrue(json_equal(1.0, 1))

    # -- json_equal: the full contract ------------------------------------
    #
    # The module docstring previously said ``1`` does not equal ``1.0`` while
    # the code and one test said it does. The prose is now corrected, and these
    # fixtures pin the real behaviour so the two cannot drift apart again.

    def test_json_equal_treats_one_and_one_point_zero_as_the_same_number(self):
        from validate_records import json_equal

        self.assertTrue(json_equal(1.0, 1))
        self.assertTrue(json_equal(1, 1.0))
        self.assertTrue(json_equal(2.0, 2))
        self.assertTrue(json_equal(0.0, 0))

    def test_json_equal_treats_equal_non_integral_floats_as_equal(self):
        from validate_records import json_equal

        self.assertTrue(json_equal(2.5, 2.5))
        self.assertFalse(json_equal(2.5, 2.6))

    def test_json_equal_distinguishes_a_boolean_from_a_number(self):
        """``True == 1`` and ``False == 0`` in Python. In JSON they differ."""
        from validate_records import json_equal

        self.assertFalse(json_equal(True, 1))
        self.assertFalse(json_equal(1, True))
        self.assertFalse(json_equal(False, 0))
        self.assertFalse(json_equal(0, False))
        self.assertFalse(json_equal(False, 0.0))
        self.assertFalse(json_equal(True, 1.0))
        self.assertTrue(json_equal(True, True))
        self.assertTrue(json_equal(False, False))

    def test_json_equal_distinguishes_a_string_from_a_number(self):
        from validate_records import json_equal

        self.assertFalse(json_equal(1, "1"))
        self.assertFalse(json_equal("1", 1))
        self.assertFalse(json_equal("1.0", 1.0))
        self.assertTrue(json_equal("1", "1"))

    def test_json_equal_handles_null_without_treating_it_as_false(self):
        """``None`` is JSON null. It equals null and nothing else."""
        from validate_records import json_equal

        self.assertTrue(json_equal(None, None))
        self.assertFalse(json_equal(None, False))
        self.assertFalse(json_equal(None, 0))
        self.assertFalse(json_equal(None, ""))
        self.assertFalse(json_equal(False, None))

    def test_json_equal_compares_nested_lists_by_element_and_type(self):
        from validate_records import json_equal

        self.assertTrue(json_equal([1, 2], [1, 2]))
        self.assertTrue(json_equal([1, 2], [1.0, 2.0]))
        self.assertFalse(json_equal([1, True], [1, 1]))
        self.assertFalse(json_equal([1, 2], [1, 2, 3]))
        self.assertFalse(json_equal([1, 2], [2, 1]))
        self.assertTrue(json_equal([[1], [2]], [[1.0], [2.0]]))

    def test_json_equal_compares_nested_objects_by_key_and_type(self):
        from validate_records import json_equal

        self.assertTrue(json_equal({"a": 1}, {"a": 1.0}))
        self.assertFalse(json_equal({"a": 1}, {"a": True}))
        self.assertFalse(json_equal({"a": 1}, {"a": 1, "b": 2}))
        self.assertFalse(json_equal({"a": 1}, {"b": 1}))
        self.assertTrue(json_equal({"a": [1, {"b": None}]}, {"a": [1.0, {"b": None}]}))
        self.assertFalse(json_equal({"a": [1, {"b": None}]}, {"a": [1, {"b": False}]}))

    def test_json_equal_does_not_confuse_an_object_with_a_list(self):
        from validate_records import json_equal

        self.assertFalse(json_equal({}, []))
        self.assertFalse(json_equal({"0": "a"}, ["a"]))

    def test_enum_rejects_a_value_outside_the_vocabulary(self):
        self._fails_for(_record(outcome="APPROVED"), "ENUM", "outcome")

    def test_const_rejects_a_different_string(self):
        self._fails_for(_record(pass_type="simulation"), "CONST", "pass_type")

    # -- required and additionalProperties ---------------------------------

    def test_a_missing_required_field_fails(self):
        record = _record()
        del record["objective_question"]
        self._fails_for(record, "MISSING_REQUIRED", "objective_question")

    def test_an_undeclared_top_level_field_fails_because_the_schema_forbids_it(self):
        """The schemas now state ``additionalProperties: false`` explicitly.

        Before that, this tool rejected extra fields while the schemas stayed
        silent, so the strictness was the tool's invention. The schema owns the
        rule now, and this test would fail if the declaration were removed.
        """
        self._fails_for(_record(reviewer_comment="x"), "UNKNOWN_FIELD", "reviewer_comment")

    def test_an_undeclared_field_inside_a_declared_object_fails(self):
        self._fails_for(
            _record(environment={"python": "x", "platform": "y", "hostname": "z"}),
            "UNKNOWN_FIELD",
            "environment.hostname",
        )

    def test_a_field_the_schema_leaves_unconstrained_accepts_any_shape(self):
        """``input`` is declared as ``{}``: no constraint at all, so any JSON."""
        self._passes(_record(input={"anything": [1, 2, {"nested": True}]}))

    def test_a_missing_required_field_inside_a_nested_object_fails(self):
        self._fails_for(
            _record(environment={"python": "x"}), "MISSING_REQUIRED", "environment.platform"
        )

    def test_an_empty_schema_constrains_nothing(self):
        from validate_records import schema_problems

        for value in ({}, {"a": 1}, [1, 2], "x", 5, None, True):
            self.assertEqual(schema_problems(value, {}, "f"), [])

    def test_every_supported_keyword_has_a_negative_fixture(self):
        """Guard against a keyword being added to the set without a test.

        The list below is the set of keywords whose rejection a fixture in this
        file demonstrates. If someone adds a keyword to ``SUPPORTED_KEYWORDS``
        and forgets its fixtures, this fails.

        This test previously asserted that ``maxLength`` and ``maximum`` were
        the two missing keywords, which made the gap a requirement: the suite
        would go red if anyone closed it. Both now have positive, negative and
        boundary fixtures, and the assertion is that nothing is missing.
        """
        from validate_records import SUPPORTED_KEYWORDS

        exercised = {
            "type", "enum", "const", "required", "properties",
            "additionalProperties", "items", "minLength", "maxLength",
            "pattern", "minimum", "maximum",
        }
        self.assertLessEqual(
            exercised,
            set(SUPPORTED_KEYWORDS),
            "a keyword in this test is no longer supported",
        )
        missing = set(SUPPORTED_KEYWORDS) - exercised
        self.assertEqual(
            missing,
            set(),
            f"keyword(s) {sorted(missing)} are supported but have no fixture here",
        )

    def test_every_bounded_keyword_has_a_boundary_fixture(self):
        """A limit that rejects everything would pass a negative-only test.

        The four keywords carrying a numeric limit must each be shown accepting
        a value exactly on the limit, not merely rejecting one past it.
        """
        source = Path(__file__).read_text(encoding="utf-8")
        for name in (
            "test_maxLength_boundary_at_the_limit_passes",
            "test_maxLength_boundary_one_over_the_limit_fails",
            "test_minimum_boundary_at_the_limit_passes",
            "test_maximum_boundary_at_the_limit_passes",
            "test_maximum_boundary_one_over_the_limit_fails",
            "test_minLength_boundary_at_the_limit_passes",
        ):
            self.assertIn(f"def {name}(", source)


class UnsupportedKeywordGateTests(unittest.TestCase):
    """A constraint the tool cannot apply must stop the run, never pass."""

    def _schema_with(self, keyword: str, value) -> dict:
        schema = json.loads(
            (ROOT / "schemas" / "simulation_result.schema.json").read_text(encoding="utf-8")
        )
        schema["properties"]["objective_question"][keyword] = value
        return schema

    def test_a_ref_in_a_schema_is_refused(self):
        from validate_records import require_supported_keywords, UnsupportedKeyword

        schema = self._schema_with("$ref", "#/$defs/x")
        with self.assertRaises(UnsupportedKeyword) as caught:
            require_supported_keywords(schema, "example.schema.json")
        self.assertIn("$ref", str(caught.exception))

    def test_a_one_of_is_refused(self):
        from validate_records import require_supported_keywords, UnsupportedKeyword

        schema = self._schema_with("oneOf", [{"type": "string"}])
        with self.assertRaises(UnsupportedKeyword):
            require_supported_keywords(schema, "example.schema.json")

    def test_a_format_is_refused(self):
        """``format`` asserts nothing here, and silently ignoring it would be a lie."""
        from validate_records import require_supported_keywords, UnsupportedKeyword

        schema = self._schema_with("format", "date-time")
        with self.assertRaises(UnsupportedKeyword):
            require_supported_keywords(schema, "example.schema.json")

    def test_an_unsupported_keyword_nested_in_properties_is_refused(self):
        from validate_records import require_supported_keywords, UnsupportedKeyword

        schema = json.loads(
            (ROOT / "schemas" / "simulation_result.schema.json").read_text(encoding="utf-8")
        )
        schema["properties"]["environment"]["properties"]["python"]["minItems"] = 1
        with self.assertRaises(UnsupportedKeyword) as caught:
            require_supported_keywords(schema, "example.schema.json")
        self.assertIn("minItems", str(caught.exception))

    def test_a_made_up_keyword_is_refused(self):
        """Unknown is not the same as allowed."""
        from validate_records import require_supported_keywords, UnsupportedKeyword

        schema = self._schema_with("requiredUnless", ["x"])
        with self.assertRaises(UnsupportedKeyword):
            require_supported_keywords(schema, "example.schema.json")

    def test_every_real_scaffold_schema_is_within_the_supported_subset(self):
        """The gate must not make the tool useless on the schemas it exists for."""
        from validate_records import require_supported_keywords, schema_file

        for path in sorted((ROOT / "schemas").glob("*.schema.json")):
            with self.subTest(schema=path.name):
                require_supported_keywords(
                    json.loads(path.read_text(encoding="utf-8")), path.name
                )

    def test_the_cli_exits_two_on_an_unsupported_schema_keyword(self):
        """Exit 2, not 1: the run could not be performed, so nothing was cleared.

        Both modules hold their own ``SCHEMA_DIR`` — this tool imports one from
        the programme validator and the loader resolves against its own — so a
        copy of the whole schema directory is redirected rather than a single
        lookup function. Redirecting only the lookup left the loader still
        reading the real directory, which is how an earlier draft of this test
        passed a broken schema to a loader that never saw it.
        """
        import shutil

        import validate_programme
        import validate_records

        with tempfile.TemporaryDirectory() as tmp:
            schema_dir = Path(tmp) / "schemas"
            shutil.copytree(ROOT / "schemas", schema_dir)
            schema = self._schema_with("oneOf", [{"type": "string"}])
            (schema_dir / "broken.schema.json").write_text(
                json.dumps(schema), encoding="utf-8"
            )
            records = Path(tmp) / "records"
            records.mkdir()
            _write(records, "SIM-001.json", _record())

            originals = (
                validate_records.SCHEMA_DIR,
                validate_programme.SCHEMA_DIR,
            )
            try:
                validate_records.SCHEMA_DIR = schema_dir
                validate_programme.SCHEMA_DIR = schema_dir
                buffer = io.StringIO()
                with contextlib.redirect_stderr(buffer):
                    code = main([str(records), "--schema", "broken"])
            finally:
                validate_records.SCHEMA_DIR, validate_programme.SCHEMA_DIR = originals

            self.assertEqual(code, 2)
            self.assertIn("UNSUPPORTED_KEYWORD", buffer.getvalue())
            self.assertIn("oneOf", buffer.getvalue())


# ---------------------------------------------------------------------------
# additionalProperties: the schemas own the rule, and the tool must follow it
# ---------------------------------------------------------------------------
#
# The docstring once claimed "None of the scaffold's schemas declares it" while
# six of the seven set it to false. Prose cannot be checked by reading, so the
# state is re-derived here from the schema files, and the tool's behaviour is
# compared against what each schema actually says. A schema added later with no
# decision about extra properties therefore cannot silently pass: this test
# class will describe it and require the tool to behave as it declares.

DECLARES_NO_ADDITIONAL_PROPERTIES = {"source_register_entry"}


def _object_subschemas(node: object, where: str = "(root)"):
    """Yield ``(schema path, subschema)`` for every object subschema in ``node``."""
    if isinstance(node, bool) or not isinstance(node, dict):
        return
    declared = node.get("type")
    is_object = (
        declared == "object"
        or (isinstance(declared, list) and "object" in declared)
        or "properties" in node
    )
    if is_object:
        yield where, node
    properties = node.get("properties")
    if isinstance(properties, dict):
        for name, sub in properties.items():
            yield from _object_subschemas(sub, f"{where}.properties.{name}")
    items = node.get("items")
    if isinstance(items, dict):
        yield from _object_subschemas(items, f"{where}.items")


def _schema_files() -> list[Path]:
    return sorted((ROOT / "schemas").glob("*.schema.json"))


class AdditionalPropertiesDerivedStateTests(unittest.TestCase):
    """Re-derive which schemas declare what, and fail if the docstring is wrong.

    The numbers asserted here are the ones the module docstring states. If a
    schema changes, this test fails and the docstring has to be corrected with
    it, rather than drifting away from the truth again.
    """

    def test_exactly_six_schemas_forbid_additional_properties_at_the_root(self):
        forbidding = [
            path.name
            for path in _schema_files()
            if json.loads(path.read_text(encoding="utf-8")).get("additionalProperties") is False
        ]
        self.assertEqual(
            sorted(forbidding),
            [
                "clause_reference.schema.json",
                "programme_status.schema.json",
                "requirement_record.schema.json",
                "research_record.schema.json",
                "simulation_case.schema.json",
                "simulation_result.schema.json",
            ],
        )

    def test_exactly_one_schema_declares_no_additional_properties_at_all(self):
        silent = [
            path.name
            for path in _schema_files()
            if "additionalProperties"
            not in json.loads(path.read_text(encoding="utf-8"))
        ]
        self.assertEqual(silent, ["source_register_entry.schema.json"])
        self.assertEqual(
            silent,
            sorted(f"{name}.schema.json" for name in DECLARES_NO_ADDITIONAL_PROPERTIES),
            "the set named in the test module and the set on disk disagree",
        )

    def test_simulation_result_declares_it_on_exactly_its_two_nested_objects(self):
        schema = json.loads(
            (ROOT / "schemas" / "simulation_result.schema.json").read_text(encoding="utf-8")
        )
        declared = [
            (where, sub.get("additionalProperties"))
            for where, sub in _object_subschemas(schema)
            if "additionalProperties" in sub
        ]
        self.assertEqual(
            sorted(declared),
            [
                ("(root)", False),
                ("(root).properties.environment", False),
                ("(root).properties.known_answer_check", False),
            ],
        )

    def test_no_other_schema_declares_it_on_a_nested_object(self):
        offenders = []
        for path in _schema_files():
            if path.name == "simulation_result.schema.json":
                continue
            schema = json.loads(path.read_text(encoding="utf-8"))
            for where, sub in _object_subschemas(schema):
                if where != "(root)" and "additionalProperties" in sub:
                    offenders.append(f"{path.name}:{where}")
        self.assertEqual(offenders, [])

    def test_the_module_docstring_matches_the_derived_schema_state(self):
        """The prose names six schemas, two nested objects and one silent schema."""
        import validate_records

        doc = validate_records.__doc__
        for name in (
            "clause_reference",
            "programme_status",
            "requirement_record",
            "research_record",
            "simulation_case",
            "simulation_result",
        ):
            self.assertIn(f"``{name}``", doc, f"the docstring does not name {name}")
        self.assertIn("``properties.environment``", doc)
        self.assertIn("``properties.known_answer_check``", doc)
        self.assertIn("``source_register_entry``", doc)
        # The false claim that has to stay dead.
        self.assertNotIn("None of the scaffold's schemas declares", doc)


class AdditionalPropertiesBehaviourTests(unittest.TestCase):
    """For every schema, the tool's behaviour must match what that schema says."""

    # Candidate values tried in order until one satisfies the field's schema.
    # The search is over the schema's own constraints, so this does not hardcode
    # what any particular schema happens to require.
    STRING_CANDIDATES = (
        "x",
        "SIM-001",
        "RES-001",
        "ULC-01-01",
        "a" * 64,
        "0" * 40,
        "2026-01-01T00:00:00+00:00",
        "01.E05",
        "PUBLICLY_CLEARED",
        "NONE",
        "NOT_AUTHORIZED",
        "documented",
        "COMPLETED",
        "PASS",
        "executed",
        "example-value",
        "catalogue_transcription",
        "full",
        "",
    )

    def _conformant_value(self, sub: dict):
        """Return the first candidate value that satisfies ``sub``, or raise.

        Raises rather than returning a placeholder that would trip an unrelated
        constraint: a fixture that failed for a reason other than the one under
        test would make the audit meaningless.
        """
        declared = sub.get("type")
        names = [declared] if isinstance(declared, str) else list(declared or [])
        if "const" in sub:
            return sub["const"]
        if "enum" in sub:
            return sub["enum"][0]
        if "object" in names:
            return self._minimal_record_for(sub)
        if "array" in names:
            items = sub.get("items")
            if isinstance(items, dict):
                return [self._conformant_value(items)]
            return []
        if "null" in names and "string" not in names:
            return None
        if "boolean" in names:
            return False
        if "integer" in names:
            return 0
        if "number" in names:
            return 0.0
        candidates = list(self.STRING_CANDIDATES)
        if "string" not in names and names:
            candidates = [0, 0.0, False, None] + candidates
        for candidate in candidates:
            if not names or self._satisfies(candidate, sub, names):
                return candidate
        raise AssertionError(
            f"no candidate satisfies this subschema, so the audit cannot build "
            f"a clean baseline: {json.dumps(sub, sort_keys=True)}"
        )

    def _satisfies(self, value, sub: dict, names: list[str]) -> bool:
        from validate_records import matches_type

        if names and not matches_type(value, names):
            return False
        if isinstance(value, str):
            if "minLength" in sub and len(value) < sub["minLength"]:
                return False
            if "maxLength" in sub and len(value) > sub["maxLength"]:
                return False
            if "pattern" in sub and not re.search(sub["pattern"], value):
                return False
        return True

    def _minimal_record_for(self, schema: dict) -> dict:
        """Build a record satisfying every required field, derived from the schema.

        Every value is found by search against the field's own subschema, so a
        record that tripped an unrelated constraint cannot be mistaken for the
        additional-property result the audit is asking about.
        """
        record: dict = {}
        properties = schema.get("properties") or {}
        for name in schema.get("required", []):
            record[name] = self._conformant_value(properties.get(name, {}))
        return record

    def test_every_schema_permits_or_forbids_an_extra_root_property_as_it_declares(self):
        """One assertion per schema file, driven by the schema's own declaration.

        A schema that forbids extra properties must produce a failure for one;
        a schema that says nothing must not. This walks every schema on disk, so
        a schema added later without a decision cannot pass silently.
        """
        for path in _schema_files():
            schema = json.loads(path.read_text(encoding="utf-8"))
            declared = schema.get("additionalProperties", None)
            with self.subTest(schema=path.name, declared=declared):
                record = self._minimal_record_for(schema)
                baseline = validate_records_schema_problems(record, schema, "")
                self.assertEqual(
                    baseline,
                    [],
                    f"{path.name}: the placeholder record is not conformant, so the "
                    "extra-property result would be unreadable",
                )
                marked = dict(record)
                marked["stray_property_for_the_audit"] = "x"
                problems = validate_records_schema_problems(marked, schema, "")
                kinds = [p["kind"] for p in problems]
                if declared is False:
                    self.assertEqual(kinds, ["UNKNOWN_FIELD"], path.name)
                    self.assertEqual(problems[0]["field"], "stray_property_for_the_audit")
                else:
                    self.assertEqual(kinds, ["UNDECLARED_FIELD"], path.name)

    def test_every_nested_object_permits_or_forbids_an_extra_property_as_it_declares(self):
        """Same audit one level down, for every nested object in every schema.

        The nested case is where a root-only implementation would look correct
        and still be wrong.
        """
        for path in _schema_files():
            schema = json.loads(path.read_text(encoding="utf-8"))
            record = self._minimal_record_for(schema)
            for where, sub in _object_subschemas(schema):
                if where == "(root)":
                    continue
                field = where.split(".properties.")[-1]
                declared = sub.get("additionalProperties", None)
                with self.subTest(schema=path.name, object=field, declared=declared):
                    nested = dict(record.get(field) or {})
                    if not isinstance(nested, dict):
                        continue
                    nested["stray_property_for_the_audit"] = "x"
                    marked = dict(record)
                    marked[field] = nested
                    problems = validate_records_schema_problems(marked, schema, "")
                    hits = [p for p in problems if p["field"] == f"{field}.stray_property_for_the_audit"]
                    self.assertEqual(len(hits), 1, f"{path.name}:{field}: {problems}")
                    expected = "UNKNOWN_FIELD" if declared is False else "UNDECLARED_FIELD"
                    self.assertEqual(hits[0]["kind"], expected, f"{path.name}:{field}")


class NestedAdditionalPropertiesTests(unittest.TestCase):
    """``simulation_result``'s two nested objects, proved one at a time."""

    def test_a_stray_property_in_environment_fails(self):
        self._fails_in_nested("environment", {"python": "x", "platform": "y"})

    def test_a_stray_property_in_known_answer_check_fails(self):
        self._fails_in_nested(
            "known_answer_check", {"included": False, "case_id": None, "detail": "d"}
        )

    def _fails_in_nested(self, field: str, nested: dict) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            polluted = dict(nested)
            polluted["stray"] = "value"
            _write(directory, "SIM-001.json", _record(**{field: polluted}))
            report = validate_directory(directory, SCHEMA)
        self.assertFalse(report["ok"], "a stray nested property must fail")
        problem = _failure_for(report, f"{field}.stray")
        self.assertEqual(problem["kind"], "UNKNOWN_FIELD")
        self.assertIn("forbids additional properties", problem["reason"])

    def test_the_clean_nested_objects_pass(self):
        """Control: the same fixture without the stray property passes."""
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record())
            report = validate_directory(directory, SCHEMA)
        self.assertTrue(report["ok"], report["failures"])

    def test_a_nested_object_with_no_declaration_permits_the_property(self):
        """A nested object that says nothing permits it, and warns.

        Driven through a temporary schema rather than a scaffold one, because
        every nested object in the scaffold's schemas that declares properties
        also forbids extras. A temporary schema directory is used so the
        scaffold's own files are untouched.
        """
        import validate_programme

        with tempfile.TemporaryDirectory() as tmp:
            schema_dir = Path(tmp) / "schemas"
            schema_dir.mkdir()
            schema = {
                "type": "object",
                "required": ["outer"],
                "properties": {
                    "outer": {
                        "type": "object",
                        "required": ["inner"],
                        "properties": {"inner": {"type": "string"}},
                        # no additionalProperties: the nested object permits extras
                    }
                },
                "additionalProperties": False,
            }
            (schema_dir / "permissive.schema.json").write_text(
                json.dumps(schema), encoding="utf-8"
            )
            records = Path(tmp) / "records"
            records.mkdir()
            _write(records, "r.json", {"outer": {"inner": "x", "stray": 1}})

            originals = (vrecords.SCHEMA_DIR, validate_programme.SCHEMA_DIR)
            try:
                vrecords.SCHEMA_DIR = schema_dir
                validate_programme.SCHEMA_DIR = schema_dir
                report = validate_directory(records, "permissive")
            finally:
                vrecords.SCHEMA_DIR, validate_programme.SCHEMA_DIR = originals
        self.assertTrue(report["ok"], report["failures"])
        self.assertEqual(
            [item["field"] for item in report["permitted_extra_fields"]], ["outer.stray"]
        )
        self.assertEqual(report["failures"], [])

    def test_the_permitted_extra_warning_reaches_the_human_report(self):
        """A warning that never reaches the reader is not a warning."""
        import validate_programme

        with tempfile.TemporaryDirectory() as tmp:
            schema_dir = Path(tmp) / "schemas"
            schema_dir.mkdir()
            schema = {
                "type": "object",
                "required": ["a"],
                "properties": {"a": {"type": "string"}},
            }
            (schema_dir / "silent.schema.json").write_text(json.dumps(schema), encoding="utf-8")
            records = Path(tmp) / "records"
            records.mkdir()
            _write(records, "r.json", {"a": "x", "stray": 1})

            originals = (vrecords.SCHEMA_DIR, validate_programme.SCHEMA_DIR)
            try:
                vrecords.SCHEMA_DIR = schema_dir
                validate_programme.SCHEMA_DIR = schema_dir
                report = validate_directory(records, "silent")
                rendered = render_human(report)
            finally:
                vrecords.SCHEMA_DIR, validate_programme.SCHEMA_DIR = originals
        self.assertTrue(report["ok"])
        self.assertIn("stray", rendered)
        self.assertIn("permitted", rendered.lower())
        self.assertIn("permitted undeclared field(s)", report["verdict"])


# ---------------------------------------------------------------------------
# Fail closed: an unimplemented constraint must stop the run, every time
# ---------------------------------------------------------------------------
#
# Ignoring a constraint the tool does not implement produces a pass that was
# never earned. These tests prove the refusal for a representative set of
# keywords, at the library level, at the CLI level with a real exit code, and
# when the keyword is buried in a nested subschema.

REPRESENTATIVE_UNSUPPORTED = (
    "$ref",
    "oneOf",
    "allOf",
    "not",
    "format",
    "minItems",
    "uniqueItems",
    "multipleOf",
    "exclusiveMinimum",
    "if",
    "patternProperties",
)


def _schema_dir_with(tmp: Path, schema: dict, name: str = "broken") -> Path:
    schema_dir = tmp / "schemas"
    schema_dir.mkdir()
    (schema_dir / f"{name}.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    return schema_dir


def _tools_copy(tmp: Path) -> Path:
    """Copy the tool package so a CLI subprocess sees a redirected schema dir.

    ``SCHEMA_DIR`` is resolved from the module's own location, so patching it in
    this process would not affect a subprocess. Copying the package and putting
    the broken schema beside it is the only way to get a real exit code from a
    real CLI run without writing into the repository.
    """
    import shutil

    tools = tmp / "tools"
    tools.mkdir()
    for source in (ROOT / "tools").glob("*.py"):
        shutil.copy2(source, tools / source.name)
    return tools


class FailClosedKeywordTests(unittest.TestCase):
    """A keyword the tool cannot apply raises, and the message says which."""

    def _schema_with(self, keyword: str, *, nested: bool = False) -> dict:
        schema = json.loads(
            (ROOT / "schemas" / "simulation_result.schema.json").read_text(encoding="utf-8")
        )
        target = schema["properties"]["objective_question"]
        if nested:
            target = schema["properties"]["environment"]["properties"]["python"]
        target[keyword] = "#/$defs/x" if keyword == "$ref" else [{"type": "string"}]
        return schema

    def test_each_representative_keyword_is_refused_at_the_library(self):
        from validate_records import require_supported_keywords, UnsupportedKeyword

        for keyword in REPRESENTATIVE_UNSUPPORTED:
            with self.subTest(keyword=keyword):
                with self.assertRaises(UnsupportedKeyword) as caught:
                    require_supported_keywords(self._schema_with(keyword), "example.schema.json")
                message = str(caught.exception)
                self.assertIn(keyword, message, "the refusal must name the keyword")
                self.assertIn("UNSUPPORTED_KEYWORD", message)

    def test_the_refusal_names_the_schema_path(self):
        """A bare keyword name is not enough: the reader must find it."""
        from validate_records import require_supported_keywords, UnsupportedKeyword

        for keyword in REPRESENTATIVE_UNSUPPORTED:
            with self.subTest(keyword=keyword):
                with self.assertRaises(UnsupportedKeyword) as caught:
                    require_supported_keywords(self._schema_with(keyword), "example.schema.json")
                self.assertIn(
                    "properties.objective_question",
                    str(caught.exception),
                    f"the refusal for {keyword} does not say where it sits",
                )

    def test_the_check_is_recursive_and_stops_a_nested_keyword(self):
        from validate_records import require_supported_keywords, UnsupportedKeyword

        for keyword in REPRESENTATIVE_UNSUPPORTED:
            with self.subTest(keyword=keyword):
                with self.assertRaises(UnsupportedKeyword) as caught:
                    require_supported_keywords(
                        self._schema_with(keyword, nested=True), "example.schema.json"
                    )
                message = str(caught.exception)
                self.assertIn(keyword, message)
                self.assertIn("properties.environment.properties.python", message)

    def test_a_supported_only_schema_does_not_trip_the_gate(self):
        """Negative control: the gate must not fire on a conformant schema."""
        from validate_records import require_supported_keywords

        for path in sorted((ROOT / "schemas").glob("*.schema.json")):
            with self.subTest(schema=path.name):
                require_supported_keywords(
                    json.loads(path.read_text(encoding="utf-8")), path.name
                )

    def test_the_gate_is_not_satisfied_by_a_schema_with_no_constraints(self):
        """An empty schema trips nothing, which is correct and not a silent pass."""
        from validate_records import require_supported_keywords

        require_supported_keywords({}, "empty.schema.json")


class FailClosedCliTests(unittest.TestCase):
    """The CLI exits 2, not 0, when it cannot apply the schema."""

    def _run_cli_with(self, schema: dict) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            tools = _tools_copy(base)
            _schema_dir_with(base, schema)
            records = base / "records"
            records.mkdir()
            _write(records, "SIM-001.json", _record())
            return subprocess.run(
                [
                    sys.executable,
                    str(tools / "validate_records.py"),
                    str(records),
                    "--schema",
                    "broken",
                ],
                capture_output=True,
                text=True,
            )

    def test_the_cli_exits_two_for_each_representative_keyword(self):
        observed = {}
        for keyword in REPRESENTATIVE_UNSUPPORTED:
            with self.subTest(keyword=keyword):
                schema = json.loads(
                    (ROOT / "schemas" / "simulation_result.schema.json").read_text(encoding="utf-8")
                )
                schema["properties"]["objective_question"][keyword] = (
                    "#/$defs/x" if keyword == "$ref" else [{"type": "string"}]
                )
                proc = self._run_cli_with(schema)
                observed[keyword] = proc.returncode
                self.assertEqual(proc.returncode, 2, f"{keyword}: {proc.stdout}{proc.stderr}")
                self.assertIn("UNSUPPORTED_KEYWORD", proc.stderr)
                self.assertIn(keyword, proc.stderr)
                self.assertEqual(proc.stdout, "", "a refused run clears nothing, so prints no verdict")
        self.assertEqual(set(observed.values()), {2})

    def test_the_cli_exits_zero_on_a_supported_only_schema(self):
        """Negative control: same harness, no unsupported keyword, exits 0."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            tools = _tools_copy(base)
            schema_dir = base / "schemas"
            schema_dir.mkdir()
            for source in (ROOT / "schemas").glob("*.schema.json"):
                (schema_dir / source.name).write_text(
                    source.read_text(encoding="utf-8"), encoding="utf-8"
                )
            records = base / "records"
            records.mkdir()
            _write(records, "SIM-001.json", _record())
            proc = subprocess.run(
                [
                    sys.executable,
                    str(tools / "validate_records.py"),
                    str(records),
                    "--schema",
                    "simulation_result",
                ],
                capture_output=True,
                text=True,
            )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("VERDICT: PASS", proc.stdout)


class UnsupportedSchemaArgumentTests(unittest.TestCase):
    """A keyword whose argument cannot be read is refused, not skipped.

    Each of these was a silent pass before: an ``isinstance`` guard skipped the
    constraint and the record passed something that was never checked.
    """

    def _assert_refused(self, schema: dict, keyword: str) -> str:
        from validate_records import require_supported_keywords, UnsupportedKeyword

        with self.assertRaises(UnsupportedKeyword) as caught:
            require_supported_keywords(schema, "example.schema.json")
        message = str(caught.exception)
        self.assertIn(keyword, message)
        return message

    def test_maxLength_with_a_string_argument_is_refused(self):
        message = self._assert_refused({"maxLength": "3"}, "maxLength")
        self.assertIn("non-negative integer", message)

    def test_maxLength_with_a_boolean_argument_is_refused(self):
        self._assert_refused({"maxLength": True}, "maxLength")

    def test_maxLength_with_a_negative_argument_is_refused(self):
        self._assert_refused({"maxLength": -1}, "maxLength")

    def test_minLength_with_a_string_argument_is_refused(self):
        self._assert_refused({"minLength": "1"}, "minLength")

    def test_minimum_with_a_string_argument_is_refused(self):
        message = self._assert_refused({"minimum": "5"}, "minimum")
        self.assertIn("must be a number", message)

    def test_maximum_with_a_boolean_argument_is_refused(self):
        self._assert_refused({"maximum": True}, "maximum")

    def test_required_that_is_not_an_array_of_strings_is_refused(self):
        self._assert_refused({"required": "abc"}, "required")
        self._assert_refused({"required": [1, 2]}, "required")

    def test_enum_that_is_not_a_non_empty_array_is_refused(self):
        self._assert_refused({"enum": "abc"}, "enum")
        self._assert_refused({"enum": []}, "enum")

    def test_a_type_name_the_tool_cannot_check_is_refused(self):
        self._assert_refused({"type": "objectx"}, "type")
        self._assert_refused({"type": ["string", "bogus"]}, "type")
        self._assert_refused({"type": []}, "type")

    def test_the_tuple_form_of_items_is_refused(self):
        """Draft-07 tuples validate position by position. Ignoring the list
        would check nothing at all while the schema appears to say something."""
        message = self._assert_refused({"items": [{"type": "integer"}]}, "items")
        self.assertIn("tuple", message)

    def test_a_boolean_subschema_under_properties_is_refused(self):
        self._assert_refused({"properties": {"x": False}}, "properties")
        self._assert_refused({"properties": {"x": True}}, "properties")

    def test_an_additionalProperties_value_that_is_neither_boolean_nor_schema_is_refused(self):
        self._assert_refused({"additionalProperties": "false"}, "additionalProperties")
        self._assert_refused({"additionalProperties": 0}, "additionalProperties")

    def test_a_schema_value_containing_a_keyword_name_is_not_refused(self):
        """Control: a *value* is data, not a schema.

        ``const: {"format": "date-time"}`` is a permitted constant value. It is
        not a use of the unsupported ``format`` keyword. Walking it as a schema
        would refuse a schema that is entirely within the supported subset, and
        an earlier version of the gate did exactly that.
        """
        from validate_records import require_supported_keywords

        for schema in (
            {"properties": {"x": {"const": {"format": "date-time"}}}},
            {"properties": {"x": {"enum": [{"oneOf": 1}]}}},
            {"properties": {"x": {"default": {"patternProperties": 1}}}},
            {"const": {"$ref": "#/x"}},
        ):
            with self.subTest(schema=schema):
                require_supported_keywords(schema, "example.schema.json")


# ---------------------------------------------------------------------------
# Non-standard JSON, and the defects found while fixing the listed ones
# ---------------------------------------------------------------------------

class NonStandardJsonTests(unittest.TestCase):
    """``NaN`` and ``Infinity`` are not JSON values and must not be read as ones.

    ``json.loads`` accepts both by default. Accepting them would let a record
    carry a literal no JSON consumer can read, and the ``--json`` report would
    serialise it back out as invalid JSON.
    """

    def test_nan_in_a_record_is_refused(self):
        for literal in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(literal=literal):
                with tempfile.TemporaryDirectory() as tmp:
                    directory = Path(tmp) / "records"
                    directory.mkdir()
                    _write(directory, "SIM-001.json", _record(input={"value": "PLACEHOLDER"}))
                    path = directory / "SIM-001.json"
                    # Written as text so the raw token reaches the parser.
                    path.write_text(
                        path.read_text(encoding="utf-8").replace('"PLACEHOLDER"', literal),
                        encoding="utf-8",
                    )
                    report = validate_directory(directory, SCHEMA)
                self.assertFalse(report["ok"])
                problem = _failure_for(report, "(record)")
                self.assertEqual(problem["kind"], "NOT_JSON")
                self.assertIn("not valid JSON", problem["reason"])
                self.assertIn(literal, problem["reason"])

    def test_the_report_stays_valid_json_when_a_record_holds_nan(self):
        """A refused record must not poison the machine-readable report."""
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(directory, "SIM-001.json", _record())
            path = directory / "SIM-001.json"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    '"example-method"', "NaN"
                ),
                encoding="utf-8",
            )
            proc = _run(directory, "--json")
        self.assertEqual(proc.returncode, 1)
        payload = json.loads(proc.stdout)  # would raise on NaN if it leaked
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["failures"][0]["kind"], "NOT_JSON")


class KeywordValueDataTests(unittest.TestCase):
    """A record *value* is data. A schema keyword name inside it is not a keyword."""

    def test_a_record_value_named_like_a_keyword_does_not_stop_the_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            _write(
                directory,
                "SIM-001.json",
                _record(input={"format": "date-time", "oneOf": [1], "patternProperties": {}}),
            )
            report = validate_directory(directory, SCHEMA)
        self.assertTrue(report["ok"], report["failures"])

    def test_a_const_whose_value_looks_like_a_schema_is_not_walked(self):
        from validate_records import require_supported_keywords

        require_supported_keywords(
            {"properties": {"x": {"const": {"format": "date-time"}}}}, "x.schema.json"
        )


class BooleanSubschemaTests(unittest.TestCase):
    """A boolean subschema is refused rather than silently ignored.

    ``{"properties": {"x": false}}`` forbids the property entirely. The tool
    cannot apply that, so it must stop rather than pass a record that sets it.
    """

    def test_a_false_property_subschema_is_refused_rather_than_passed(self):
        from validate_records import require_supported_keywords, UnsupportedKeyword

        with self.assertRaises(UnsupportedKeyword):
            require_supported_keywords({"properties": {"x": False}}, "x.schema.json")

    def test_the_library_reports_a_problem_even_if_the_gate_is_bypassed(self):
        """Defence in depth: a direct caller gets a reported problem, not a pass."""
        problems = validate_records_schema_problems(
            {"x": 1}, {"properties": {"x": False}}, ""
        )
        kinds = [p["kind"] for p in problems]
        self.assertIn("UNSUPPORTED_SUBSCHEMA", kinds)


class ItemsTests(unittest.TestCase):
    """``items`` applies one subschema to every element of an array.

    ``source_register_entry.independence_from`` is the one scaffold field that
    declares it, so these fixtures run through the real schema file rather than
    a hand-built node wherever the schema makes that possible.
    """

    def _write_source(self, directory: Path, value) -> None:
        _write(
            directory,
            "s.json",
            {
                "id": "SRC-001",
                "kind": "tablet",
                "review_scope": "full",
                "release_classification": "PUBLICLY_CLEARED",
                "source_role": "catalogue_transcription",
                "independence_from": value,
            },
        )

    def test_a_conforming_array_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            self._write_source(directory, ["SRC-002", "SRC-003"])
            report = validate_directory(directory, "source_register_entry")
        self.assertTrue(report["ok"], report["failures"])

    def test_an_empty_array_passes_because_the_schema_sets_no_minItems(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            self._write_source(directory, [])
            report = validate_directory(directory, "source_register_entry")
        self.assertTrue(report["ok"], report["failures"])

    def test_a_non_string_element_fails_at_its_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            self._write_source(directory, ["SRC-002", 7])
            report = validate_directory(directory, "source_register_entry")
        self.assertFalse(report["ok"])
        problem = _failure_for(report, "independence_from[1]")
        self.assertEqual(problem["kind"], "TYPE")
        self.assertIn("must be string", problem["reason"])

    def test_an_element_violating_a_nested_constraint_fails_at_its_index(self):
        """The per-element subschema carries ``minLength``, not just ``type``."""
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            self._write_source(directory, ["ok", ""])
            report = validate_directory(directory, "source_register_entry")
        self.assertFalse(report["ok"])
        problem = _failure_for(report, "independence_from[1]")
        self.assertEqual(problem["kind"], "MIN_LENGTH")

    def test_every_bad_element_is_reported_not_just_the_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "records"
            directory.mkdir()
            self._write_source(directory, [1, 2])
            report = validate_directory(directory, "source_register_entry")
        fields = sorted(item["field"] for item in report["failures"])
        self.assertEqual(fields, ["independence_from[0]", "independence_from[1]"])

    def test_items_is_not_applied_to_a_non_array_value(self):
        """``items`` constrains arrays only, as the specification requires."""
        from validate_records import schema_problems

        self.assertEqual(schema_problems({"a": 1}, {"items": {"type": "integer"}}, "f"), [])
        self.assertEqual(schema_problems("abc", {"items": {"type": "integer"}}, "f"), [])
