"""Fail-closed validator for knowledge records.

The walker understands a small JSON Schema subset: type, properties, required,
additionalProperties, items, enum, const, pattern, minLength, maxLength,
minItems, maxItems. Semantic Rule 1, source-digest, authorization, and
capability-growth checks live in Python.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from foundation.invariant import (
    FORBIDDEN_INTERPRETATION_KINDS,
    check_rule_1_assessment,
    check_rule_1_document,
    check_rule_1_reference,
    has_human_decision,
    locator_exists,
    sha256_bytes,
)

PACKAGE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = PACKAGE_DIR / "schemas" / "knowledge-record.schema.json"
RECORDS_DIRNAME = "records"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _is_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def validate_schema(instance: Any, schema: dict[str, Any], pointer: str = "$") -> list[str]:
    errors: list[str] = []
    expected = schema.get("type")
    if expected and not _is_type(instance, expected):
        return [f"{pointer}: expected {expected}, got {_type_name(instance)}"]
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{pointer}: must equal {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{pointer}: must be one of {schema['enum']!r}")
    if isinstance(instance, str):
        pattern = schema.get("pattern")
        if pattern and re.search(pattern, instance) is None:
            errors.append(f"{pointer}: does not match {pattern}")
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{pointer}: shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{pointer}: longer than maxLength {schema['maxLength']}")
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{pointer}: fewer than minItems {schema['minItems']}")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{pointer}: more than maxItems {schema['maxItems']}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(instance):
                errors.extend(validate_schema(item, item_schema, f"{pointer}[{index}]"))
    if isinstance(instance, dict):
        required = schema.get("required") or []
        for key in required:
            if key not in instance:
                errors.append(f"{pointer}: missing required property {key!r}")
        properties = schema.get("properties") or {}
        additional = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in properties:
                errors.extend(validate_schema(value, properties[key], f"{pointer}.{key}"))
            elif additional is False:
                errors.append(f"{pointer}: additional property {key!r} is not allowed")
    return errors


def git_blob_sha256(repo_root: Path, commit: str, path: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{commit}:{path}"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return sha256_bytes(result.stdout)


def check_sources(record: dict[str, Any], repo_root: Path, *, label: str) -> list[str]:
    errors: list[str] = []
    knowledge = record.get("knowledge") if isinstance(record.get("knowledge"), dict) else {}
    sources = knowledge.get("sources") or []
    if not isinstance(sources, list):
        return [f"{label}: knowledge.sources must be an array"]
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"{label}: knowledge.sources[{index}] is not an object")
            continue
        path = source.get("path")
        digest = source.get("sha256")
        commit = source.get("commit")
        prefix = f"{label}: knowledge.sources[{index}]"
        if not isinstance(path, str) or not path:
            errors.append(f"{prefix}: missing path")
            continue
        if not isinstance(digest, str):
            errors.append(f"{prefix}: missing sha256")
            continue
        local = Path(repo_root) / path
        checked = False
        if isinstance(commit, str) and commit:
            compact = commit.strip().lower().replace("_", "-")
            if compact in {"working-tree", "workingtree"} or re.fullmatch(
                r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit
            ) is None:
                errors.append(
                    f"{prefix}: commit must be a 40- or 64-character lowercase hexadecimal SHA, not {commit!r}"
                )
            else:
                blob = git_blob_sha256(repo_root, commit, path)
                if blob is not None:
                    checked = True
                    if blob != digest:
                        errors.append(
                            f"{prefix}: sha256 does not match git object {commit}:{path}"
                        )
        if local.is_file():
            actual = sha256_bytes(local.read_bytes())
            if actual != digest:
                errors.append(f"{prefix}: sha256 does not match the file on disk ({path})")
            checked = True
        if not checked:
            if source.get("repository"):
                continue
            errors.append(f"{prefix}: source file is missing ({path})")
    return errors


def check_interpretation(record: dict[str, Any], *, label: str) -> list[str]:
    interpretation = record.get("interpretation")
    if not isinstance(interpretation, dict):
        return [f"{label}: missing interpretation"]
    errors: list[str] = []
    kind = interpretation.get("kind")
    if kind in FORBIDDEN_INTERPRETATION_KINDS:
        errors.append(f"{label}: interpretation cannot be marked as source text")
    if interpretation.get("not_source_text") is not True:
        errors.append(f"{label}: interpretation.not_source_text must be true")
    if kind != "interpretation":
        errors.append(f"{label}: interpretation.kind must be 'interpretation'")
    return errors


def check_review_and_authorization(record: dict[str, Any], *, label: str) -> list[str]:
    errors: list[str] = []
    if record.get("review_status") == "accepted" and not has_human_decision(record):
        errors.append(f"{label}: review_status accepted requires a cited human decision record")
    auth = record.get("authorization") if isinstance(record.get("authorization"), dict) else {}
    if auth.get("inferred_from_test_pass") is True:
        errors.append(f"{label}: authorization cannot be set from a test pass")
    if auth.get("status") == "AUTHORIZED" and not has_human_decision(record):
        errors.append(f"{label}: AUTHORIZED status requires a cited human decision record")
    return errors


def check_local_test_locators(record: dict[str, Any], repo_root: Path, *, label: str) -> list[str]:
    errors: list[str] = []
    locators: list[Any] = []
    tests = record.get("tests") or []
    if isinstance(tests, list):
        locators.extend(tests)
    for req in record.get("requirements") or []:
        if isinstance(req, dict):
            locators.extend(req.get("test_locators") or [])
    for ev in record.get("evidence") or []:
        if isinstance(ev, dict) and isinstance(ev.get("locator"), dict):
            locators.append(ev["locator"])
    for loc in locators:
        if isinstance(loc, dict):
            for err in locator_exists(loc, repo_root):
                errors.append(f"{label}: {err}")
    return errors


def semantic_errors(record: dict[str, Any], repo_root: Path, *, label: str) -> list[str]:
    errors: list[str] = []
    errors.extend(check_rule_1_reference(record, repo_root, label=label))
    errors.extend(check_rule_1_assessment(record, repo_root, label=label))
    errors.extend(check_sources(record, repo_root, label=label))
    errors.extend(check_interpretation(record, label=label))
    errors.extend(check_review_and_authorization(record, label=label))
    errors.extend(check_local_test_locators(record, repo_root, label=label))
    return errors


def validate_record_data(record: dict[str, Any], repo_root: Path, *, label: str) -> list[str]:
    schema = load_json(SCHEMA_PATH)
    errors = validate_schema(record, schema)
    errors.extend(semantic_errors(record, repo_root, label=label))
    return errors


def validate_record_file(path: Path, repo_root: Path) -> list[str]:
    try:
        record = load_json(path)
    except json.JSONDecodeError as exc:
        return [f"{path.as_posix()}: invalid JSON ({exc})"]
    if not isinstance(record, dict):
        return [f"{path.as_posix()}: record must be an object"]
    rel = path.relative_to(repo_root).as_posix() if path.is_relative_to(repo_root) else path.as_posix()
    return validate_record_data(record, repo_root, label=rel)


def apply_correction(record: dict[str, Any], new_principle: str, *, reason: str = "correction") -> dict[str, Any]:
    updated = deepcopy(record)
    prior = deepcopy(record.get("interpretation") or {})
    history = list(updated.get("history") or [])
    history.append(
        {
            "preserved_principle": prior.get("principle", ""),
            "reason": reason,
            "prior_status": prior.get("status", ""),
        }
    )
    updated["history"] = history
    interpretation = deepcopy(prior)
    interpretation["principle"] = new_principle
    updated["interpretation"] = interpretation
    return updated


def iter_record_paths(repo_root: Path) -> list[Path]:
    records_dir = Path(repo_root) / "knowledge" / RECORDS_DIRNAME
    if not records_dir.is_dir():
        return []
    return sorted(path for path in records_dir.glob("*.json") if path.is_file())


def validate_tree(repo_root: Path) -> list[str]:
    repo_root = Path(repo_root)
    errors = check_rule_1_document(repo_root)
    schema_path = repo_root / "knowledge" / "schemas" / "knowledge-record.schema.json"
    if not schema_path.is_file():
        errors.append(f"missing {schema_path.as_posix()}")
    paths = iter_record_paths(repo_root)
    if not paths:
        errors.append("no knowledge records found under knowledge/records")
    for path in paths:
        errors.extend(validate_record_file(path, repo_root))
    self_assessment = repo_root / "knowledge" / "SELF_ASSESSMENT.json"
    if self_assessment.is_file():
        try:
            payload = load_json(self_assessment)
        except json.JSONDecodeError as exc:
            errors.append(f"knowledge/SELF_ASSESSMENT.json: invalid JSON ({exc})")
        else:
            if isinstance(payload, dict):
                errors.extend(check_rule_1_reference(payload, repo_root, label="knowledge/SELF_ASSESSMENT.json"))
                errors.extend(check_rule_1_assessment(payload, repo_root, label="knowledge/SELF_ASSESSMENT.json"))
            else:
                errors.append("knowledge/SELF_ASSESSMENT.json must be an object")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate knowledge records (fail closed).")
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="repository root (default: current directory)",
    )
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    errors = validate_tree(root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("knowledge records: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
