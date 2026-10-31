"""Execute one authored case in this process and write an evidence record.

The expected outcome is read from the case file. It is not edited to fit the
output. evidence_status records the execution. authorization_status is always
NOT_AUTHORIZED. This script does not award programme credit.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

TOOL_SETTABLE = frozenset({"planned", "executed", "failed", "incomplete", "reproduced"})
COPY_FIELDS = (
    "programme_unit_id",
    "checkpoint_id",
    "objective_question",
    "claim_class",
    "relevant_dimensions",
    "phase",
    "level",
    "method_summary",
    "sources_or_inputs",
    "assumptions",
    "acceptance_or_falsification_criteria",
    "regression_links",
    "open_obligations",
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_model(path: Path):
    spec = importlib.util.spec_from_file_location("programme_model", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one simulation case and write its evidence record.")
    parser.add_argument("--case", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    scenarios_path = root / "simulations" / "scenarios.json"
    code_path = root / "simulations" / "model.py"
    cases = load_json(scenarios_path)
    case = next((item for item in cases if item.get("id") == args.case), None)
    if case is None:
        print(f"CASE_ABSENT: {args.case}", file=sys.stderr)
        return 2
    research_records = load_json(root / "research" / "research_records.json")
    research = next(
        (item for item in research_records if item.get("record_id") == case.get("research_record_id")),
        None,
    )
    if research is None:
        print(
            f"RESEARCH_RECORD_ABSENT: {case.get('research_record_id')}",
            file=sys.stderr,
        )
        return 2
    code_hash = sha256_file(code_path)
    fixtures_hash = sha256_file(scenarios_path)
    started = datetime.now(timezone.utc)
    clock = time.perf_counter()
    try:
        model = load_model(code_path)
        actual = model.run_case(case)
        matched = actual == case.get("expected")
        execution_status = "COMPLETED"
        outcome = "PASS" if matched else "FAIL"
        error = None
        evidence_status = "executed" if matched else "failed"
    except Exception as exc:
        actual = None
        matched = False
        execution_status = "ERROR"
        outcome = "ERROR"
        error = f"{type(exc).__name__}: {exc}"
        evidence_status = "failed"
    if evidence_status not in TOOL_SETTABLE:
        print(
            f"tooling cannot set evidence state {evidence_status!r}; "
            "reviewed, accepted and authorized require an explicit owner or reviewer decision record",
            file=sys.stderr,
        )
        return 2
    # Separate column. Never derived from evidence_status.
    authorization_status = "NOT_AUTHORIZED"
    ended = datetime.now(timezone.utc)
    record = {field: research.get(field, "") for field in COPY_FIELDS}
    record.update(
        {
            "record_id": case["id"],
            "pass_type": "simulation",
            "research_record_id": research["record_id"],
            "actual_conditions": "Separate subprocess. No network. No authorization.",
            "outcome_summary": json.dumps(
                {"expectation_matched": matched, "actual": actual},
                sort_keys=True,
                default=str,
            ),
            "raw_evidence_location": f"results/{case['id']}.json",
            "uncertainty_and_limitations": case.get("limitations")
            or research.get("uncertainty_and_limitations")
            or "Limitations were not stated on the case.",
            "review_note": "Runner record only. No review performed. authorization_status remains NOT_AUTHORIZED.",
            "evidence_status": evidence_status,
            "authorization_status": authorization_status,
            "protocol_version": case["protocol_version"],
            "configuration": case["configuration"],
            "environment": {
                "python": " ".join(sys.version.split()),
                "platform": platform.platform(),
            },
            "input": case.get("input"),
            "expected": case.get("expected"),
            "actual": actual,
            "expectation_matched": matched,
            "execution_status": execution_status,
            "outcome": outcome,
            "error": error,
            "started_at": started.isoformat(),
            "ended_at": ended.isoformat(),
            "duration_seconds": time.perf_counter() - clock,
            "exit_code": 0 if outcome == "PASS" else 1,
            "code_path": "simulations/model.py",
            "code_sha256": code_hash,
            "fixtures_sha256": fixtures_hash,
            "programme_credit": "CANDIDATE_PENDING_OWNER_REVIEW",
            "independent_review": "NOT_PERFORMED",
            "randomness": "none",
            "release_classification": "PUBLICLY_CLEARED",
        }
    )
    destination = Path(args.output)
    if not destination.is_absolute():
        destination = Path.cwd() / destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"id": case["id"], "outcome": outcome, "execution_status": execution_status}))
    return 0 if outcome == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
