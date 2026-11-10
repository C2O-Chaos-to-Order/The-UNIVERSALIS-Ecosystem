
"""Immutable, commit-bound run records."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import RuntimeConfig
from .constants import BANNER, CLASSIFICATION, TOOL_NAME, TOOL_STATUS, TOOL_VERSION
from .findings import Finding, severity_counts

SCHEMA_ID = "engineering-doctor-run-record/v0.1"

FORBIDDEN_SCORE_KEYS = frozenset(
    {
        "confidence",
        "confidence_percent",
        "readiness_percent",
        "readiness_score",
        "readiness",
    }
)


def canonical_dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def inputs_fingerprint(inputs: dict[str, Any]) -> str:
    return sha256_text(canonical_dumps(inputs))


def validate_record(
    record: dict[str, Any],
    *,
    config: RuntimeConfig | None = None,
) -> list[str]:
    """Stdlib structural checks. Missing required data is an error, not a pass."""

    errors: list[str] = []
    required = [
        "schema_id",
        "tool_name",
        "tool_version",
        "tool_status",
        "classification",
        "banner",
        "run_id",
        "started_at",
        "finished_at",
        "python_version",
        "inputs",
        "inputs_sha256",
        "inventory",
        "suites",
        "findings",
        "limitations",
        "severity_counts",
    ]
    for key in required:
        if key not in record:
            errors.append(f"missing required field {key!r}")
    if record.get("schema_id") != SCHEMA_ID:
        errors.append("schema_id mismatch")
    expected_name = config.tool_name if config is not None else record.get("tool_name", TOOL_NAME)
    expected_banner = config.banner if config is not None else record.get("banner", BANNER)
    expected_status = config.tool_status if config is not None else record.get("tool_status", TOOL_STATUS)
    expected_class = (
        config.classification if config is not None else record.get("classification", CLASSIFICATION)
    )
    if record.get("tool_name") != expected_name:
        errors.append("tool_name mismatch")
    if record.get("banner") != expected_banner:
        errors.append("banner mismatch")
    if record.get("tool_status") != expected_status:
        errors.append("tool_status mismatch")
    if not record.get("classification"):
        errors.append("classification is missing")
    elif record.get("classification") != expected_class:
        errors.append("classification mismatch")
    for key in FORBIDDEN_SCORE_KEYS:
        if key in record:
            errors.append(f"forbidden score field {key!r} is present")
    expected = record.get("inputs_sha256")
    inputs = record.get("inputs")
    if isinstance(inputs, dict) and isinstance(expected, str):
        actual = inputs_fingerprint(inputs)
        if actual != expected:
            errors.append("inputs_sha256 does not match canonical inputs")
    findings = record.get("findings")
    if isinstance(findings, list):
        for item in findings:
            if not isinstance(item, dict):
                errors.append("finding is not an object")
                continue
            if "basis" not in item or not item["basis"]:
                errors.append(f"finding {item.get('finding_id')!r} is missing a severity basis")
            if item.get("severity") not in {"Critical", "High", "Medium", "Low"}:
                errors.append(f"finding {item.get('finding_id')!r} has an invalid severity")
    return errors


def build_record(
    *,
    run_id: str,
    started_at: datetime,
    finished_at: datetime,
    python_version: str,
    inputs: dict[str, Any],
    inventory: list[dict[str, Any]],
    suites: list[dict[str, Any]],
    findings: list[Finding],
    limitations: list[str],
    repo_shas: dict[str, str | None],
    notes: list[str] | None = None,
    config: RuntimeConfig | None = None,
) -> dict[str, Any]:
    cfg = config or RuntimeConfig()
    record = {
        "schema_id": SCHEMA_ID,
        "tool_name": cfg.tool_name,
        "tool_version": cfg.tool_version,
        "tool_status": cfg.tool_status,
        "classification": cfg.classification,
        "banner": cfg.banner,
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "python_version": python_version,
        "inputs": inputs,
        "inputs_sha256": inputs_fingerprint(inputs),
        "repo_shas": repo_shas,
        "inventory": inventory,
        "suites": suites,
        "findings": [item.to_dict() for item in findings],
        "severity_counts": severity_counts(findings),
        "limitations": list(limitations),
        "notes": list(notes or []),
    }
    problems = validate_record(record, config=cfg)
    if problems:
        raise ValueError("refusing to write an invalid run record: " + "; ".join(problems))
    return record


def allocate_run_dir(output_dir: Path, started_at: datetime) -> tuple[str, Path]:
    """Create a new run directory. Existing paths are never overwritten."""

    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = started_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for _ in range(5):
        run_id = f"{stamp}-{uuid.uuid4().hex[:8]}"
        run_dir = output_dir / run_id
        try:
            run_dir.mkdir(exist_ok=False)
            return run_id, run_dir
        except FileExistsError:
            continue
    raise RuntimeError("could not allocate a unique run directory")


def write_record(run_dir: Path, record: dict[str, Any], brief_markdown: str) -> dict[str, Path]:
    """Write record.json, its sha256 sidecar, and brief.md. Never overwrite."""

    record_path = run_dir / "record.json"
    hash_path = run_dir / "record.json.sha256"
    brief_path = run_dir / "brief.md"
    for path in (record_path, hash_path, brief_path):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite {path}")
    serialized = json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    digest = sha256_text(serialized)
    record_path.write_text(serialized, encoding="utf-8")
    hash_path.write_text(digest + "\n", encoding="utf-8")
    brief_path.write_text(brief_markdown, encoding="utf-8")
    return {"record": record_path, "sha256": hash_path, "brief": brief_path}


def verify_record_sidecar(run_dir: Path) -> None:
    record_path = run_dir / "record.json"
    hash_path = run_dir / "record.json.sha256"
    actual = sha256_text(record_path.read_text(encoding="utf-8"))
    expected = hash_path.read_text(encoding="utf-8").strip()
    if actual != expected:
        raise ValueError("record.json does not match record.json.sha256")
