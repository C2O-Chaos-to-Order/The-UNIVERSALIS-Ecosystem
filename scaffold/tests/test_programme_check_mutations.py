"""Break a package once per check, and require that check to be the one that fires.

A check named in a test proves only that the name exists. This suite takes a
freshly generated, passing package and applies exactly one defect of the kind
each check exists to catch, then requires that check's outcome to be FAIL. A
check that quietly stopped working would leave the package passing and this
suite would fail.

These mutations are authored defects in validator fixtures. They are not
research findings and they establish nothing about any scientific claim.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from support import build_empty, run_validator


def _load(path: Path):
    text = path.read_text(encoding="utf-8").strip()
    return json.loads(text) if text else []


def _save(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _relock(package: Path) -> None:
    """Re-hash the manifest so a mutation trips only its intended check.

    Each mutation changes a file the manifest covers. Without this, every
    mutation would also fail manifest_integrity and the test could not tell
    which check caught it.
    """
    manifest_path = package / "metadata" / "sha256_manifest.json"
    manifest = _load(manifest_path)
    for relative in list(manifest):
        target = package / relative
        if target.is_file():
            manifest[relative] = hashlib.sha256(target.read_bytes()).hexdigest()
    _save(manifest_path, manifest)


def _status(package: Path, **fields) -> None:
    path = package / "metadata" / "programme_status.json"
    status = _load(path)
    status.update(fields)
    _save(path, status)
    _relock(package)


class ProgrammeCheckMutationTests(unittest.TestCase):
    """One mutation per check, asserting that check specifically fails."""

    def _assert_caught(self, mutate, check: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            package = build_empty(Path(tmp) / "package")
            baseline_code, baseline, _ = run_validator(package)
            self.assertEqual(
                baseline_code, 0, "the fixture package must pass before it is mutated"
            )
            mutate(package)
            code, payload, stderr = run_validator(package)
            outcomes = {item["check"]: item["outcome"] for item in payload["checks"]}
            self.assertEqual(
                outcomes.get(check),
                "FAIL",
                f"{check} did not fail after its mutation; outcomes were {outcomes}\n{stderr}",
            )
            self.assertEqual(code, 1, "a failed check must exit 1")
            return outcomes

    def test_manifest_integrity_catches_an_edited_file(self):
        def mutate(package: Path) -> None:
            readme = package / "README.md"
            readme.write_text(readme.read_text(encoding="utf-8") + "\n", encoding="utf-8")

        self._assert_caught(mutate, "manifest_integrity")

    def test_traceability_catches_a_case_citing_an_unregistered_source(self):
        def mutate(package: Path) -> None:
            path = package / "simulations" / "scenarios.json"
            cases = _load(path)
            cases.append(
                {
                    "id": "SIM-900",
                    "research_record_id": "RES-900",
                    "clause_ids": ["ULC-99-99"],
                    "source_ids": ["SRC-DOES-NOT-EXIST"],
                    "expectation": "authored fixture",
                    "limitations": "authored fixture",
                    "release_classification": "PUBLICLY_CLEARED",
                }
            )
            _save(path, cases)
            _relock(package)

        self._assert_caught(mutate, "traceability")

    def test_execution_evidence_catches_a_fabricated_execution(self):
        """A logged run with a made-up hash and no matching case must not pass."""

        def mutate(package: Path) -> None:
            path = package / "results" / "execution_log.json"
            results = _load(path)
            results.append(
                {
                    "record_id": "SIM-901",
                    "simulation_id": "SIM-901",
                    "outcome": "PASS",
                    "evidence_status": "tested",
                    "execution_outcome": "executed",
                    "execution_timestamp": "2026-10-31T12:00:00-05:00",
                    "expectation_matched": True,
                    "code_sha256": "0" * 64,
                }
            )
            _save(path, results)
            _relock(package)

        self._assert_caught(mutate, "execution_evidence")

    def test_count_arithmetic_catches_a_count_with_nothing_behind_it(self):
        def mutate(package: Path) -> None:
            _status(package, simulation_results=5)

        self._assert_caught(mutate, "count_arithmetic")

    def test_honest_status_catches_acceptance_claimed_by_the_author(self):
        def mutate(package: Path) -> None:
            _status(package, owner_acceptance="ACCEPTED", programme_complete=True)

        self._assert_caught(mutate, "honest_status")

    def test_honest_status_catches_self_authorized_release(self):
        def mutate(package: Path) -> None:
            _status(package, release_authorized=True)

        self._assert_caught(mutate, "honest_status")

    def test_classification_gate_catches_a_missing_classification(self):
        def mutate(package: Path) -> None:
            path = package / "metadata" / "classifications.json"
            classifications = _load(path)
            classifications.pop("README.md")
            _save(path, classifications)
            _relock(package)

        self._assert_caught(mutate, "classification_gate")

    def test_every_check_has_a_mutation_that_trips_it(self):
        """Guard: a new check must not arrive without something that breaks it."""
        with tempfile.TemporaryDirectory() as tmp:
            package = build_empty(Path(tmp) / "package")
            _, payload, _ = run_validator(package)
        names = {item["check"] for item in payload["checks"]}
        covered = {
            "manifest_integrity",
            "traceability",
            "execution_evidence",
            "expectation_discipline",
            "count_arithmetic",
            "honest_status",
            "classification_gate",
        }
        self.assertLessEqual(
            names,
            covered,
            "a check exists with no mutation test here: "
            + ", ".join(sorted(names - covered)),
        )
