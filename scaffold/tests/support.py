"""Build programme packages for validator tests.

These packages are fixtures for evidence discipline. They are not research
findings, and they do not authorize anything.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from new_programme import instantiate
from package_files import MANIFEST_REL, rebuild_locks, write_json, write_manifest
from validate_programme import (
    REQUIREMENT_LEDGER,
    RESEARCH_LEDGER,
    SIMULATION_LEDGER,
    environment_lock,
)

VALIDATOR = TOOLS / "validate_programme.py"
PROGRAMME_ID = "EXAMPLE-PROGRAMME"
EDITION = "0.0.0"
CLAUSE_ID = "EXAMPLE-TABLET-00.CLAUSE-01"
REQUIREMENT_ID = "ULC-00-01"


def run_validator(package: Path) -> tuple[int, dict, str]:
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), str(package)],
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"validator did not return JSON\nstdout={proc.stdout}\nstderr={proc.stderr}") from exc
    return proc.returncode, payload, proc.stderr


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: "" if row.get(column) is None else row.get(column) for column in columns})


def _research_record() -> dict:
    return {
        "record_id": "RES-001",
        "programme_unit_id": PROGRAMME_ID,
        "pass_type": "research",
        "checkpoint_id": "CP01",
        "objective_question": "Does the validator accept one consistent executed fixture?",
        "claim_class": "validator fixture",
        "relevant_dimensions": "none",
        "phase": "unassigned",
        "level": "unassigned",
        "method_summary": "Author a case expectation before recording a matching actual value.",
        "sources_or_inputs": "fixture: no external source",
        "assumptions": "Deterministic authored values. No external system.",
        "acceptance_or_falsification_criteria": "Acceptance: the recorded actual value equals the pre-authored expectation. Falsification: a different actual value falsifies the fixture match.",
        "actual_conditions": "Desktop fixture. No external system and no authorization.",
        "outcome_summary": "Fixture finding only. This is not a research result.",
        "raw_evidence_location": "results/SIM-001.json",
        "uncertainty_and_limitations": "Validator fixture. Not scientific validation, security certification, or production evidence.",
        "review_note": "No reviewer. Self-authored fixture.",
        "evidence_status": "executed",
        "authorization_status": "NOT_AUTHORIZED",
        "regression_links": "none",
        "open_obligations": "none",
        "simulation_link": "SIM-001",
        "programme_credit": "CANDIDATE_PENDING_OWNER_REVIEW",
        "clause_ids": [CLAUSE_ID],
        "release_classification": "PUBLICLY_CLEARED",
    }


def _case() -> dict:
    return {
        "id": "SIM-001",
        "research_record_id": "RES-001",
        "checkpoint_id": "CP01",
        "family": "fixture",
        "title": "Fixture match",
        "protocol_version": "PROGRAMME-FINITE-1",
        "configuration": "value=1",
        "input": {"value": 1},
        "expected": {"outcome": "RECORDED", "value": 1},
        "source_ids": [],
        "clause_ids": [CLAUSE_ID],
        "limitations": "Validator fixture. Not scientific validation, security certification, or production evidence.",
        "release_classification": "PUBLICLY_CLEARED",
    }


def _requirement() -> dict:
    return {
        "requirement_id": REQUIREMENT_ID,
        "objective_question": "Does the validator accept one consistent executed fixture?",
        "candidate_requirement": "Example placeholder requirement. Not a baselined requirement and not a corpus clause.",
        "research_record_id": "RES-001",
        "simulation_record_id": "SIM-001",
        "clause_id": CLAUSE_ID,
        "classification": "PROPOSED_NOT_BASELINED",
        "implementation": "NOT_STARTED",
        "production_validation": "NOT_PERFORMED",
        "evidence_status": "planned",
        "authorization_status": "NOT_AUTHORIZED",
        "programme_credit": "NONE",
        "release_classification": "PUBLICLY_CLEARED",
    }


def _research_row(record: dict) -> dict:
    row = {field: record.get(field, "") for field in RESEARCH_LEDGER}
    row["clause_ids"] = ";".join(record.get("clause_ids") or [])
    return row


def _simulation_row(result: dict) -> dict:
    row = {field: result.get(field, "") for field in SIMULATION_LEDGER}
    row["environment"] = environment_lock(result.get("environment"))
    row["exit_code"] = result.get("exit_code", "")
    row["duration_seconds"] = result.get("duration_seconds", "")
    return row


def _write_common_ledgers(root: Path, research: dict, requirement: dict, checkpoint: dict) -> None:
    _write_csv(root / "ledgers" / "research_ledger.csv", RESEARCH_LEDGER, [_research_row(research)])
    _write_csv(root / "ledgers" / "requirements.csv", REQUIREMENT_LEDGER, [requirement])
    _write_csv(
        root / "ledgers" / "checkpoint_schedule.csv",
        (
            "checkpoint",
            "name",
            "required_research",
            "recorded_desktop_assessments",
            "required_simulations",
            "executed_simulations",
            "matched_expectations",
            "owner_accepted_research_credits",
            "owner_accepted_simulation_credits",
            "status",
        ),
        [checkpoint],
    )
    _write_csv(
        root / "ledgers" / "dimensions.csv",
        ("dimension", "assessment", "evidence_families", "limit", "status", "simulation_ids"),
        [
            {
                "dimension": "DIM-FIXTURE",
                "assessment": "Fixture axis only.",
                "evidence_families": "fixture",
                "limit": "Not a claim.",
                "status": "RECORDED_NOT_CREDITED",
                "simulation_ids": "SIM-001",
            }
        ],
    )
    _write_csv(
        root / "ledgers" / "levels.csv",
        ("level", "disposition", "reason", "owner_decision", "simulation_ids"),
        [
            {
                "level": "LVL-FIXTURE",
                "disposition": "RECORDED_NOT_CREDITED",
                "reason": "A level name is not a capability.",
                "owner_decision": "PENDING",
                "simulation_ids": "SIM-001",
            }
        ],
    )
    _write_csv(
        root / "ledgers" / "model_family_summary.csv",
        ("family", "configurations", "completed", "expectations_matched", "scope"),
        [
            {
                "family": "fixture",
                "configurations": 1,
                "completed": 1,
                "expectations_matched": 1,
                "scope": "FINITE_AUTHORED_FIXTURE_NOT_A_VALIDATION",
            }
        ],
    )


def build_empty(dest: Path) -> Path:
    return instantiate(dest, PROGRAMME_ID, EDITION)


def build_executed(dest: Path) -> Path:
    root = instantiate(dest, PROGRAMME_ID, EDITION)
    (root / "simulations" / "model.py").write_text(
        "def run_case(case):\n"
        '    return {"outcome": "RECORDED", "value": case["input"]["value"]}\n',
        encoding="utf-8",
    )
    research = _research_record()
    case = _case()
    requirement = _requirement()
    write_json(root / "research" / "research_records.json", [research])
    write_json(root / "simulations" / "scenarios.json", [case])
    write_json(
        root / "clauses" / "clause_references.json",
        [
            {
                "clause_id": CLAUSE_ID,
                "tablet_number": 0,
                "clause_number": 1,
                "side": "unspecified",
                "placeholder": True,
                "note": "Example placeholder. Not a corpus clause.",
                "release_classification": "PUBLICLY_CLEARED",
            }
        ],
    )
    write_json(root / "requirements" / "requirements.json", [requirement])
    (root / "research" / "RES-001.md").write_text(
        "# RES-001\n\nFixture card. Not a research finding. authorization_status is NOT_AUTHORIZED.\n",
        encoding="utf-8",
    )
    command = [
        sys.executable,
        str(root / "simulations" / "run_one.py"),
        "--case",
        "SIM-001",
        "--output",
        str(root / "results" / "SIM-001.json"),
    ]
    proc = subprocess.run(command, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"fixture execution failed\nstdout={proc.stdout}\nstderr={proc.stderr}")
    result = json.loads((root / "results" / "SIM-001.json").read_text(encoding="utf-8"))
    write_json(
        root / "results" / "execution_log.json",
        [
            {
                "id": "SIM-001",
                "command": command,
                "exit_code": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
        ],
    )
    _write_csv(root / "ledgers" / "simulation_ledger.csv", SIMULATION_LEDGER, [_simulation_row(result)])
    checkpoint = {
        "checkpoint": "CP01",
        "name": "Example checkpoint",
        "required_research": 1,
        "recorded_desktop_assessments": 1,
        "required_simulations": 1,
        "executed_simulations": 1,
        "matched_expectations": 1 if result.get("outcome") == "PASS" else 0,
        "owner_accepted_research_credits": 0,
        "owner_accepted_simulation_credits": 0,
        "status": "RECORDS_PRESENT_REVIEW_PENDING",
    }
    _write_common_ledgers(root, research, requirement, checkpoint)
    status = json.loads((root / "metadata" / "programme_status.json").read_text(encoding="utf-8"))
    status.update(
        {
            "research_records": 1,
            "simulation_cases": 1,
            "simulation_results": 1,
            "requirements": 1,
            "expectations_matched": 1 if result.get("outcome") == "PASS" else 0,
            "expectation_failures": 1 if result.get("outcome") == "FAIL" else 0,
            "execution_errors": 1 if result.get("outcome") == "ERROR" else 0,
        }
    )
    write_json(root / "metadata" / "programme_status.json", status)
    rebuild_locks(root)
    return root


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, payload) -> None:
    write_json(path, payload)


def build_wrong_hash(dest: Path) -> Path:
    root = build_empty(dest)
    manifest = _load(root / MANIFEST_REL)
    manifest["README.md"] = "0" * 64
    _save(root / MANIFEST_REL, manifest)
    return root


def build_duplicate_id(dest: Path) -> Path:
    root = build_empty(dest)
    _save(
        root / "sources" / "source_register.json",
        [
            {
                "id": "SRC-001",
                "kind": "fixture",
                "review_scope": "Fixture source. Nothing was reviewed.",
                "release_classification": "PUBLICLY_CLEARED",
            },
            {
                "id": "SRC-001",
                "kind": "fixture",
                "review_scope": "Duplicate fixture source.",
                "release_classification": "PUBLICLY_CLEARED",
            },
        ],
    )
    write_manifest(root)
    return root


def build_unclassified(dest: Path) -> Path:
    root = build_empty(dest)
    notes = root / "notes"
    notes.mkdir()
    (notes / "stray.txt").write_text("unclassified fixture\n", encoding="utf-8")
    write_manifest(root)
    return root


def build_altered_expected(dest: Path) -> Path:
    root = build_executed(dest)
    result_path = root / "results" / "SIM-001.json"
    result = _load(result_path)
    result["expected"] = {"outcome": "RECORDED", "value": 2}
    _save(result_path, result)
    write_manifest(root)
    return root


def build_self_credit(dest: Path) -> Path:
    root = build_executed(dest)
    research_path = root / "research" / "research_records.json"
    research = _load(research_path)
    research[0]["programme_credit"] = "AWARDED"
    _save(research_path, research)
    _replace_ledger_field(root / "ledgers" / "research_ledger.csv", "programme_credit", "AWARDED")
    _replace_ledger_field(root / "ledgers" / "checkpoint_schedule.csv", "owner_accepted_research_credits", "1")
    status = _load(root / "metadata" / "programme_status.json")
    status["owner_acceptance"] = "ACCEPTED"
    status["owner_accepted_research_credits"] = 1
    _save(root / "metadata" / "programme_status.json", status)
    write_manifest(root)
    return root


def build_accepted_without_decision(dest: Path) -> Path:
    root = build_executed(dest)
    research_path = root / "research" / "research_records.json"
    research = _load(research_path)
    research[0]["evidence_status"] = "accepted"
    _save(research_path, research)
    _replace_ledger_field(root / "ledgers" / "research_ledger.csv", "evidence_status", "accepted")
    write_manifest(root)
    return root


def build_authorization_without_record(dest: Path) -> Path:
    root = build_executed(dest)
    research_path = root / "research" / "research_records.json"
    research = _load(research_path)
    research[0]["authorization_status"] = "AUTHORIZED"
    _save(research_path, research)
    _replace_ledger_field(root / "ledgers" / "research_ledger.csv", "authorization_status", "AUTHORIZED")
    write_manifest(root)
    return root


def _replace_ledger_field(path: Path, field: str, value: str) -> None:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    for row in rows:
        row[field] = value
    _write_csv(path, tuple(fieldnames), rows)


def build_fixture(kind: str, dest: Path) -> Path:
    if dest.exists():
        import shutil

        shutil.rmtree(dest)
    builders = {
        "valid_empty": build_empty,
        "valid_executed": build_executed,
        "wrong_hash": build_wrong_hash,
        "duplicate_id": build_duplicate_id,
        "unclassified": build_unclassified,
        "altered_expected": build_altered_expected,
        "self_credit": build_self_credit,
        "accepted_without_decision": build_accepted_without_decision,
        "authorization_without_record": build_authorization_without_record,
    }
    if kind not in builders:
        raise SystemExit(f"unknown fixture {kind}")
    return builders[kind](dest)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: support.py <fixture-kind> <destination>", file=sys.stderr)
        sys.exit(2)
    print(build_fixture(sys.argv[1], Path(sys.argv[2])))
