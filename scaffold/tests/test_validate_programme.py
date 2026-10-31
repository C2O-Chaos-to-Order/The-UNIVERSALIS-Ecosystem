"""Validator checks, negative fixtures, and the repository identifier scan.

Every negative fixture must fail for its own stated reason. A fixture that
fails for a different reason is a broken fixture, not a passing test.
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The repository root. This file is scaffold/tests/test_validate_programme.py,
# so parents[0] is tests/, parents[1] is scaffold/, and parents[2] is the repo
# root. Every repository scan below is rooted here and nowhere else.
REPO_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

from support import (
    build_altered_expected,
    build_authorization_without_record,
    build_duplicate_id,
    build_evidence_authorized_default_authorization,
    build_evidence_authorized_without_authorization,
    build_evidence_outcome_confusion,
    build_executed,
    build_executed_without_execution_evidence,
    build_owner_acceptance_with_decision,
    build_owner_acceptance_without_decision,
    build_self_credit,
    build_unclassified,
    build_verified_without_decision,
    build_wrong_hash,
    run_validator,
)
from validate_programme import (
    PLAN_EVIDENCE_FIELDS,
    SIMULATION_PASS_FIELDS,
    STATES,
)

# A four-digit collection-register id. The separate collection-level register
# already uses UNI-001..UNI-015 as collection ids, so a four-digit UNI- id here
# collided with it and was previously repaired to ULC-<tablet>-<clause>.
# Requirement ids in this repository must therefore never carry a four-digit
# UNI- id.
FOUR_DIGIT_UNI = re.compile(r"UNI-\d{4}")

SCANNED_SUFFIXES = frozenset({".py", ".md", ".json", ".csv"})
SKIPPED_DIR_PARTS = frozenset({".git", "__pycache__"})


def scan_four_digit_uni_ids(root: Path, *, exclude: Path | None = None) -> list[Path]:
    """Return files under ``root`` that contain a four-digit ``UNI-`` id.

    ``root`` is the only directory read. Nothing outside it can affect the
    result, which is the point: the scan is a statement about one tree.
    ``exclude`` names a file to skip, compared by resolved path, so a scan
    module that contains its own pattern cannot match itself.
    """
    root = Path(root).resolve()
    skip = exclude.resolve() if exclude is not None else None
    offenders: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in SKIPPED_DIR_PARTS for part in relative.parts):
            continue
        if path.suffix not in SCANNED_SUFFIXES:
            continue
        resolved = path.resolve()
        if skip is not None and resolved == skip:
            continue
        if FOUR_DIGIT_UNI.search(resolved.read_text(encoding="utf-8", errors="ignore")):
            offenders.append(resolved)
    return offenders


def _failing_check(payload: dict) -> str:
    failed = [item["check"] for item in payload["checks"] if item["outcome"] == "FAIL"]
    return failed[0] if len(failed) == 1 else str(failed)


def _reasons(payload: dict, check: str) -> str:
    for item in payload["checks"]:
        if item["check"] == check:
            return "\n".join(item["reasons"])
    return ""


class ValidatorTests(unittest.TestCase):
    def test_plan_fields_are_required_and_authorization_is_separate(self):
        research = json.loads(
            (ROOT / "schemas" / "research_record.schema.json").read_text(encoding="utf-8")
        )
        result = json.loads(
            (ROOT / "schemas" / "simulation_result.schema.json").read_text(encoding="utf-8")
        )
        for field in PLAN_EVIDENCE_FIELDS:
            self.assertIn(field, research["required"], field)
            self.assertIn(field, result["required"], field)
        for field in SIMULATION_PASS_FIELDS:
            self.assertIn(field, result["required"], field)
            self.assertNotIn(field, research["required"], field)
        self.assertIn("evidence_status", research["properties"])
        self.assertIn("authorization_status", research["properties"])
        self.assertNotEqual(
            research["properties"]["evidence_status"],
            research["properties"]["authorization_status"],
        )
        self.assertEqual(
            research["properties"]["authorization_status"]["enum"],
            ["NOT_AUTHORIZED", "AUTHORIZED"],
        )
        # The evidence enum is the Plan ladder, not the retired scaffold ladder.
        self.assertEqual(research["properties"]["evidence_status"]["enum"], list(STATES))
        self.assertEqual(result["properties"]["evidence_status"]["enum"], list(STATES))
        requirement = json.loads(
            (ROOT / "schemas" / "requirement_record.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            requirement["properties"]["requirement_id"]["pattern"], r"^ULC-[0-9]{2}-[0-9]{2}$"
        )
        self.assertEqual(requirement["properties"]["evidence_status"]["enum"], list(STATES))

    def test_only_two_pass_type_values_can_be_emitted(self):
        """The Plan allows exactly ``research`` and ``executed_simulation``.

        This is a whitelist test: it collects every ``pass_type`` value the
        scaffold can write, plus the constants that constrain them, and asserts
        the set is exactly the two Plan values.
        """
        from validate_programme import (
            PASS_TYPE_EXECUTED_SIMULATION,
            PASS_TYPE_RESEARCH,
            PASS_TYPE_VALUES,
        )

        self.assertEqual(PASS_TYPE_VALUES, {"research", "executed_simulation"})
        research = json.loads(
            (ROOT / "schemas" / "research_record.schema.json").read_text(encoding="utf-8")
        )
        result = json.loads(
            (ROOT / "schemas" / "simulation_result.schema.json").read_text(encoding="utf-8")
        )
        emitted = {
            research["properties"]["pass_type"]["const"],
            result["properties"]["pass_type"]["const"],
        }
        # Ledger headers carry the column name, not a value. The templates that
        # seed a value are scanned for the literal too.
        runner = (
            ROOT / "templates" / "programme" / "simulations" / "run_one.py"
        ).read_text(encoding="utf-8")
        card = (
            ROOT / "templates" / "programme" / "research" / "_TEMPLATE_research_card.md"
        ).read_text(encoding="utf-8")
        if '"pass_type": "executed_simulation"' in runner:
            emitted.add("executed_simulation")
        if "\nresearch\n" in card:
            emitted.add("research")
        self.assertEqual(emitted, {"research", "executed_simulation"})
        self.assertEqual(emitted, PASS_TYPE_VALUES)

    def test_executed_package_passes_all_seven_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = build_executed(Path(tmp) / "programme")
            code, payload, stderr = run_validator(package)
            self.assertEqual(code, 0, stderr + "\n" + json.dumps(payload, indent=2))
            self.assertEqual(
                [item["check"] for item in payload["checks"]],
                [
                    "manifest_integrity",
                    "traceability",
                    "execution_evidence",
                    "expectation_discipline",
                    "count_arithmetic",
                    "honest_status",
                    "classification_gate",
                ],
            )
            result = json.loads(
                (package / "results" / "SIM-001.json").read_text(encoding="utf-8")
            )
            self.assertEqual(result["pass_type"], "executed_simulation")
            self.assertEqual(result["execution_outcome"], "executed")
            self.assertEqual(result["evidence_status"], "documented")
            self.assertEqual(result["authorization_status"], "NOT_AUTHORIZED")
            self.assertNotEqual(result["authorization_status"], result["evidence_status"])
            self.assertEqual(result["programme_credit"], "CANDIDATE_PENDING_OWNER_REVIEW")
            # The four Plan simulation-pass fields are present and honest.
            for field in (
                "execution_timestamp",
                "failure_policy",
                "known_answer_check",
                "mcse_or_precision_note",
            ):
                self.assertIn(field, result, field)
            self.assertRegex(
                result["execution_timestamp"],
                r"(Z|[+-]\d{2}:\d{2})$",
                "execution_timestamp must carry an explicit offset",
            )

    def test_wrong_hash_fails_manifest_integrity(self):
        self._expect(
            "wrong_hash",
            build_wrong_hash,
            "manifest_integrity",
            "MANIFEST_INTEGRITY: hash mismatch for README.md",
        )

    def test_duplicate_identifier_fails_traceability(self):
        self._expect(
            "duplicate_id",
            build_duplicate_id,
            "traceability",
            "DUPLICATE_IDENTIFIER: SRC-001 appears more than once in sources/source_register.json",
        )

    def test_unclassified_artefact_fails_classification_gate(self):
        self._expect(
            "unclassified",
            build_unclassified,
            "classification_gate",
            "UNCLASSIFIED_ARTEFACT: unclassified artefact notes/stray.txt has no classification",
        )

    def test_altered_expected_outcome_fails_expectation_discipline(self):
        self._expect(
            "altered_expected",
            build_altered_expected,
            "expectation_discipline",
            "EXPECTATION_MISMATCH: result SIM-001 records an expected outcome that does not equal the expected outcome declared in simulations/scenarios.json",
        )

    def test_self_awarded_programme_credit_fails_honest_status(self):
        self._expect(
            "self_credit",
            build_self_credit,
            "honest_status",
            "PROGRAMME_CREDIT_SELF_AWARDED: RES-001 refusing to award programme credit without an explicit owner or reviewer decision record",
        )

    def test_verified_without_decision_fails_honest_status(self):
        self._expect(
            "verified_without_decision",
            build_verified_without_decision,
            "honest_status",
            "EVIDENCE_STATE_WITHOUT_DECISION: RES-001 evidence state 'verified' requires an explicit owner or reviewer decision record",
        )

    def test_authorization_without_record_fails_honest_status(self):
        self._expect(
            "authorization_without_record",
            build_authorization_without_record,
            "honest_status",
            "AUTHORIZATION_WITHOUT_RECORD: RES-001 authorization_status 'AUTHORIZED' is not the default NOT_AUTHORIZED and no authorization record exists",
        )

    def test_evidence_authorized_does_not_grant_authorization(self):
        """The sharpest distinction: evidence state is not authorization.

        The fixture carries ``evidence_status: authorized`` and sets
        ``authorization_status: AUTHORIZED`` on the strength of it alone. No
        authorization record exists, so validation must refuse.
        """
        self._expect(
            "evidence_authorized_without_authorization",
            build_evidence_authorized_without_authorization,
            "honest_status",
            "AUTHORIZATION_WITHOUT_RECORD: RES-001 sets authorization_status AUTHORIZED "
            "while carrying evidence_status 'authorized'; the evidence state is not an "
            "authorization record and does not imply one",
        )

    def test_owner_acceptance_needs_a_cited_decision(self):
        """Owner acceptance is gated on a decision, because the Plan has no 'accepted' state.

        The Plan's ladder has no state called ``accepted``. Owner acceptance is
        therefore supported by a decision at ``validated`` or above, which is a
        named scaffold decision rather than an invented evidence state.
        """
        self._expect(
            "owner_acceptance_without_decision",
            build_owner_acceptance_without_decision,
            "honest_status",
            "HONEST_STATUS: owner_acceptance is ACCEPTED without an explicit owner "
            "or reviewer decision record citing the programme",
        )

    def test_owner_acceptance_with_a_cited_decision_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = build_owner_acceptance_with_decision(Path(tmp) / "programme")
            code, payload, stderr = run_validator(package)
            self.assertEqual(code, 0, stderr + "\n" + json.dumps(payload, indent=2))
            status = json.loads(
                (package / "metadata" / "programme_status.json").read_text(encoding="utf-8")
            )
            self.assertEqual(status["owner_acceptance"], "ACCEPTED")
            # Acceptance of the records is still not an authorization.
            self.assertEqual(status["authorization_status"], "NOT_AUTHORIZED")

    def test_evidence_authorized_with_default_authorization_validates(self):
        """Reaching the top evidence state does not authorize anything.

        A package where a record sits at ``evidence_status: authorized``, backed
        by a cited owner decision, and still carries ``authorization_status:
        NOT_AUTHORIZED`` must validate.
        """
        with tempfile.TemporaryDirectory() as tmp:
            package = build_evidence_authorized_default_authorization(Path(tmp) / "programme")
            code, payload, stderr = run_validator(package)
            self.assertEqual(code, 0, stderr + "\n" + json.dumps(payload, indent=2))
            self.assertTrue(payload["ok"])
            research = json.loads(
                (package / "research" / "research_records.json").read_text(encoding="utf-8")
            )
            self.assertEqual(research[0]["evidence_status"], "authorized")
            self.assertEqual(research[0]["authorization_status"], "NOT_AUTHORIZED")

    def test_evidence_and_execution_outcome_confusion_fails(self):
        """A run outcome on the evidence axis, and an evidence state on the outcome axis.

        ``failed`` is a real execution outcome. ``documented`` is a real
        evidence state. Each is refused on the other's field, so an execution
        outcome can never silently replace the Plan's evidence terminology.
        """
        with tempfile.TemporaryDirectory() as tmp:
            package = build_evidence_outcome_confusion(Path(tmp) / "programme")
            code, payload, stderr = run_validator(package)
            self.assertNotEqual(code, 0)
            self.assertFalse(payload["ok"])
            # Traceability owns the finding. The strict schema enum also rejects
            # both bad values, and count_arithmetic cascades from that rejection,
            # so the assertion below is on the named reason rather than on
            # traceability being the only failing check.
            self.assertIn(
                "traceability",
                [item["check"] for item in payload["checks"] if item["outcome"] == "FAIL"],
                stderr,
            )
            reasons = _reasons(payload, "traceability")
            self.assertIn(
                "EXECUTION_OUTCOME_CONFUSED: RES-001 evidence_status 'failed' is an "
                "execution outcome",
                reasons,
            )
            self.assertIn(
                "EXECUTION_OUTCOME_CONFUSED: RES-001 execution_outcome 'documented' "
                "is an evidence state",
                reasons,
            )

    def test_executed_claim_without_execution_evidence_fails(self):
        self._expect(
            "executed_without_execution_evidence",
            build_executed_without_execution_evidence,
            "execution_evidence",
            "claims execution_outcome executed but has no execution evidence (exit_code)",
        )

    def test_runner_does_not_assign_authorization_from_evidence(self):
        runner = (
            ROOT / "templates" / "programme" / "simulations" / "run_one.py"
        ).read_text(encoding="utf-8")
        self.assertIn('authorization_status = "NOT_AUTHORIZED"', runner)
        self.assertNotIn("authorization_status = evidence_status", runner)
        validator = (ROOT / "tools" / "validate_programme.py").read_text(encoding="utf-8")
        self.assertNotIn("authorization_status = evidence_status", validator)
        self.assertNotRegex(validator, r"authorization_status\"\]\s*=\s*.*evidence_status")

    def _expect(self, _name: str, builder, check: str, reason: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = builder(Path(tmp) / "programme")
            code, payload, stderr = run_validator(package)
            self.assertNotEqual(code, 0)
            self.assertFalse(payload["ok"])
            self.assertEqual(
                _failing_check(payload), check, stderr + "\n" + json.dumps(payload, indent=2)
            )
            self.assertIn(reason, _reasons(payload, check))


class RepositoryScanTests(unittest.TestCase):
    """The four-digit ``UNI-`` scan is scoped to this repository only.

    A four-digit ``UNI-`` id is forbidden here because a separate register
    already uses ``UNI-001``..``UNI-015`` as collection-level ids and the
    collision was previously repaired to ``ULC-<tablet>-<clause>``.
    """

    def test_repository_root_is_derived_from_this_file_and_is_the_repository(self):
        self.assertEqual(REPO_ROOT, ROOT.parent)
        self.assertTrue((REPO_ROOT / "scaffold").is_dir())
        self.assertTrue((REPO_ROOT / "README.md").is_file())
        # The root is the repository itself, not a parent and not the scaffold.
        self.assertEqual((REPO_ROOT / ".git").parent, REPO_ROOT)
        self.assertNotEqual(REPO_ROOT, ROOT)
        self.assertNotEqual(REPO_ROOT, REPO_ROOT.parent)

    def test_the_scan_never_references_the_workspace_directory(self):
        """The scan root is the repository, never the wider workspace directory.

        The literal is assembled from parts so this module does not itself
        contain the path it forbids.
        """
        workspace_literal = "/" + "workspace"
        source = Path(__file__).read_text(encoding="utf-8")
        self.assertNotIn(workspace_literal, source)
        # And the scan function only ever reads the root it is given: no
        # module-level directory constant is consulted.
        import inspect

        parameters = inspect.signature(scan_four_digit_uni_ids).parameters
        self.assertEqual(list(parameters), ["root", "exclude"])
        self.assertIs(
            parameters["exclude"].default,
            None,
            "only the exclusion may default; the root must be passed in",
        )
        self.assertIs(parameters["root"].default, inspect.Parameter.empty)

    def test_repository_has_no_four_digit_uni_requirement_ids(self):
        offenders = scan_four_digit_uni_ids(REPO_ROOT, exclude=Path(__file__))
        self.assertEqual([path.as_posix() for path in offenders], [])

    def test_four_digit_uni_scan_does_not_report_its_own_definition(self):
        """The scan must not match the regular expression in its own module."""
        found = scan_four_digit_uni_ids(REPO_ROOT, exclude=Path(__file__))
        self.assertNotIn(Path(__file__).resolve(), found)
        # Control: without the exclusion the module matches its own pattern,
        # which is why the exclusion exists.
        control = scan_four_digit_uni_ids(REPO_ROOT)
        self.assertIn(Path(__file__).resolve(), control)

    def test_four_digit_uni_scan_finds_an_offender_inside_a_given_root(self):
        """Positive control: a temp root containing an offending file is reported."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            root.mkdir()
            (root / "notes.md").write_text("requirement UNI-0042 is wrong\n", encoding="utf-8")
            (root / "clean.md").write_text("requirement ULC-18-10 is fine\n", encoding="utf-8")
            found = scan_four_digit_uni_ids(root)
            self.assertEqual([path.name for path in found], ["notes.md"])

    def test_four_digit_uni_scan_ignores_files_outside_the_repository(self):
        """An unrelated file outside the repository cannot change its result.

        A file containing ``UNI-0001`` is written to a temporary directory that
        is explicitly not the repository root. The temp scan finds it, proving
        the pattern is live. The repository scan is unaffected and still finds
        zero offenders: that is the assertion Kyle asked for.
        """
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp).resolve()
            self.assertNotEqual(outside, REPO_ROOT)
            self.assertFalse(
                str(outside).startswith(str(REPO_ROOT) + "/"),
                "the control directory must be outside the repository",
            )
            (outside / "unrelated.md").write_text(
                "scratch note: UNI-0001\n", encoding="utf-8"
            )

            # Control: the same function does find the offender in its own root.
            self.assertEqual(
                [path.name for path in scan_four_digit_uni_ids(outside)],
                ["unrelated.md"],
            )

            # The repository's result must be unchanged by that file.
            self.assertEqual(
                [path.as_posix() for path in scan_four_digit_uni_ids(REPO_ROOT, exclude=Path(__file__))],
                [],
            )

    def test_four_digit_uni_scan_skips_caches_and_unscanned_suffixes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            (root / "__pycache__").mkdir(parents=True)
            (root / "kept.md").write_text("UNI-0099\n", encoding="utf-8")
            (root / "__pycache__" / "cached.md").write_text("UNI-0099\n", encoding="utf-8")
            (root / "binary.bin").write_text("UNI-0099\n", encoding="utf-8")
            found = scan_four_digit_uni_ids(root)
            self.assertEqual([path.name for path in found], ["kept.md"])


if __name__ == "__main__":
    unittest.main()
