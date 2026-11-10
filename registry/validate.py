"""Fail-closed validator for the public Tool and Evidence registries.

Unknown instance fields, missing required fields, unsupported schema
keywords, bad identifiers, and evidence or test locators that do not
resolve are errors. The validator uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_REPO_ROOT = PACKAGE_DIR.parent

TOOL_SCHEMA_PATH = PACKAGE_DIR / "schemas" / "tool-record.schema.json"
EVIDENCE_SCHEMA_PATH = PACKAGE_DIR / "schemas" / "evidence-record.schema.json"

# Schema keywords this validator implements. Any other keyword is an error
# so validation cannot silently ignore a constraint.
SUPPORTED_SCHEMA_KEYS = {
    "$schema",
    "$id",
    "title",
    "description",
    "type",
    "properties",
    "required",
    "additionalProperties",
    "items",
    "enum",
    "const",
    "pattern",
    "minLength",
    "maxLength",
    "minItems",
    "maxItems",
}

FORBIDDEN_FIELD_NAMES = frozenset({"score", "confidence"})

JSON_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
}


class ValidationError(Exception):
    """A single validation failure with a JSON-pointer-like path."""


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _is_json_type(value: Any, expected: str) -> bool:
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    expected_type = JSON_TYPES.get(expected)
    if expected_type is None:
        return False
    if expected == "string":
        return isinstance(value, str)
    return isinstance(value, expected_type)


def check_schema_supported(schema: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if not isinstance(schema, dict):
        return [f"{path}: schema must be an object"]
    for key in schema:
        if key not in SUPPORTED_SCHEMA_KEYS:
            errors.append(
                f"{path}: unsupported schema keyword {key!r} (fail closed)"
            )
    if "properties" in schema:
        properties = schema["properties"]
        if not isinstance(properties, dict):
            errors.append(f"{path}.properties: must be an object")
        else:
            for name, subschema in properties.items():
                errors.extend(check_schema_supported(subschema, f"{path}.properties.{name}"))
    if "items" in schema:
        errors.extend(check_schema_supported(schema["items"], f"{path}.items"))
    return errors


def validate_instance(instance: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    errors.extend(check_schema_supported(schema, f"{path}<schema>"))

    expected_type = schema.get("type")
    if expected_type is not None and not _is_json_type(instance, expected_type):
        errors.append(f"{path}: expected type {expected_type}, got {type(instance).__name__}")
        return errors

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {instance!r}")

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value {instance!r} is not in enum {schema['enum']!r}")

    if isinstance(instance, str):
        pattern = schema.get("pattern")
        if pattern is not None and re.search(pattern, instance) is None:
            errors.append(f"{path}: value {instance!r} does not match pattern {pattern!r}")
        min_length = schema.get("minLength")
        if min_length is not None and len(instance) < min_length:
            errors.append(f"{path}: string shorter than minLength {min_length}")
        max_length = schema.get("maxLength")
        if max_length is not None and len(instance) > max_length:
            errors.append(f"{path}: string longer than maxLength {max_length}")

    if isinstance(instance, list):
        min_items = schema.get("minItems")
        if min_items is not None and len(instance) < min_items:
            errors.append(f"{path}: array shorter than minItems {min_items}")
        max_items = schema.get("maxItems")
        if max_items is not None and len(instance) > max_items:
            errors.append(f"{path}: array longer than maxItems {max_items}")
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, item in enumerate(instance):
                errors.extend(validate_instance(item, item_schema, f"{path}[{index}]"))

    if isinstance(instance, dict):
        extra_forbidden = FORBIDDEN_FIELD_NAMES.intersection(instance)
        for name in sorted(extra_forbidden):
            errors.append(f"{path}.{name}: field {name!r} is not allowed")

        required = schema.get("required", [])
        for name in required:
            if name not in instance:
                errors.append(f"{path}.{name}: missing required field")

        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", False)
        for name, value in instance.items():
            if name in properties:
                errors.extend(
                    validate_instance(value, properties[name], f"{path}.{name}")
                )
            elif additional is False:
                errors.append(f"{path}.{name}: unknown field {name!r} (fail closed)")
            elif isinstance(additional, dict):
                errors.extend(
                    validate_instance(value, additional, f"{path}.{name}")
                )

    return errors


def collect_forbidden_fields(instance: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(instance, dict):
        for name, value in instance.items():
            child = f"{path}.{name}"
            if name in FORBIDDEN_FIELD_NAMES:
                errors.append(f"{child}: field {name!r} is not allowed")
            errors.extend(collect_forbidden_fields(value, child))
    elif isinstance(instance, list):
        for index, value in enumerate(instance):
            errors.extend(collect_forbidden_fields(value, f"{path}[{index}]"))
    return errors


def _path_exists(repo_root: Path, rel: str) -> bool:
    return (repo_root / rel).exists()


def check_test_locator(locator: dict[str, Any], repo_root: Path, path: str) -> list[str]:
    errors: list[str] = []
    rel = locator.get("path")
    if not isinstance(rel, str) or not rel:
        errors.append(f"{path}.path: missing test locator path")
        return errors
    target = repo_root / rel
    if not target.exists():
        errors.append(f"{path}.path: test locator {rel!r} does not exist")
        return errors
    if locator.get("kind") == "unittest_dir":
        if not target.is_dir():
            errors.append(f"{path}.path: unittest_dir {rel!r} is not a directory")
        elif not any(target.glob("test_*.py")):
            errors.append(
                f"{path}.path: unittest_dir {rel!r} contains no test_*.py files"
            )
    if locator.get("kind") == "workflow_file" and not target.is_file():
        errors.append(f"{path}.path: workflow_file {rel!r} is not a file")
    return errors


def check_evidence_locator(record: dict[str, Any], repo_root: Path, path: str) -> list[str]:
    errors: list[str] = []
    locator = record.get("locator")
    if not isinstance(locator, dict):
        errors.append(f"{path}.locator: missing locator object")
        return errors
    kind = locator.get("kind")
    if kind == "local_path":
        rel = locator.get("path")
        if not isinstance(rel, str) or not rel:
            errors.append(f"{path}.locator.path: local_path evidence requires path")
        elif not _path_exists(repo_root, rel):
            errors.append(
                f"{path}.locator.path: evidence link points to missing path {rel!r}"
            )
        elif record.get("kind") == "unittest_suite":
            target = repo_root / rel
            if not target.is_dir() or not any(target.glob("test_*.py")):
                errors.append(
                    f"{path}.locator.path: evidence link points to a missing test at {rel!r}"
                )
        if "command" not in locator:
            errors.append(f"{path}.locator.command: local_path evidence requires command")
    elif kind == "github_actions_run":
        for field in ("url", "run_id", "head_sha", "workflow_name"):
            if field not in locator:
                errors.append(f"{path}.locator.{field}: github_actions_run requires {field}")
    else:
        errors.append(f"{path}.locator.kind: unknown locator kind {kind!r}")
    return errors


def _iter_record_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.glob("*.json") if path.is_file())


def validate_registry(repo_root: Path | None = None) -> list[str]:
    repo_root = (repo_root or DEFAULT_REPO_ROOT).resolve()
    errors: list[str] = []

    try:
        tool_schema = load_json(TOOL_SCHEMA_PATH)
        evidence_schema = load_json(EVIDENCE_SCHEMA_PATH)
    except OSError as exc:
        return [f"unable to load schemas: {exc}"]

    tools_dir = repo_root / "registry" / "tools"
    evidence_dir = repo_root / "registry" / "evidence"
    if not tools_dir.is_dir():
        errors.append(f"{tools_dir}: tools directory is missing")
    if not evidence_dir.is_dir():
        errors.append(f"{evidence_dir}: evidence directory is missing")
    if errors:
        return errors

    tools: dict[str, dict[str, Any]] = {}
    evidence: dict[str, dict[str, Any]] = {}

    for path in _iter_record_files(tools_dir):
        pointer = f"registry/tools/{path.name}"
        try:
            record = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{pointer}: unable to read JSON ({exc})")
            continue
        errors.extend(validate_instance(record, tool_schema, pointer))
        errors.extend(collect_forbidden_fields(record, pointer))
        if isinstance(record, dict) and "id" in record:
            if path.stem != record["id"]:
                errors.append(
                    f"{pointer}: filename stem {path.stem!r} does not match id {record['id']!r}"
                )
            tools[str(record["id"])] = record
        locators = record.get("test_locators") if isinstance(record, dict) else None
        if isinstance(locators, list):
            for index, locator in enumerate(locators):
                if isinstance(locator, dict):
                    errors.extend(
                        check_test_locator(
                            locator, repo_root, f"{pointer}.test_locators[{index}]"
                        )
                    )

    for path in _iter_record_files(evidence_dir):
        pointer = f"registry/evidence/{path.name}"
        try:
            record = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{pointer}: unable to read JSON ({exc})")
            continue
        errors.extend(validate_instance(record, evidence_schema, pointer))
        errors.extend(collect_forbidden_fields(record, pointer))
        if isinstance(record, dict) and "id" in record:
            if path.stem != record["id"]:
                errors.append(
                    f"{pointer}: filename stem {path.stem!r} does not match id {record['id']!r}"
                )
            evidence[str(record["id"])] = record
            errors.extend(check_evidence_locator(record, repo_root, pointer))

    for tool_id, record in tools.items():
        pointer = f"registry/tools/{tool_id}.json"
        for index, evidence_id in enumerate(record.get("evidence_ids") or []):
            if evidence_id not in evidence:
                errors.append(
                    f"{pointer}.evidence_ids[{index}]: evidence link {evidence_id!r} "
                    "points to a missing evidence record"
                )
        for index, locator in enumerate(record.get("test_locators") or []):
            if not isinstance(locator, dict):
                continue
            rel = locator.get("path")
            if isinstance(rel, str) and not _path_exists(repo_root, rel):
                errors.append(
                    f"{pointer}.test_locators[{index}].path: evidence link "
                    f"points to a missing test at {rel!r}"
                )

    for evidence_id, record in evidence.items():
        pointer = f"registry/evidence/{evidence_id}.json"
        for index, tool_id in enumerate(record.get("tool_ids") or []):
            if tool_id not in tools:
                errors.append(
                    f"{pointer}.tool_ids[{index}]: tool link {tool_id!r} "
                    "points to a missing tool record"
                )

    # Deduplicate while preserving order (schema + explicit forbidden checks
    # can report the same field twice).
    seen: set[str] = set()
    unique: list[str] = []
    for error in errors:
        if error not in seen:
            seen.add(error)
            unique.append(error)
    return unique


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the public Tool and Evidence registries (fail closed)."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_REPO_ROOT,
        help="repository root containing registry/",
    )
    args = parser.parse_args(argv)
    errors = validate_registry(args.root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"{len(errors)} validation error(s)", file=sys.stderr)
        return 1
    print("registry ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
