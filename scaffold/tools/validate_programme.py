"""Validate the internal consistency of a programme package.

A passing run proves that the manifest, links, recorded execution fields,
expectation lock, counts, status claims, and release classifications agree.
It does not re-execute simulations, award programme credit, or establish that
a finding is true, reviewed, accepted, certified, or authorized.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from evidence_states import (
    DECISION_REQUIRED,
    EXECUTION_OUTCOMES,
    PROGRAMME_CREDITS,
    STATES,
    assert_authorization_status,
    assert_programme_credit,
    authorization_record_supports,
    cross_axis_problems,
    decision_supports,
    require_state_authority,
    EvidenceStateError,
)
from package_files import (
    CLASSIFICATION_REL,
    MANIFEST_REL,
    PUBLIC_CLASSIFICATION,
    iter_package_files,
    package_relative_paths,
    relative_posix,
    sha256_file,
)

CHECKS = (
    "manifest_integrity",
    "traceability",
    "execution_evidence",
    "expectation_discipline",
    "count_arithmetic",
    "honest_status",
    "classification_gate",
)

SCOPE = (
    "Package evidence-discipline consistency only. A passing validation proves "
    "the manifest, links, recorded execution fields, expectation lock, counts, "
    "status claims, and release classifications agree. It does not prove that "
    "a finding is true, that an oracle is the right oracle, that a human "
    "reviewed or accepted the work, or that anything is scientifically "
    "validated, security-certified, production-ready, or authorized for "
    "release. The validator does not re-execute simulations and does not "
    "award programme credit."
)

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"
HASH64 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
FORBIDDEN_PRODUCTION = frozenset(
    {
        "PASSED",
        "PASS",
        "CERTIFIED",
        "VALIDATED",
        "PRODUCTION_READY",
        "COMPLETE",
        "APPROVED",
        "PERFORMED",
    }
)
# Results at ``independently_reproduced`` or beyond have been reproduced by
# someone other than the author. ``verified`` alone has not.
LATER_THAN_REPRODUCED = frozenset(
    {"independently_reproduced", "validated", "authorized"}
)
# Evidence states that a single run may not claim on its own authority.
DECISION_GATED_LABEL = ", ".join(
    state for state in STATES if state in DECISION_REQUIRED
)
CLAUSE_BODY_KEYS = frozenset({"body", "clause_text", "text", "title", "clause_title"})

# Governing Plan evidence-record fields, in Plan order. These names are the
# contract. evidence_status and authorization_status stay separate columns.
PLAN_EVIDENCE_FIELDS = (
    "record_id",
    "programme_unit_id",
    "pass_type",
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
    "actual_conditions",
    "outcome_summary",
    "raw_evidence_location",
    "uncertainty_and_limitations",
    "review_note",
    "evidence_status",
    "authorization_status",
    "regression_links",
    "open_obligations",
)
# The four Plan simulation-pass fields are required on every simulation
# result. started_at, ended_at, duration_seconds and exit_code are extra
# execution detail and do not replace execution_timestamp.
SIMULATION_PASS_FIELDS = (
    "protocol_version",
    "configuration",
    "environment",
    "execution_timestamp",
    "failure_policy",
    "known_answer_check",
    "mcse_or_precision_note",
)
# Plan values for pass_type. Structure (directory and ledger names) keeps the
# word simulation; the pass_type value does not.
PASS_TYPE_RESEARCH = "research"
PASS_TYPE_EXECUTED_SIMULATION = "executed_simulation"
PASS_TYPE_VALUES = frozenset({PASS_TYPE_RESEARCH, PASS_TYPE_EXECUTED_SIMULATION})
EXECUTION_OUTCOME_VALUES = frozenset(EXECUTION_OUTCOMES)
NAIVE_TIMESTAMP = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}(:[0-9]{2}(\.[0-9]+)?)?$"
)
ULC_REQUIREMENT_ID = re.compile(r"^ULC-[0-9]{2}-[0-9]{2}$")
# Collection-level ids use a different register. They are not programme requirements.
OTHER_REGISTER_ID = re.compile(r"^UNI-[0-9]{3,4}$")

RESEARCH_LEDGER = PLAN_EVIDENCE_FIELDS + (
    "execution_outcome",
    "simulation_link",
    "programme_credit",
    "clause_ids",
    "release_classification",
)
SIMULATION_LEDGER = PLAN_EVIDENCE_FIELDS + ("execution_outcome",) + SIMULATION_PASS_FIELDS + (
    "research_record_id",
    "execution_status",
    "outcome",
    "started_at",
    "ended_at",
    "duration_seconds",
    "exit_code",
    "code_path",
    "code_sha256",
    "fixtures_sha256",
    "programme_credit",
    "independent_review",
    "release_classification",
)
CHECKPOINT_LEDGER = (
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
)
REQUIREMENT_LEDGER = (
    "requirement_id",
    "objective_question",
    "candidate_requirement",
    "research_record_id",
    "simulation_record_id",
    "clause_id",
    "classification",
    "implementation",
    "production_validation",
    "evidence_status",
    "authorization_status",
    "programme_credit",
    "release_classification",
)
COVERAGE_LEDGERS = {
    "ledgers/dimensions.csv": ("dimension", "assessment", "evidence_families", "limit", "status", "simulation_ids"),
    "ledgers/levels.csv": ("level", "disposition", "reason", "owner_decision", "simulation_ids"),
    "ledgers/phases.csv": ("phase", "application", "status", "simulation_ids"),
    "ledgers/relationships.csv": ("first", "second", "question", "assessment", "status", "simulation_ids"),
    "ledgers/report_index.csv": ("report_id", "path", "title", "research_ids", "simulation_ids"),
    "ledgers/model_family_summary.csv": (
        "family",
        "configurations",
        "completed",
        "expectations_matched",
        "scope",
    ),
}


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and (
        not isinstance(value, float) or math.isfinite(value)
    )


def nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def split_ids(value: object) -> list[str]:
    if value is None:
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def evidence_record_id(record: dict) -> str:
    value = record.get("record_id")
    return value if isinstance(value, str) else ""


def environment_lock(environment: object) -> str:
    """Render the simulation ``environment`` column. Does not read evidence_status."""
    if not isinstance(environment, dict):
        return ""
    return f"python={environment.get('python', '')};platform={environment.get('platform', '')}"


def safe_relative(name: object) -> bool:
    if not isinstance(name, str) or not name or name.startswith(("/", "\\")):
        return False
    path = Path(name)
    return not path.is_absolute() and ".." not in path.parts and "\\" not in name


def parse_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def matches_type(value: object, types: list[str]) -> bool:
    checks = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "boolean": lambda item: isinstance(item, bool),
        "integer": is_int,
        "number": is_number,
        "null": lambda item: item is None,
    }
    return any(checks[name](value) for name in types if name in checks)


def schema_problems(instance: object, schema: dict, label: str) -> list[str]:
    problems: list[str] = []

    def walk(value: object, node: dict, path: str) -> None:
        if "const" in node and value != node["const"]:
            problems.append(f"SCHEMA: {path} must be {node['const']!r}")
            return
        if "enum" in node and value not in node["enum"]:
            problems.append(f"SCHEMA: {path} value {value!r} is not allowed")
            return
        declared = node.get("type")
        types = [declared] if isinstance(declared, str) else list(declared or [])
        if types and not matches_type(value, types):
            problems.append(f"SCHEMA: {path} has the wrong type")
            return
        if isinstance(value, str):
            minimum = node.get("minLength")
            if isinstance(minimum, int) and len(value) < minimum:
                problems.append(f"SCHEMA: {path} is empty or too short")
            pattern = node.get("pattern")
            if isinstance(pattern, str) and re.fullmatch(pattern, value) is None:
                problems.append(f"SCHEMA: {path} does not match the required pattern")
        if is_number(value) and "minimum" in node and value < node["minimum"]:
            problems.append(f"SCHEMA: {path} is below the minimum")
        if "object" in types and isinstance(value, dict):
            for key in node.get("required", []):
                if key not in value:
                    problems.append(f"SCHEMA: {path} missing required field {key}")
            properties = node.get("properties") or {}
            for key, subschema in properties.items():
                if key in value and isinstance(subschema, dict):
                    walk(value[key], subschema, f"{path}.{key}")
        if "array" in types and isinstance(value, list):
            item_schema = node.get("items")
            if isinstance(item_schema, dict):
                for index, item in enumerate(value):
                    walk(item, item_schema, f"{path}[{index}]")

    walk(instance, schema, label)
    return problems


def load_json(path: Path) -> tuple[object | None, str | None]:
    if not path.is_file():
        return None, f"missing required file {path.as_posix()}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"{path.as_posix()} is not valid JSON ({exc.msg})"


def read_csv(path: Path, columns: tuple[str, ...]) -> tuple[list[dict] | None, str | None]:
    if not path.is_file():
        return None, f"missing required file {path.as_posix()}"
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        missing = [column for column in columns if column not in fieldnames]
        if missing:
            return None, f"{path.as_posix()} is missing columns: {', '.join(missing)}"
        rows = []
        for row in reader:
            if not any((value or "").strip() for value in row.values() if value is not None):
                continue
            rows.append(row)
    return rows, None


def duplicates_within(identifiers: list[str], label: str) -> list[str]:
    reasons = []
    for identifier, count in Counter(identifiers).items():
        if identifier and count > 1:
            reasons.append(
                f"DUPLICATE_IDENTIFIER: {identifier} appears more than once in {label}"
            )
    return reasons


def cross_identifier_collisions(groups: list[tuple[str, set[str]]]) -> list[str]:
    owners: dict[str, str] = {}
    reasons = []
    for entity_type, identifiers in groups:
        for identifier in sorted(identifiers):
            previous = owners.get(identifier)
            if previous is None:
                owners[identifier] = entity_type
            elif previous != entity_type:
                reasons.append(
                    f"DUPLICATE_IDENTIFIER: {identifier} is used as {previous} and {entity_type}"
                )
    return reasons


def report_paths(root: Path) -> list[str]:
    reports = root / "reports"
    if not reports.is_dir():
        return []
    found = []
    for path in sorted(reports.glob("*.md")):
        if path.name.startswith("_TEMPLATE") or path.name == "README.md":
            continue
        found.append(relative_posix(root, path))
    return found


def check_manifest(root: Path, files: list[str], reasons: dict[str, list[str]]) -> None:
    bucket = reasons["manifest_integrity"]
    loaded, error = load_json(root / MANIFEST_REL)
    if error:
        bucket.append(f"MANIFEST_INTEGRITY: {error}")
        return
    if not isinstance(loaded, dict):
        bucket.append("MANIFEST_INTEGRITY: manifest must be a JSON object of relative path to SHA-256")
        return
    actual = {name for name in files if name != MANIFEST_REL}
    declared = set(loaded)
    for name in sorted(actual - declared):
        bucket.append(f"MANIFEST_INTEGRITY: manifest is missing {name}")
    for name in sorted(declared - actual):
        if not safe_relative(name):
            bucket.append(f"MANIFEST_INTEGRITY: manifest path is not a relative package path: {name}")
        else:
            bucket.append(f"MANIFEST_INTEGRITY: manifest contains extra path {name}")
    for name, digest in loaded.items():
        if not safe_relative(name):
            if name not in declared - actual:
                bucket.append(f"MANIFEST_INTEGRITY: manifest path is not a relative package path: {name}")
            continue
        if name not in actual:
            continue
        if not isinstance(digest, str) or HASH64.fullmatch(digest) is None:
            bucket.append(f"MANIFEST_INTEGRITY: hash for {name} is not a lowercase SHA-256 digest")
            continue
        if sha256_file(root / name) != digest:
            bucket.append(f"MANIFEST_INTEGRITY: hash mismatch for {name}")


def records_from_schema(
    payload: object,
    schema: dict,
    label: str,
    reasons: list[str],
) -> list[dict] | None:
    if not isinstance(payload, list):
        reasons.append(f"SCHEMA: {label} must be a JSON array")
        return None
    items = schema.get("items") if schema.get("type") == "array" else schema
    if not isinstance(items, dict):
        items = schema
    ok = True
    for index, record in enumerate(payload):
        problems = schema_problems(record, items, f"{label}[{index}]")
        if problems:
            reasons.extend(problems)
            ok = False
    if not ok:
        return None
    return payload


def load_package(root: Path, reasons: dict[str, list[str]]) -> dict:
    """Load package JSON and ledgers. File errors stay on the check that owns them."""
    data: dict = {
        # Raw payloads as parsed, before schema acceptance. The evidence/outcome
        # cross-axis check reads these so a record that fails schema validation
        # still yields the specific confusion finding rather than only a
        # generic "value is not allowed".
        "raw_research": [],
        "raw_results": [],
        "research": [],
        "cases": [],
        "results": [],
        "requirements": [],
        "sources": [],
        "clauses": [],
        "decisions": [],
        "status": None,
        "log": [],
        "ledgers": {},
        "ready": True,
    }
    research_schema = load_schema("research_record.schema.json")
    case_schema = load_schema("simulation_case.schema.json")
    result_schema = load_schema("simulation_result.schema.json")
    requirement_schema = load_schema("requirement_record.schema.json")
    clause_schema = load_schema("clause_reference.schema.json")
    source_schema = load_schema("source_register_entry.schema.json")
    status_schema = load_schema("programme_status.schema.json")

    research_payload, error = load_json(root / "research" / "research_records.json")
    if error:
        reasons["traceability"].append(f"TRACEABILITY: {error}")
        data["ready"] = False
    else:
        if isinstance(research_payload, list):
            data["raw_research"] = [item for item in research_payload if isinstance(item, dict)]
        research = records_from_schema(
            research_payload,
            {"type": "array", "items": research_schema},
            "research/research_records.json",
            reasons["traceability"],
        )
        if research is None:
            data["ready"] = False
        else:
            data["research"] = research

    case_payload, error = load_json(root / "simulations" / "scenarios.json")
    if error:
        reasons["traceability"].append(f"TRACEABILITY: {error}")
        reasons["expectation_discipline"].append(f"EXPECTATION_MISMATCH: {error}")
        data["ready"] = False
    else:
        cases = records_from_schema(
            case_payload,
            {"type": "array", "items": case_schema},
            "simulations/scenarios.json",
            reasons["traceability"],
        )
        if cases is None:
            data["ready"] = False
        else:
            data["cases"] = cases

    log_payload, error = load_json(root / "results" / "execution_log.json")
    if error:
        reasons["execution_evidence"].append(f"EXECUTION_EVIDENCE: {error}")
        data["ready"] = False
    elif not isinstance(log_payload, list):
        reasons["execution_evidence"].append("EXECUTION_EVIDENCE: results/execution_log.json must be a JSON array")
        data["ready"] = False
    else:
        data["log"] = log_payload

    result_files = sorted((root / "results").glob("SIM-*.json")) if (root / "results").is_dir() else []
    results = []
    raw_results = []
    result_ok = True
    for path in result_files:
        payload, error = load_json(path)
        rel = relative_posix(root, path)
        if error or not isinstance(payload, dict):
            reasons["execution_evidence"].append(f"EXECUTION_EVIDENCE: {rel} is not a JSON object")
            result_ok = False
            continue
        raw_results.append(payload)
        problems = schema_problems(payload, result_schema, rel)
        if problems:
            reasons["execution_evidence"].extend(
                f"EXECUTION_EVIDENCE: {problem}" for problem in problems
            )
            result_ok = False
        results.append(payload)
    if not result_ok:
        data["ready"] = False
    data["results"] = results
    data["raw_results"] = raw_results

    requirement_payload, error = load_json(root / "requirements" / "requirements.json")
    if error:
        reasons["traceability"].append(f"TRACEABILITY: {error}")
        data["ready"] = False
    else:
        requirements = records_from_schema(
            requirement_payload,
            {"type": "array", "items": requirement_schema},
            "requirements/requirements.json",
            reasons["traceability"],
        )
        if requirements is None:
            data["ready"] = False
        else:
            data["requirements"] = requirements

    source_payload, error = load_json(root / "sources" / "source_register.json")
    if error:
        reasons["traceability"].append(f"TRACEABILITY: {error}")
        data["ready"] = False
    else:
        sources = records_from_schema(
            source_payload,
            {"type": "array", "items": source_schema},
            "sources/source_register.json",
            reasons["traceability"],
        )
        if sources is None:
            data["ready"] = False
        else:
            data["sources"] = sources

    clause_payload, error = load_json(root / "clauses" / "clause_references.json")
    if error:
        reasons["traceability"].append(f"TRACEABILITY: {error}")
        data["ready"] = False
    else:
        clauses = records_from_schema(
            clause_payload,
            {"type": "array", "items": clause_schema},
            "clauses/clause_references.json",
            reasons["traceability"],
        )
        if clauses is None:
            data["ready"] = False
        else:
            data["clauses"] = clauses

    status_payload, error = load_json(root / "metadata" / "programme_status.json")
    if error:
        reasons["honest_status"].append(f"HONEST_STATUS: {error}")
        data["ready"] = False
    elif not isinstance(status_payload, dict):
        reasons["honest_status"].append("HONEST_STATUS: metadata/programme_status.json must be a JSON object")
        data["ready"] = False
    else:
        problems = schema_problems(status_payload, status_schema, "metadata/programme_status.json")
        if problems:
            reasons["honest_status"].extend(f"HONEST_STATUS: {problem}" for problem in problems)
            data["ready"] = False
        else:
            data["status"] = status_payload

    decision_dir = root / "decisions"
    if decision_dir.is_dir():
        for path in sorted(decision_dir.glob("*.json")):
            payload, error = load_json(path)
            rel = relative_posix(root, path)
            if error or not isinstance(payload, dict):
                reasons["traceability"].append(f"TRACEABILITY: {rel} is not a JSON decision object")
                data["ready"] = False
                continue
            data["decisions"].append(payload)

    ledger_specs = {
        "research": (root / "ledgers" / "research_ledger.csv", RESEARCH_LEDGER),
        "simulation": (root / "ledgers" / "simulation_ledger.csv", SIMULATION_LEDGER),
        "checkpoint": (root / "ledgers" / "checkpoint_schedule.csv", CHECKPOINT_LEDGER),
        "requirements": (root / "ledgers" / "requirements.csv", REQUIREMENT_LEDGER),
    }
    for key, (path, columns) in ledger_specs.items():
        rows, error = read_csv(path, columns)
        if error:
            reasons["count_arithmetic"].append(f"COUNT_ARITHMETIC: {error}")
            data["ready"] = False
        else:
            data["ledgers"][key] = rows
    for rel, columns in COVERAGE_LEDGERS.items():
        rows, error = read_csv(root / rel, columns)
        if error:
            reasons["count_arithmetic"].append(f"COUNT_ARITHMETIC: {error}")
            data["ready"] = False
        else:
            data["ledgers"][rel] = rows
    return data


def check_traceability(root: Path, data: dict, reasons: dict[str, list[str]]) -> None:
    bucket = reasons["traceability"]
    if not data["ready"] and not data["research"] and not data["sources"]:
        # Structural load failures are already recorded. Still scan whatever loaded.
        pass
    research = data["research"]
    cases = data["cases"]
    results = data["results"]
    requirements = data["requirements"]
    sources = data["sources"]
    clauses = data["clauses"]
    decisions = data["decisions"]

    # Evidence status and execution outcome are separate axes. Scan the raw
    # payloads so the finding names the confusion even when the schema also
    # refuses the value: a run outcome must never silently replace the Plan's
    # evidence terminology, and the reason for the refusal should say so.
    for record in data.get("raw_research", []):
        bucket.extend(
            cross_axis_problems(record, str(record.get("record_id") or "research record"))
        )
    for record in data.get("raw_results", []):
        bucket.extend(
            cross_axis_problems(record, str(record.get("record_id") or "simulation result"))
        )
    if isinstance(data.get("status"), dict):
        bucket.extend(cross_axis_problems(data["status"], "programme status"))

    bucket.extend(
        duplicates_within(
            [evidence_record_id(item) for item in research],
            "research/research_records.json",
        )
    )
    bucket.extend(duplicates_within([item.get("id", "") for item in cases], "simulations/scenarios.json"))
    bucket.extend(
        duplicates_within([evidence_record_id(item) for item in results], "results")
    )
    bucket.extend(
        duplicates_within(
            [item.get("requirement_id", "") for item in requirements],
            "requirements/requirements.json",
        )
    )
    bucket.extend(duplicates_within([item.get("id", "") for item in sources], "sources/source_register.json"))
    bucket.extend(
        duplicates_within([item.get("clause_id", "") for item in clauses], "clauses/clause_references.json")
    )
    bucket.extend(
        duplicates_within(
            [item.get("decision_id", "") for item in decisions],
            "decisions",
        )
    )
    checkpoints = [row.get("checkpoint", "") for row in data["ledgers"].get("checkpoint", [])]
    bucket.extend(duplicates_within(checkpoints, "ledgers/checkpoint_schedule.csv"))
    report_ids = [row.get("report_id", "") for row in data["ledgers"].get("ledgers/report_index.csv", [])]
    bucket.extend(duplicates_within(report_ids, "ledgers/report_index.csv"))
    for rel, column in (
        ("ledgers/dimensions.csv", "dimension"),
        ("ledgers/levels.csv", "level"),
        ("ledgers/phases.csv", "phase"),
    ):
        bucket.extend(
            duplicates_within(
                [row.get(column, "") for row in data["ledgers"].get(rel, [])],
                rel,
            )
        )

    groups = [
        ("research", {evidence_record_id(item) for item in research if evidence_record_id(item)}),
        (
            "simulation",
            {item["id"] for item in cases if item.get("id")}
            | {evidence_record_id(item) for item in results if evidence_record_id(item)},
        ),
        ("requirement", {item["requirement_id"] for item in requirements if item.get("requirement_id")}),
        ("source", {item["id"] for item in sources if item.get("id")}),
        ("clause", {item["clause_id"] for item in clauses if item.get("clause_id")}),
        ("decision", {item.get("decision_id", "") for item in decisions if item.get("decision_id")}),
        ("checkpoint", {item for item in checkpoints if item}),
        ("report", {item for item in report_ids if item}),
        ("dimension", {row.get("dimension", "") for row in data["ledgers"].get("ledgers/dimensions.csv", []) if row.get("dimension")}),
        ("level", {row.get("level", "") for row in data["ledgers"].get("ledgers/levels.csv", []) if row.get("level")}),
        ("phase", {row.get("phase", "") for row in data["ledgers"].get("ledgers/phases.csv", []) if row.get("phase")}),
    ]
    bucket.extend(cross_identifier_collisions(groups))

    for record in decisions:
        label = record.get("decision_id", "decision")
        for key in (
            "decision_id",
            "authority",
            "decided_by",
            "citation",
            "target_ids",
            "statement",
            "release_classification",
        ):
            if key not in record:
                bucket.append(f"TRACEABILITY: decision {label} is missing {key}")
        evidence_decision = record.get("state") in DECISION_REQUIRED
        authorization_decision = record.get("authorization_status") == "AUTHORIZED"
        if record.get("state") not in (None, "") and not evidence_decision:
            bucket.append(
                f"TRACEABILITY: decision {label} state must be one of {DECISION_GATED_LABEL}"
            )
        # An execution outcome is not a decision state. Refuse the confusion
        # here too so a decision cannot be filed as if it were a run result.
        if record.get("state") in EXECUTION_OUTCOMES:
            bucket.append(
                f"TRACEABILITY: decision {label} state {record.get('state')!r} is an "
                "execution outcome, not an evidence decision state"
            )
        if not evidence_decision and not authorization_decision:
            bucket.append(
                f"TRACEABILITY: decision {label} must record an evidence decision or an authorization, as separate fields"
            )
        if record.get("authority") not in {"owner", "reviewer"}:
            bucket.append(f"TRACEABILITY: decision {label} authority must be owner or reviewer")
        if not nonempty_string(record.get("decided_by")) or not nonempty_string(record.get("citation")):
            bucket.append(
                f"TRACEABILITY: decision {label} must cite an owner or reviewer and a record locator"
            )
        if not isinstance(record.get("target_ids"), list) or not record.get("target_ids"):
            bucket.append(f"TRACEABILITY: decision {label} must name at least one target id")

    case_ids = {item["id"] for item in cases}
    research_ids = {evidence_record_id(item) for item in research}
    clause_ids = {item["clause_id"] for item in clauses}
    source_ids = {item["id"] for item in sources}
    results_by_id: dict[str, list[dict]] = {}
    for item in results:
        results_by_id.setdefault(evidence_record_id(item), []).append(item)

    if len(research) != len(cases) or len(cases) != len(results):
        if research or cases or results:
            bucket.append(
                "TRACEABILITY: research records, simulation cases, and simulation results are not one-to-one"
            )

    for record in research:
        identifier = evidence_record_id(record)
        if record.get("pass_type") != PASS_TYPE_RESEARCH:
            bucket.append(
                f"TRACEABILITY: {identifier} pass_type must be {PASS_TYPE_RESEARCH}"
            )
        bucket.extend(cross_axis_problems(record, identifier))
        link = record.get("simulation_link")
        matched_cases = [item for item in cases if item.get("id") == link]
        if len(matched_cases) != 1:
            bucket.append(f"TRACEABILITY: {identifier} must link to exactly one simulation case")
        else:
            case = matched_cases[0]
            if case.get("research_record_id") != identifier:
                bucket.append(
                    f"TRACEABILITY: {case.get('id')} does not link back to {identifier}"
                )
        expected_evidence = f"results/{link}.json"
        if record.get("raw_evidence_location") != expected_evidence:
            bucket.append(
                f"TRACEABILITY: {identifier} raw_evidence_location must be {expected_evidence}"
            )
        elif not (root / expected_evidence).is_file():
            bucket.append(f"TRACEABILITY: {identifier} raw evidence file is missing")
        matched_results = results_by_id.get(link, [])
        if len(matched_results) != 1:
            bucket.append(f"TRACEABILITY: {identifier} must link to exactly one simulation result")
        elif matched_results[0].get("research_record_id") != identifier:
            bucket.append(
                f"TRACEABILITY: result {link} does not link back to {identifier}"
            )
        card = root / "research" / f"{identifier}.md"
        if not card.is_file():
            bucket.append(f"TRACEABILITY: missing research card research/{identifier}.md")
        for clause_id in record.get("clause_ids") or []:
            if clause_id not in clause_ids:
                bucket.append(
                    f"TRACEABILITY: {identifier} clause reference {clause_id} is not declared"
                )

    for case in cases:
        if case.get("research_record_id") not in research_ids:
            bucket.append(
                f"TRACEABILITY: {case.get('id')} does not resolve to an existing research record"
            )
        for source_id in case.get("source_ids") or []:
            if source_id not in source_ids:
                bucket.append(f"TRACEABILITY: {case.get('id')} source {source_id} is not in the source register")
        for clause_id in case.get("clause_ids") or []:
            if clause_id not in clause_ids:
                bucket.append(
                    f"TRACEABILITY: {case.get('id')} clause reference {clause_id} is not declared"
                )

    requirement_cards: dict[str, int] = {}
    for requirement in requirements:
        label = requirement.get("requirement_id", "")
        if OTHER_REGISTER_ID.fullmatch(str(label)):
            bucket.append(
                f"TRACEABILITY: {label} belongs to the separate collection-level register, "
                "not this programme. Requirement ids use the form ULC-<tablet>-<clause>."
            )
        elif ULC_REQUIREMENT_ID.fullmatch(str(label)) is None:
            bucket.append(
                f"TRACEABILITY: {label} must be a requirement id of the form ULC-<tablet>-<clause>"
            )
        research_record_id = requirement.get("research_record_id")
        requirement_cards[research_record_id] = requirement_cards.get(research_record_id, 0) + 1
        if research_record_id not in research_ids:
            bucket.append(f"TRACEABILITY: {label} does not resolve to an existing research record")
        if requirement.get("clause_id") not in clause_ids:
            bucket.append(f"TRACEABILITY: {label} does not resolve to a declared clause reference")
        simulation_id = requirement.get("simulation_record_id")
        if simulation_id and simulation_id not in case_ids:
            bucket.append(f"TRACEABILITY: {label} simulation {simulation_id} does not exist")
    for research_record_id, count in requirement_cards.items():
        if count > 1:
            bucket.append(
                f"TRACEABILITY: {research_record_id} has {count} requirements; one requirement per card"
            )

    for clause in clauses:
        label = clause.get("clause_id")
        if clause.get("placeholder") is True:
            note = clause.get("note") or ""
            if "example placeholder" not in str(note).lower():
                bucket.append(
                    f"TRACEABILITY: placeholder clause reference {label} must be marked as an example placeholder"
                )
        note = clause.get("note")
        if isinstance(note, str) and ("\n" in note or len(note) > 240):
            bucket.append(
                f"TRACEABILITY: clause reference {label} note must be a single line and must not carry clause text"
            )
        banned = CLAUSE_BODY_KEYS.intersection(clause)
        if banned:
            bucket.append(
                f"TRACEABILITY: clause reference {label} must carry an identifier only, not {', '.join(sorted(banned))}"
            )

    for source in sources:
        # A witness siglum is a claim about what a cited edition assigns. It is
        # refused without a locator into that edition, and the repository never
        # assigns one of its own.
        if "witness_siglum" in source:
            if not nonempty_string(source.get("witness_siglum_locator")):
                bucket.append(
                    f"TRACEABILITY: source {source.get('id')} records a witness_siglum "
                    "without a locator into the edition that assigns it"
                )
            if source.get("source_role") != "critical_edition":
                bucket.append(
                    f"TRACEABILITY: source {source.get('id')} records a witness_siglum "
                    "but its source_role is not critical_edition; only the citing "
                    "edition may assign a siglum"
                )
        elif "witness_siglum_locator" in source:
            bucket.append(
                f"TRACEABILITY: source {source.get('id')} records a witness_siglum_locator "
                "without a witness_siglum"
            )
        for dependency in source.get("independence_from") or []:
            if dependency == source.get("id"):
                bucket.append(
                    f"TRACEABILITY: source {source.get('id')} lists itself in independence_from"
                )
            elif dependency not in source_ids:
                bucket.append(
                    f"TRACEABILITY: source {source.get('id')} independence_from names "
                    f"{dependency}, which is not in the source register"
                )
        for field in ("commit", "blob_sha"):
            value = source.get(field)
            if value in (None, ""):
                continue
            if not isinstance(value, str) or GIT_SHA.fullmatch(value) is None:
                bucket.append(
                    f"TRACEABILITY: source {source.get('id')} {field} must be a 40-character git SHA or omitted"
                )

    for rel, column in (
        ("ledgers/dimensions.csv", "simulation_ids"),
        ("ledgers/levels.csv", "simulation_ids"),
        ("ledgers/phases.csv", "simulation_ids"),
        ("ledgers/relationships.csv", "simulation_ids"),
        ("ledgers/report_index.csv", "simulation_ids"),
    ):
        for row in data["ledgers"].get(rel, []):
            for identifier in split_ids(row.get(column, "")):
                if identifier not in case_ids:
                    bucket.append(f"TRACEABILITY: {identifier} in {rel} does not match a simulation case")
    for row in data["ledgers"].get("ledgers/report_index.csv", []):
        for identifier in split_ids(row.get("research_ids", "")):
            if identifier not in research_ids:
                bucket.append(
                    f"TRACEABILITY: {identifier} in ledgers/report_index.csv does not match a research record"
                )


def parse_execution_timestamp(value: object) -> datetime | None:
    """Parse ``execution_timestamp``, refusing a naive or malformed value."""
    if not isinstance(value, str):
        return None
    if NAIVE_TIMESTAMP.fullmatch(value.strip()):
        return None
    return parse_time(value)


def check_simulation_pass_fields(
    result: dict,
    identifier: str,
    started: datetime | None,
    ended: datetime | None,
    bucket: list[str],
) -> None:
    """Check the four Plan simulation-pass fields beyond the lock fields.

    ``execution_timestamp``, ``failure_policy``, ``known_answer_check`` and
    ``mcse_or_precision_note`` are required on every simulation pass.
    """
    stamp = parse_execution_timestamp(result.get("execution_timestamp"))
    if stamp is None:
        bucket.append(
            f"EXECUTION_EVIDENCE: {identifier} execution_timestamp is missing, "
            "malformed, or has no explicit numeric offset or Z"
        )
    elif started is not None and ended is not None and not (started <= stamp <= ended):
        bucket.append(
            f"EXECUTION_EVIDENCE: {identifier} execution_timestamp falls outside "
            "the recorded started_at..ended_at interval"
        )

    if not nonempty_string(result.get("failure_policy")):
        bucket.append(
            f"EXECUTION_EVIDENCE: {identifier} failure_policy must state what is "
            "recorded on a crash or non-convergence"
        )

    known = result.get("known_answer_check")
    if not isinstance(known, dict):
        bucket.append(
            f"EXECUTION_EVIDENCE: {identifier} known_answer_check must be an object "
            "with included, case_id and detail"
        )
    else:
        included = known.get("included")
        case_id = known.get("case_id")
        detail = known.get("detail")
        if not isinstance(included, bool):
            bucket.append(
                f"EXECUTION_EVIDENCE: {identifier} known_answer_check.included must be a boolean"
            )
        elif included is True:
            if not nonempty_string(case_id):
                bucket.append(
                    f"EXECUTION_EVIDENCE: {identifier} known_answer_check.included is true "
                    "but case_id is empty"
                )
            if not nonempty_string(detail):
                bucket.append(
                    f"EXECUTION_EVIDENCE: {identifier} known_answer_check.detail must be "
                    "a non-empty string"
                )
        else:
            if case_id not in (None, ""):
                bucket.append(
                    f"EXECUTION_EVIDENCE: {identifier} known_answer_check.case_id must be "
                    "null when included is false"
                )
            if not nonempty_string(detail):
                bucket.append(
                    f"EXECUTION_EVIDENCE: {identifier} known_answer_check.detail must state "
                    "why no known-answer or negative-control case applies"
                )

    if not nonempty_string(result.get("mcse_or_precision_note")):
        bucket.append(
            f"EXECUTION_EVIDENCE: {identifier} mcse_or_precision_note must be a non-empty "
            "string that says so explicitly when the model is deterministic or single-run"
        )


def check_execution_outcome_evidence(result: dict, identifier: str, bucket: list[str]) -> None:
    """Refuse an ``executed`` claim that carries no execution evidence.

    ``execution_outcome`` is what the run did. ``executed`` requires the
    recorded artefacts of a run: an exit code, a code hash, and a raw
    evidence location. ``failed`` and ``incomplete`` are execution outcomes
    too, and neither implies anything about ``evidence_status``.
    """
    outcome = result.get("execution_outcome")
    if outcome not in EXECUTION_OUTCOME_VALUES:
        bucket.append(
            f"EXECUTION_EVIDENCE: {identifier} execution_outcome {outcome!r} is not one of "
            f"{', '.join(sorted(EXECUTION_OUTCOME_VALUES))}"
        )
        return
    if outcome != "executed":
        return
    missing = [
        field
        for field, present in (
            ("exit_code", is_int(result.get("exit_code"))),
            ("code_sha256", isinstance(result.get("code_sha256"), str) and HASH64.fullmatch(result.get("code_sha256", "")) is not None),
            ("raw_evidence_location", nonempty_string(result.get("raw_evidence_location"))),
        )
        if not present
    ]
    if missing:
        bucket.append(
            f"EXECUTION_EVIDENCE: {identifier} claims execution_outcome executed but has "
            f"no execution evidence ({', '.join(missing)})"
        )


def check_execution(root: Path, data: dict, reasons: dict[str, list[str]]) -> None:
    bucket = reasons["execution_evidence"]
    cases = {item["id"]: item for item in data["cases"] if item.get("id")}
    log_entries: dict[str, list[dict]] = {}
    for entry in data["log"]:
        if not isinstance(entry, dict):
            bucket.append("EXECUTION_EVIDENCE: execution log contains a non-object entry")
            continue
        log_entries.setdefault(entry.get("id"), []).append(entry)
    if len(data["log"]) != len(data["results"]):
        if data["log"] or data["results"]:
            bucket.append(
                "EXECUTION_EVIDENCE: execution log entries and simulation results are not one-to-one"
            )
    for result in data["results"]:
        identifier = evidence_record_id(result) or "result"
        entries = log_entries.get(identifier, [])
        if len(entries) != 1:
            bucket.append(f"EXECUTION_EVIDENCE: {identifier} must have exactly one execution log entry")
        else:
            entry = entries[0]
            if not is_int(result.get("exit_code")):
                bucket.append(f"EXECUTION_EVIDENCE: {identifier} exit_code is missing or not an integer")
            elif not is_int(entry.get("exit_code")) or entry.get("exit_code") != result.get("exit_code"):
                bucket.append(
                    f"EXECUTION_EVIDENCE: {identifier} execution log exit_code does not match the result"
                )
            if not isinstance(entry.get("stdout"), str) or not isinstance(entry.get("stderr"), str):
                bucket.append(
                    f"EXECUTION_EVIDENCE: {identifier} execution log must carry stdout and stderr strings"
                )
        started = parse_time(result.get("started_at"))
        ended = parse_time(result.get("ended_at"))
        if started is None or ended is None:
            bucket.append(f"EXECUTION_EVIDENCE: {identifier} is missing a real start or end timestamp")
        elif ended < started:
            bucket.append(f"EXECUTION_EVIDENCE: {identifier} ended_at is earlier than started_at")
        environment = result.get("environment")
        if (
            not isinstance(environment, dict)
            or not nonempty_string(environment.get("python"))
            or not nonempty_string(environment.get("platform"))
        ):
            bucket.append(f"EXECUTION_EVIDENCE: {identifier} is missing an environment description")
        code_path = result.get("code_path")
        if not safe_relative(code_path) or not (root / str(code_path)).is_file():
            bucket.append(f"EXECUTION_EVIDENCE: {identifier} code_path does not name a package file")
        elif sha256_file(root / str(code_path)) != result.get("code_sha256"):
            bucket.append(f"EXECUTION_EVIDENCE: {identifier} code_sha256 does not match {code_path}")
        if not isinstance(result.get("fixtures_sha256"), str) or HASH64.fullmatch(result.get("fixtures_sha256", "")) is None:
            bucket.append(f"EXECUTION_EVIDENCE: {identifier} fixtures_sha256 is missing or not a SHA-256 digest")
        if not is_number(result.get("duration_seconds")) or result.get("duration_seconds") < 0:
            bucket.append(f"EXECUTION_EVIDENCE: {identifier} duration_seconds is missing or negative")
        outcome = result.get("outcome")
        execution_status = result.get("execution_status")
        matched = result.get("expectation_matched")
        if outcome == "PASS":
            if matched is not True or result.get("exit_code") != 0 or execution_status != "COMPLETED":
                bucket.append(
                    f"EXECUTION_EVIDENCE: {identifier} PASS does not agree with its exit code, status, and expectation flag"
                )
        elif outcome == "FAIL":
            if matched is not False or execution_status != "COMPLETED":
                bucket.append(f"EXECUTION_EVIDENCE: {identifier} FAIL does not agree with its execution record")
        elif outcome == "ERROR":
            if execution_status != "ERROR" or matched is not False:
                bucket.append(f"EXECUTION_EVIDENCE: {identifier} ERROR does not agree with its execution record")
        else:
            bucket.append(f"EXECUTION_EVIDENCE: {identifier} outcome is not PASS, FAIL, or ERROR")
        case = cases.get(identifier)
        if case is not None and result.get("input") != case.get("input"):
            bucket.append(f"EXECUTION_EVIDENCE: {identifier} input does not match the simulation case")
        if not nonempty_string(result.get("uncertainty_and_limitations")):
            bucket.append(f"EXECUTION_EVIDENCE: {identifier} is missing uncertainty_and_limitations")
        if result.get("pass_type") != PASS_TYPE_EXECUTED_SIMULATION:
            bucket.append(
                f"EXECUTION_EVIDENCE: {identifier} pass_type must be "
                f"{PASS_TYPE_EXECUTED_SIMULATION}"
            )
        bucket.extend(cross_axis_problems(result, identifier))
        check_simulation_pass_fields(result, identifier, started, ended, bucket)
        check_execution_outcome_evidence(result, identifier, bucket)


def check_expectation(root: Path, data: dict, reasons: dict[str, list[str]]) -> None:
    bucket = reasons["expectation_discipline"]
    scenarios = root / "simulations" / "scenarios.json"
    if not scenarios.is_file():
        return
    current_hash = sha256_file(scenarios)
    cases = {item["id"]: item for item in data["cases"] if item.get("id")}
    for result in data["results"]:
        identifier = evidence_record_id(result)
        case = cases.get(identifier)
        if case is None:
            continue
        if result.get("expected") != case.get("expected"):
            bucket.append(
                "EXPECTATION_MISMATCH: result "
                f"{identifier} records an expected outcome that does not equal "
                "the expected outcome declared in simulations/scenarios.json"
            )
        if result.get("fixtures_sha256") != current_hash:
            bucket.append(
                f"CASE_FILE_NOT_HASH_LOCKED: fixtures_sha256 for {identifier} "
                "does not match simulations/scenarios.json"
            )


def _parse_ledger_int(value: object, label: str, bucket: list[str]) -> int | None:
    if isinstance(value, str) and re.fullmatch(r"-?\d+", value.strip()):
        return int(value.strip())
    bucket.append(f"COUNT_ARITHMETIC: {label} is not an integer")
    return None


def _coverage_duplicates(rows: list[dict], columns: tuple[str, ...], label: str) -> list[str]:
    seen: list[str] = []
    for row in rows:
        for column in columns:
            seen.extend(split_ids(row.get(column, "")))
    return [
        f"DOUBLE_COUNT: {identifier} appears more than once in {label}"
        for identifier, count in Counter(seen).items()
        if count > 1
    ]


def check_counts(root: Path, data: dict, reasons: dict[str, list[str]]) -> None:
    bucket = reasons["count_arithmetic"]
    status = data["status"]
    if not isinstance(status, dict):
        return
    research = data["research"]
    cases = data["cases"]
    results = data["results"]
    requirements = data["requirements"]
    ledgers = data["ledgers"]
    if "research" not in ledgers or "simulation" not in ledgers or "checkpoint" not in ledgers:
        return

    def expect(actual: int, declared: object, label: str) -> None:
        if declared != actual:
            bucket.append(
                f"COUNT_ARITHMETIC: status {label} is {declared!r} but the package contains {actual}"
            )

    matched = sum(
        1
        for item in results
        if item.get("expectation_matched") is True
        and item.get("execution_status") == "COMPLETED"
        and item.get("outcome") == "PASS"
    )
    failures = sum(
        1
        for item in results
        if item.get("expectation_matched") is False
        and item.get("execution_status") == "COMPLETED"
        and item.get("outcome") == "FAIL"
    )
    errors = sum(
        1
        for item in results
        if item.get("execution_status") == "ERROR" or item.get("outcome") == "ERROR"
    )
    expect(len(research), status.get("research_records"), "research_records")
    expect(len(cases), status.get("simulation_cases"), "simulation_cases")
    expect(len(results), status.get("simulation_results"), "simulation_results")
    expect(len(requirements), status.get("requirements"), "requirements")
    expect(matched, status.get("expectations_matched"), "expectations_matched")
    expect(failures, status.get("expectation_failures"), "expectation_failures")
    expect(errors, status.get("execution_errors"), "execution_errors")

    reports = report_paths(root)
    report_rows = ledgers.get("ledgers/report_index.csv", [])
    expect(len(reports), status.get("reports"), "reports")
    if len(report_rows) != len(reports):
        bucket.append(
            f"COUNT_ARITHMETIC: report index has {len(report_rows)} rows and reports/ has {len(reports)} report files"
        )
    indexed = {row.get("path") for row in report_rows}
    for rel in reports:
        if rel not in indexed:
            bucket.append(f"COUNT_ARITHMETIC: report file {rel} is not in ledgers/report_index.csv")
    for row in report_rows:
        path = row.get("path")
        if path not in reports:
            bucket.append(f"COUNT_ARITHMETIC: report index path {path} is not a report file")

    research_rows = ledgers.get("research", [])
    if {row.get("record_id") for row in research_rows} != {evidence_record_id(item) for item in research}:
        bucket.append("COUNT_ARITHMETIC: research ledger ids do not match research records")
    research_by_id = {evidence_record_id(item): item for item in research}
    for row in research_rows:
        record = research_by_id.get(row.get("record_id"))
        if record is None:
            continue
        for field in PLAN_EVIDENCE_FIELDS:
            if row.get(field) != record.get(field):
                bucket.append(
                    f"COUNT_ARITHMETIC: research ledger {row.get('record_id')} {field} does not match the research record"
                )
        if row.get("execution_outcome") != record.get("execution_outcome"):
            bucket.append(
                f"COUNT_ARITHMETIC: research ledger {row.get('record_id')} execution_outcome does not match the research record"
            )
        for field in ("simulation_link", "programme_credit", "release_classification"):
            if row.get(field) != record.get(field):
                bucket.append(
                    f"COUNT_ARITHMETIC: research ledger {row.get('record_id')} {field} does not match the research record"
                )
        if split_ids(row.get("clause_ids")) != list(record.get("clause_ids") or []):
            bucket.append(
                f"COUNT_ARITHMETIC: research ledger {row.get('record_id')} clause_ids do not match the research record"
            )

    simulation_rows = ledgers.get("simulation", [])
    result_ids = {evidence_record_id(item) for item in results}
    if {row.get("record_id") for row in simulation_rows} != result_ids or result_ids != {item["id"] for item in cases}:
        if results or cases or simulation_rows:
            bucket.append("COUNT_ARITHMETIC: simulation ledger ids do not match cases and results")
    results_by_id = {evidence_record_id(item): item for item in results}
    for row in simulation_rows:
        result = results_by_id.get(row.get("record_id"))
        if result is None:
            continue
        for field in PLAN_EVIDENCE_FIELDS:
            if row.get(field) != result.get(field):
                bucket.append(
                    f"COUNT_ARITHMETIC: simulation ledger {row.get('record_id')} {field} does not match the result"
                )
        for field in (
            "protocol_version",
            "configuration",
            "execution_timestamp",
            "failure_policy",
            "mcse_or_precision_note",
            "execution_outcome",
            "research_record_id",
            "execution_status",
            "outcome",
            "started_at",
            "ended_at",
            "code_path",
            "code_sha256",
            "fixtures_sha256",
            "programme_credit",
            "independent_review",
            "release_classification",
        ):
            if row.get(field) != result.get(field):
                bucket.append(
                    f"COUNT_ARITHMETIC: simulation ledger {row.get('record_id')} {field} does not match the result"
                )
        # known_answer_check is an object on the result and a JSON cell in the
        # ledger. Compare it as JSON so a structural field is not silently dropped.
        if row.get("known_answer_check") != json.dumps(
            result.get("known_answer_check"), sort_keys=True
        ):
            bucket.append(
                f"COUNT_ARITHMETIC: simulation ledger {row.get('record_id')} known_answer_check does not match the result"
            )
        if row.get("environment") != environment_lock(result.get("environment")):
            bucket.append(
                f"COUNT_ARITHMETIC: simulation ledger {row.get('record_id')} environment does not match the result"
            )
        # A result with no exit_code at all is reported by
        # execution_evidence, which owns the missing-field finding. Only compare
        # the ledger cell when the result actually carries a value.
        if "exit_code" in result:
            exit_code = _parse_ledger_int(
                row.get("exit_code"),
                f"simulation ledger {row.get('record_id')} exit_code",
                bucket,
            )
            if exit_code is not None and exit_code != result.get("exit_code"):
                bucket.append(
                    f"COUNT_ARITHMETIC: simulation ledger {row.get('record_id')} exit_code does not match the result"
                )
        if row.get("raw_evidence_location") != f"results/{row.get('record_id')}.json":
            bucket.append(
                f"COUNT_ARITHMETIC: simulation ledger {row.get('record_id')} raw_evidence_location must point at its result file"
            )

    requirement_rows = ledgers.get("requirements", [])
    if {row.get("requirement_id") for row in requirement_rows} != {
        item["requirement_id"] for item in requirements
    }:
        bucket.append("COUNT_ARITHMETIC: requirements ledger ids do not match requirement records")
    requirements_by_id = {item["requirement_id"]: item for item in requirements}
    for row in requirement_rows:
        requirement = requirements_by_id.get(row.get("requirement_id"))
        if requirement is None:
            continue
        for field in (
            "research_record_id",
            "simulation_record_id",
            "clause_id",
            "evidence_status",
            "authorization_status",
            "programme_credit",
            "release_classification",
        ):
            if row.get(field) != requirement.get(field):
                bucket.append(
                    f"COUNT_ARITHMETIC: requirements ledger {row.get('requirement_id')} {field} does not match the requirement record"
                )

    schedule = ledgers.get("checkpoint", [])
    research_by_cp = Counter(item.get("checkpoint_id") for item in research)
    cases_by_cp = Counter(item.get("checkpoint_id") for item in cases)
    results_by_cp: Counter = Counter()
    matched_by_cp: Counter = Counter()
    awarded_research_by_cp = Counter(
        item.get("checkpoint_id") for item in research if item.get("programme_credit") == "AWARDED"
    )
    awarded_simulation_by_cp = Counter(
        item.get("checkpoint_id") for item in results if item.get("programme_credit") == "AWARDED"
    )
    case_checkpoint = {item["id"]: item.get("checkpoint_id") for item in cases}
    for result in results:
        checkpoint = result.get("checkpoint_id") or case_checkpoint.get(evidence_record_id(result))
        results_by_cp[checkpoint] += 1
        if (
            result.get("expectation_matched") is True
            and result.get("outcome") == "PASS"
            and result.get("execution_status") == "COMPLETED"
        ):
            matched_by_cp[checkpoint] += 1
    known_checkpoints = {row.get("checkpoint") for row in schedule}
    for record in research:
        if record.get("checkpoint_id") not in known_checkpoints:
            bucket.append(
                f"COUNT_ARITHMETIC: {evidence_record_id(record)} checkpoint {record.get('checkpoint_id')} is not in the checkpoint schedule"
            )
    for case in cases:
        if case.get("checkpoint_id") not in known_checkpoints:
            bucket.append(
                f"COUNT_ARITHMETIC: {case.get('id')} checkpoint {case.get('checkpoint_id')} is not in the checkpoint schedule"
            )

    recorded_research = 0
    executed = 0
    accepted_research = 0
    accepted_simulation = 0
    for row in schedule:
        checkpoint = row.get("checkpoint")
        label = f"checkpoint {checkpoint}"
        required_research = _parse_ledger_int(row.get("required_research"), f"{label} required_research", bucket)
        recorded = _parse_ledger_int(
            row.get("recorded_desktop_assessments"),
            f"{label} recorded_desktop_assessments",
            bucket,
        )
        required_simulations = _parse_ledger_int(
            row.get("required_simulations"),
            f"{label} required_simulations",
            bucket,
        )
        executed_simulations = _parse_ledger_int(
            row.get("executed_simulations"),
            f"{label} executed_simulations",
            bucket,
        )
        matched_expectations = _parse_ledger_int(
            row.get("matched_expectations"),
            f"{label} matched_expectations",
            bucket,
        )
        owner_research = _parse_ledger_int(
            row.get("owner_accepted_research_credits"),
            f"{label} owner_accepted_research_credits",
            bucket,
        )
        owner_simulation = _parse_ledger_int(
            row.get("owner_accepted_simulation_credits"),
            f"{label} owner_accepted_simulation_credits",
            bucket,
        )
        if None in (
            required_research,
            recorded,
            required_simulations,
            executed_simulations,
            matched_expectations,
            owner_research,
            owner_simulation,
        ):
            continue
        if recorded != research_by_cp[checkpoint]:
            bucket.append(
                f"COUNT_ARITHMETIC: {label} recorded_desktop_assessments does not match research records"
            )
        if executed_simulations != results_by_cp[checkpoint]:
            bucket.append(
                f"COUNT_ARITHMETIC: {label} executed_simulations does not match simulation results"
            )
        if matched_expectations != matched_by_cp[checkpoint]:
            bucket.append(
                f"COUNT_ARITHMETIC: {label} matched_expectations does not match passing results"
            )
        if required_research < recorded or required_simulations < executed_simulations:
            bucket.append(f"COUNT_ARITHMETIC: {label} records more activity than it required")
        if cases_by_cp[checkpoint] != results_by_cp[checkpoint]:
            bucket.append(f"COUNT_ARITHMETIC: {label} cases and results differ")
        if owner_research != awarded_research_by_cp[checkpoint]:
            bucket.append(
                f"COUNT_ARITHMETIC: {label} owner_accepted_research_credits does not match AWARDED research records"
            )
        if owner_simulation != awarded_simulation_by_cp[checkpoint]:
            bucket.append(
                f"COUNT_ARITHMETIC: {label} owner_accepted_simulation_credits does not match AWARDED simulation records"
            )
        recorded_research += recorded
        executed += executed_simulations
        accepted_research += owner_research
        accepted_simulation += owner_simulation
    if recorded_research != len(research):
        bucket.append("COUNT_ARITHMETIC: checkpoint recorded research does not match research records")
    if executed != len(results):
        bucket.append("COUNT_ARITHMETIC: checkpoint executed simulations do not match simulation results")
    if accepted_research != status.get("owner_accepted_research_credits"):
        bucket.append(
            "COUNT_ARITHMETIC: owner_accepted_research_credits does not match the checkpoint schedule"
        )
    if accepted_simulation != status.get("owner_accepted_simulation_credits"):
        bucket.append(
            "COUNT_ARITHMETIC: owner_accepted_simulation_credits does not match the checkpoint schedule"
        )
    if status.get("owner_accepted_research_credits") != sum(awarded_research_by_cp.values()):
        bucket.append(
            "COUNT_ARITHMETIC: owner_accepted_research_credits does not match AWARDED research records"
        )
    if status.get("owner_accepted_simulation_credits") != sum(awarded_simulation_by_cp.values()):
        bucket.append(
            "COUNT_ARITHMETIC: owner_accepted_simulation_credits does not match AWARDED simulation records"
        )

    for rel, columns in (
        ("ledgers/dimensions.csv", ("simulation_ids",)),
        ("ledgers/levels.csv", ("simulation_ids",)),
        ("ledgers/phases.csv", ("simulation_ids",)),
        ("ledgers/relationships.csv", ("simulation_ids",)),
    ):
        bucket.extend(_coverage_duplicates(ledgers.get(rel, []), columns, rel))
    bucket.extend(
        _coverage_duplicates(report_rows, ("simulation_ids",), "ledgers/report_index.csv")
    )
    bucket.extend(
        _coverage_duplicates(report_rows, ("research_ids",), "ledgers/report_index.csv research_ids")
    )

    summary = ledgers.get("ledgers/model_family_summary.csv", [])
    if not cases:
        if summary:
            bucket.append("COUNT_ARITHMETIC: model_family_summary.csv has rows but there are no simulation cases")
        return
    if any(not nonempty_string(item.get("family")) for item in cases):
        bucket.append("COUNT_ARITHMETIC: every simulation case must declare a family")
        return
    if not summary:
        bucket.append("COUNT_ARITHMETIC: cases declare families but model_family_summary.csv has no rows")
        return
    families = [row.get("family", "") for row in summary]
    bucket.extend(duplicates_within(families, "ledgers/model_family_summary.csv"))
    if set(families) != {item["family"] for item in cases}:
        bucket.append("COUNT_ARITHMETIC: model families do not reconcile with simulation cases")
    case_by_family: dict[str, list[dict]] = {}
    for case in cases:
        case_by_family.setdefault(case["family"], []).append(case)
    for row in summary:
        family = row.get("family")
        members = case_by_family.get(family, [])
        member_ids = {item["id"] for item in members}
        configurations = _parse_ledger_int(row.get("configurations"), f"family {family} configurations", bucket)
        completed_value = _parse_ledger_int(row.get("completed"), f"family {family} completed", bucket)
        matched_value = _parse_ledger_int(
            row.get("expectations_matched"),
            f"family {family} expectations_matched",
            bucket,
        )
        if configurations is not None and configurations != len(members):
            bucket.append(f"COUNT_ARITHMETIC: family {family} configurations does not match its cases")
        completed = [
            item
            for item in results
            if evidence_record_id(item) in member_ids and item.get("execution_status") == "COMPLETED"
        ]
        matched_members = [item for item in completed if item.get("expectation_matched") is True]
        if completed_value is not None and completed_value != len(completed):
            bucket.append(f"COUNT_ARITHMETIC: family {family} completed does not match its results")
        if matched_value is not None and matched_value != len(matched_members):
            bucket.append(
                f"COUNT_ARITHMETIC: family {family} expectations_matched does not match its results"
            )
        if not nonempty_string(row.get("scope")):
            bucket.append(f"COUNT_ARITHMETIC: family {family} is missing a scope limit")


def _reviewer_decision(record: dict) -> bool:
    return (
        record.get("authority") == "reviewer"
        and record.get("state") in DECISION_REQUIRED
        and nonempty_string(record.get("decided_by"))
        and nonempty_string(record.get("citation"))
        and isinstance(record.get("target_ids"), list)
        and bool(record.get("target_ids"))
    )


def check_honest(data: dict, reasons: dict[str, list[str]]) -> None:
    bucket = reasons["honest_status"]
    status = data["status"]
    if not isinstance(status, dict):
        return
    decisions = data["decisions"]
    programme_id = status.get("programme", "")
    records = []
    for collection, key in (
        (data["research"], "record_id"),
        (data["results"], "record_id"),
        (data["requirements"], "requirement_id"),
    ):
        for record in collection:
            records.append((record, record.get(key, "record")))
    records.append((status, programme_id))
    for record, identifier in records:
        # Evidence and authorization are separate columns. Do not pass one into
        # the other: assert_authorization_status reads only the authorization
        # column, and require_state_authority reads only the evidence column.
        state = record.get("evidence_status")
        try:
            require_state_authority(state, decisions, identifier)
        except EvidenceStateError as exc:
            bucket.append(f"EVIDENCE_STATE_WITHOUT_DECISION: {identifier} {exc}")
        try:
            assert_authorization_status(record.get("authorization_status"), decisions, identifier)
        except EvidenceStateError as exc:
            bucket.append(f"AUTHORIZATION_WITHOUT_RECORD: {identifier} {exc}")
        # The Plan's ladder now has a state literally named ``authorized``.
        # Reaching it does not set, and does not imply, authorization_status
        # AUTHORIZED. Say so explicitly in the failure text so the finding is
        # not mistaken for a missing decision on the evidence ladder.
        if (
            state == "authorized"
            and record.get("authorization_status") == "AUTHORIZED"
            and not any(
                authorization_record_supports(item, identifier) for item in decisions
            )
        ):
            bucket.append(
                f"AUTHORIZATION_WITHOUT_RECORD: {identifier} sets authorization_status "
                "AUTHORIZED while carrying evidence_status 'authorized'; the evidence "
                "state is not an authorization record and does not imply one"
            )
        bucket.extend(cross_axis_problems(record, identifier))
        if "programme_credit" not in record:
            continue
        try:
            assert_programme_credit(record.get("programme_credit"), decisions, identifier)
        except EvidenceStateError as exc:
            bucket.append(f"PROGRAMME_CREDIT_SELF_AWARDED: {identifier} {exc}")

    acceptance = status.get("owner_acceptance")
    if acceptance == "PENDING":
        if status.get("owner_accepted_research_credits") or status.get("owner_accepted_simulation_credits"):
            bucket.append(
                "HONEST_STATUS: owner_acceptance is PENDING while owner-accepted credits are non-zero"
            )
    elif acceptance == "ACCEPTED":
        if not any(decision_supports(item, "accepted", programme_id) for item in decisions):
            bucket.append(
                "HONEST_STATUS: owner_acceptance is ACCEPTED without an explicit owner or reviewer decision record citing the programme"
            )
    else:
        bucket.append("HONEST_STATUS: owner_acceptance is not PENDING or ACCEPTED")

    if status.get("programme_complete") is True:
        supported = any(
            isinstance(item, dict)
            and item.get("programme_complete") is True
            and decision_supports(item, "accepted", programme_id)
            for item in decisions
        )
        if not supported:
            bucket.append(
                "HONEST_STATUS: programme_complete is true without a decision record that says so"
            )
    if status.get("release_authorized") is True:
        if not any(decision_supports(item, "authorized", programme_id) for item in decisions):
            bucket.append(
                "HONEST_STATUS: release_authorized is true without an explicit authorized decision record"
            )
    reviews = sum(1 for item in decisions if _reviewer_decision(item))
    if status.get("independent_reviews") != reviews:
        bucket.append(
            "HONEST_STATUS: independent_reviews does not equal cited reviewer decision records"
        )
    reproductions = sum(
        1 for item in data["results"] if item.get("evidence_status") in LATER_THAN_REPRODUCED
    )
    if status.get("independent_reproductions") != reproductions:
        bucket.append(
            "HONEST_STATUS: independent_reproductions does not equal results at "
            "independently_reproduced or a later evidence state"
        )
    production = status.get("production_validation")
    if production == "NOT_PERFORMED":
        pass
    elif production == "RECORDED":
        supported = any(
            isinstance(item, dict)
            and item.get("production_validation") == "RECORDED"
            and decision_supports(item, "accepted", programme_id)
            for item in decisions
        )
        if not supported:
            bucket.append(
                "PRODUCTION_VALIDATION_UNSUPPORTED: production_validation is RECORDED without a decision record"
            )
    else:
        bucket.append(
            "PRODUCTION_VALIDATION_UNSUPPORTED: production_validation "
            f"{production!r} is not supported; this scaffold does not certify production readiness"
        )
    for record in data["requirements"]:
        value = record.get("production_validation")
        if value == "NOT_PERFORMED":
            continue
        bucket.append(
            "PRODUCTION_VALIDATION_UNSUPPORTED: requirement "
            f"{record.get('requirement_id')} production_validation {value!r} is not supported without a recorded decision"
        )
    for result in data["results"]:
        if status.get("independent_reviews") == 0 and result.get("independent_review") not in {
            None,
            "NOT_PERFORMED",
        }:
            bucket.append(
                f"HONEST_STATUS: {evidence_record_id(result)} claims independent_review without a reviewer decision record"
            )
    for row in data["ledgers"].get("checkpoint", []):
        if str(row.get("status", "")).strip().upper() in {
            "ACCEPTED",
            "AUTHORIZED",
            "COMPLETE",
            "VALIDATED",
            "VERIFIED",
        }:
            cited = row.get("checkpoint", "")
            if not any(
                decision_supports(item, "accepted", cited) or decision_supports(item, "accepted", programme_id)
                for item in decisions
            ):
                bucket.append(
                    f"HONEST_STATUS: checkpoint {cited} status claims acceptance without a decision record"
                )
    for row in data["ledgers"].get("ledgers/model_family_summary.csv", []):
        if str(row.get("scope", "")).strip().upper() in FORBIDDEN_PRODUCTION:
            bucket.append(
                f"HONEST_STATUS: model family {row.get('family')} scope claims validation this scaffold does not grant"
            )
    for credit in (
        item.get("programme_credit")
        for item in data["research"] + data["results"] + data["requirements"]
    ):
        if credit is not None and credit not in PROGRAMME_CREDITS:
            bucket.append(f"HONEST_STATUS: unknown programme credit {credit!r}")


def iter_release_records(data: dict) -> list[tuple[dict, str]]:
    labeled = []
    for record in data["research"]:
        labeled.append((record, f"research {evidence_record_id(record)}"))
    for record in data["cases"]:
        labeled.append((record, f"simulation case {record.get('id')}"))
    for record in data["results"]:
        labeled.append((record, f"simulation result {evidence_record_id(record)}"))
    for record in data["requirements"]:
        labeled.append((record, f"requirement {record.get('requirement_id')}"))
    for record in data["sources"]:
        labeled.append((record, f"source {record.get('id')}"))
    for record in data["clauses"]:
        labeled.append((record, f"clause {record.get('clause_id')}"))
    for record in data["decisions"]:
        labeled.append((record, f"decision {record.get('decision_id')}"))
    if isinstance(data["status"], dict):
        labeled.append((data["status"], f"programme {data['status'].get('programme')}"))
    return labeled


def check_classification(root: Path, files: list[str], data: dict, reasons: dict[str, list[str]]) -> None:
    bucket = reasons["classification_gate"]
    loaded, error = load_json(root / CLASSIFICATION_REL)
    if error:
        bucket.append(f"CLASSIFICATION_GATE: {error}")
        return
    if not isinstance(loaded, dict):
        bucket.append("CLASSIFICATION_GATE: classifications must be a JSON object")
        return
    actual = set(files)
    declared = set(loaded)
    for name in sorted(actual - declared):
        bucket.append(f"UNCLASSIFIED_ARTEFACT: unclassified artefact {name} has no classification")
    for name in sorted(declared - actual):
        bucket.append(f"CLASSIFICATION_GATE: classifications.json lists {name} which is not a package file")
    for name in sorted(actual & declared):
        value = loaded[name]
        if value != PUBLIC_CLASSIFICATION:
            bucket.append(
                f"CLASSIFICATION_GATE: {name} is classified {value!r}; "
                f"this package may contain only {PUBLIC_CLASSIFICATION}"
            )
    for record, label in iter_release_records(data):
        value = record.get("release_classification")
        if value is None:
            bucket.append(f"UNCLASSIFIED_ARTEFACT: unclassified artefact {label} has no release_classification")
        elif value != PUBLIC_CLASSIFICATION:
            bucket.append(
                f"CLASSIFICATION_GATE: {label} release_classification is {value!r}; "
                f"this package may contain only {PUBLIC_CLASSIFICATION}"
            )


def validate(root: Path) -> dict:
    root = root.resolve()
    reasons = {name: [] for name in CHECKS}
    if not root.is_dir():
        reasons["manifest_integrity"].append(
            f"PACKAGE_ABSENT: package directory does not exist: {root}"
        )
    else:
        files = package_relative_paths(root)
        check_manifest(root, files, reasons)
        data = load_package(root, reasons)
        check_traceability(root, data, reasons)
        check_execution(root, data, reasons)
        check_expectation(root, data, reasons)
        check_counts(root, data, reasons)
        check_honest(data, reasons)
        check_classification(root, files, data, reasons)
    checks = []
    for name in CHECKS:
        item_reasons = reasons[name]
        checks.append(
            {
                "check": name,
                "outcome": "PASS" if not item_reasons else "FAIL",
                "reasons": item_reasons,
            }
        )
    return {
        "scope": SCOPE,
        "package": str(root),
        "ok": all(item["outcome"] == "PASS" for item in checks),
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check programme-package evidence discipline. "
            "A pass is not scientific validation, acceptance, or production readiness."
        )
    )
    parser.add_argument("package", help="Programme package directory")
    args = parser.parse_args(argv)
    root = Path(args.package)
    if not root.is_dir():
        print(f"PACKAGE_ABSENT: package directory does not exist: {root}", file=sys.stderr)
        return 2
    result = validate(root)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    for item in result["checks"]:
        if item["outcome"] != "FAIL":
            continue
        for reason in item["reasons"]:
            print(f"FAIL {item['check']}: {reason}", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
