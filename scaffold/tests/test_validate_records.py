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
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

from validate_records import (
    SCOPE,
    UNSPECIFIED,
    main,
    schema_file,
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
        """A pass is structural only, and the report says so."""
        for phrase in ("does not prove", "pattern, minLength and minimum"):
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
