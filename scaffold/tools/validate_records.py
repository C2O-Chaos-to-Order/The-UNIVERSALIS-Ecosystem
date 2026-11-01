"""Validate standalone record files against one scaffold schema.

Usage:

    python scaffold/tools/validate_records.py <records-dir> [--schema NAME] [--json] [--recursive]

``validate_programme.py`` validates a whole programme package: manifest,
ledgers, links, counts and traceability. It has no entry point for a
directory of record files on their own. This tool fills that gap and does
nothing else. It reads each ``*.json`` file in one directory, asks whether
the object is structurally conformant with one schema in ``scaffold/schemas``,
and reports what it finds.

The rules are the structural ones: the file parses as a JSON object, every
field in the schema's ``required`` list is present, no field is present that
the schema does not declare, every ``enum`` and ``const`` value is inside its
declared set, and every ``type`` matches a declared JSON type. Nested objects
and arrays that the schema declares are checked by the same rules. Type
semantics are imported from ``validate_programme`` rather than rewritten, so
``integer`` means an ``int`` and never a ``bool`` or a float such as ``1.0``,
and ``number`` rejects a non-finite float.

A field whose value is the literal string ``"UNSPECIFIED"`` is reported as a
WARNING, not a failure: a record may declare a field unspecified rather than
invent a value. The exception is a field the schema constrains by ``enum`` or
``const``: there the schema's vocabulary governs, ``"UNSPECIFIED"`` is not in
it, and the record fails. This tool does not widen a schema's vocabulary.

An empty directory is an error, not a pass. A gate that found nothing to
check has cleared nothing, and a mistyped path must not read as a green
light. It exits 2, the same convention ``validate_programme.py`` uses for an
absent package directory.

What a pass proves: the record's keys, required fields, enumerated values,
constants and JSON types agree with the named schema.

What a pass does not prove: that the record is true, that the simulation it
describes was ever run, that the evidence was reviewed or accepted, or that
anything is validated, certified, production-ready or authorized. ``pattern``,
``minLength`` and ``minimum`` are not applied here; ``validate_programme.py``
applies them to a record inside a package.

Exit codes: 0 for no failures (warnings alone still exit 0), 1 when any
record fails, 2 when the run could not be performed at all.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from validate_programme import SCHEMA_DIR, load_schema, matches_type

UNSPECIFIED = "UNSPECIFIED"
SCHEMA_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
RENDER_LIMIT = 80

SCOPE = (
    "Structural schema conformance of standalone record files only. A pass "
    "proves that each record's keys, required fields, enumerated values, "
    "constants and JSON types agree with the named schema. It does not prove "
    "that a record is true, that the run it describes happened, or that "
    "anything was reviewed, accepted, validated, certified or authorized. "
    "pattern, minLength and minimum constraints are not applied here."
)


def schema_file(name: str) -> Path:
    """Return the schema path for ``name``, refusing to leave the schema dir.

    Accepts ``simulation_result``, ``simulation_result.schema`` and the full
    ``simulation_result.schema.json``, because the schemas on disk are named
    ``<name>.schema.json`` while the short name is what a caller types.
    """
    if not SCHEMA_NAME.fullmatch(name) or ".." in name or "/" in name or "\\" in name:
        raise ValueError(
            f"SCHEMA_NAME_INVALID: {name!r} must be a plain schema file name"
        )
    candidates = [name] if name.endswith(".json") else [f"{name}.json", f"{name}.schema.json"]
    for candidate in candidates:
        path = SCHEMA_DIR / candidate
        if path.is_file():
            return path
    available = ", ".join(
        sorted(item.name[: -len(".schema.json")] for item in SCHEMA_DIR.glob("*.schema.json"))
    )
    raise ValueError(
        f"SCHEMA_ABSENT: no schema matches {name!r} in {SCHEMA_DIR} ({available})"
    )


def record_files(directory: Path, recursive: bool) -> list[Path]:
    """Return the ``*.json`` files to check, sorted by path."""
    pattern = "**/*.json" if recursive else "*.json"
    return sorted(path for path in directory.glob(pattern) if path.is_file())


def json_type(value: object) -> str:
    """Name the JSON type of a parsed value, keeping ``bool`` out of ``integer``."""
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
    return "object"


def render(value: object, limit: int = RENDER_LIMIT) -> str:
    """Render a value for a one-line message, truncated to a readable width."""
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def field_label(path: str) -> str:
    return path or "(record)"


def schema_problems(value: object, node: dict, path: str) -> list[dict]:
    """Return every structural problem in ``value`` against schema ``node``."""
    problems: list[dict] = []

    if "const" in node and value != node["const"]:
        problems.append(
            {
                "field": field_label(path),
                "kind": "CONST",
                "reason": f"must be {render(node['const'])}, found {render(value)}",
            }
        )
        return problems
    if "enum" in node and value not in node["enum"]:
        problems.append(
            {
                "field": field_label(path),
                "kind": "ENUM",
                "reason": (
                    f"{render(value)} is not one of the {len(node['enum'])} "
                    f"permitted values {render(node['enum'])}"
                ),
            }
        )
        return problems
    declared = node.get("type")
    types = [declared] if isinstance(declared, str) else list(declared or [])
    if types and not matches_type(value, types):
        problems.append(
            {
                "field": field_label(path),
                "kind": "TYPE",
                "reason": (
                    f"must be {' or '.join(types)}, found {json_type(value)} "
                    f"{render(value)}"
                ),
            }
        )
        return problems

    if isinstance(value, dict):
        for key in node.get("required", []):
            if key not in value:
                problems.append(
                    {
                        "field": field_label(f"{path}.{key}" if path else key),
                        "kind": "MISSING_REQUIRED",
                        "reason": "required field is missing",
                    }
                )
        properties = node.get("properties") or {}
        for key in value:
            child = f"{path}.{key}" if path else key
            if properties and key not in properties:
                problems.append(
                    {
                        "field": child,
                        "kind": "UNKNOWN_FIELD",
                        "reason": (
                            "field is not declared by the schema"
                            if path
                            else f"field is not declared by the schema ({len(properties)} declared)"
                        ),
                    }
                )
            elif isinstance(properties.get(key), dict):
                problems.extend(schema_problems(value[key], properties[key], child))
    elif isinstance(value, list):
        items = node.get("items")
        if isinstance(items, dict):
            for index, item in enumerate(value):
                problems.extend(schema_problems(item, items, f"{path}[{index}]"))
    return problems


def unspecified_paths(value: object, path: str = "") -> list[str]:
    """Return the dotted paths whose value is the literal ``UNSPECIFIED`` sentinel."""
    if isinstance(value, str):
        return [path] if value == UNSPECIFIED else []
    if isinstance(value, dict):
        found: list[str] = []
        for key, item in value.items():
            found.extend(unspecified_paths(item, f"{path}.{key}" if path else key))
        return found
    if isinstance(value, list):
        found = []
        for index, item in enumerate(value):
            found.extend(unspecified_paths(item, f"{path}[{index}]"))
        return found
    return []


def top_field(path: str) -> str:
    """Reduce a dotted path to the top-level field it sits under."""
    return path.split(".", 1)[0].split("[", 1)[0]


def read_record(path: Path) -> tuple[object | None, str | None]:
    """Return the parsed JSON, or a reason the file could not be read as JSON."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None, "file is not valid UTF-8 and cannot be read as JSON"
    except OSError as exc:
        return None, f"file could not be read ({exc.strerror or exc})"
    try:
        return json.loads(text), None
    except json.JSONDecodeError as exc:
        return None, f"not valid JSON (line {exc.lineno} column {exc.colno}: {exc.msg})"


def validate_directory(directory: Path, schema_name: str, recursive: bool = False) -> dict:
    """Check every record file in ``directory`` and return the report payload."""
    if not directory.is_dir():
        raise FileNotFoundError(f"DIRECTORY_ABSENT: directory does not exist: {directory}")
    schema_path = schema_file(schema_name)
    schema = load_schema(schema_path.name)
    files = record_files(directory, recursive)
    if not files:
        scope = "recursively" if recursive else "non-recursively"
        raise ValueError(
            f"NO_RECORDS: no *.json files found in {directory} (searched {scope}). "
            "A directory with no records clears nothing."
        )

    failures: list[dict] = []
    warnings: list[dict] = []
    # Per-field sets of file names, so a record that leaves two sub-fields
    # unspecified counts once for that field rather than twice.
    unspecified: dict[str, set[str]] = {}
    failed_files = 0

    for path in files:
        # Relative to the directory asked about, so recursive mode cannot show
        # two different files under the same name.
        label = path.relative_to(directory).as_posix()
        record, error = read_record(path)
        if error is not None:
            failures.append(
                {"file": label, "field": "(record)", "kind": "NOT_JSON", "reason": error}
            )
            failed_files += 1
            continue
        if not isinstance(record, dict):
            failures.append(
                {
                    "file": label,
                    "field": "(record)",
                    "kind": "NOT_OBJECT",
                    "reason": f"must be a JSON object, found {json_type(record)}",
                }
            )
            failed_files += 1
            continue

        problems = schema_problems(record, schema, "")
        for problem in problems:
            failures.append({"file": label, **problem})
        if problems:
            failed_files += 1

        # A path that already failed is not a permitted "unspecified": the
        # schema enumerated the field and UNSPECIFIED is not in its
        # vocabulary. Reporting it twice would blur that distinction.
        failed_paths = {problem["field"] for problem in problems}
        for hit in unspecified_paths(record):
            if field_label(hit) in failed_paths:
                continue
            warnings.append(
                {
                    "file": label,
                    "field": field_label(hit),
                    "reason": "declares the field UNSPECIFIED rather than a value",
                }
            )
            unspecified.setdefault(top_field(hit), set()).add(label)

    # Report order must not depend on the key order inside a record file.
    warnings.sort(key=lambda item: (item["file"], item["field"]))
    ok = not failures
    count = len(files)
    if ok:
        verdict = (
            f"VERDICT: PASS — {count} record(s) checked, 0 failed, "
            f"{len(warnings)} unspecified warning(s)"
        )
    else:
        verdict = (
            f"VERDICT: FAIL — {failed_files} of {count} record(s) failed "
            f"({len(failures)} problem(s)), {len(warnings)} unspecified warning(s)"
        )

    return {
        "scope": SCOPE,
        "directory": str(directory.resolve()),
        "schema": schema_path.name,
        "recursive": recursive,
        "required_fields": len(schema.get("required", [])),
        "declared_fields": len(schema.get("properties", {})),
        "records_checked": count,
        "records_failed": failed_files,
        "ok": ok,
        "failures": failures,
        "warnings": warnings,
        "unspecified_counts": {
            field: len(names) for field, names in sorted(unspecified.items())
        },
        "verdict": verdict,
    }


def render_human(report: dict) -> str:
    """Render the report as readable lines, problems first, verdict last."""
    lines = [
        f"schema: {report['schema']} — {report['required_fields']} required fields, "
        f"{report['declared_fields']} declared",
        f"records checked: {report['records_checked']} file(s) in {report['directory']}"
        f" ({'recursive' if report['recursive'] else 'non-recursive'})",
    ]
    by_file: dict[str, list[dict]] = {}
    for failure in report["failures"]:
        by_file.setdefault(failure["file"], []).append(failure)
    if by_file:
        lines.append("")
    for name in sorted(by_file):
        lines.append(name)
        for failure in by_file[name]:
            lines.append(
                f"  FAIL {failure['kind']} {failure['field']}: {failure['reason']}"
            )
    if report["unspecified_counts"]:
        lines.append("")
        lines.append("UNSPECIFIED values — warnings, not failures:")
        for field, count in report["unspecified_counts"].items():
            lines.append(f"  {field}: {count} record(s)")
    if not report["failures"] and not report["unspecified_counts"]:
        lines.append("")
        lines.append("  (no problems found)")
    lines.append("")
    lines.append(report["verdict"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check standalone record JSON files against a scaffold schema. "
            "A pass is structural conformance only, not validation of a finding."
        )
    )
    parser.add_argument("records", help="Directory holding the record files")
    parser.add_argument(
        "--schema",
        default="simulation_result",
        help="Schema name in scaffold/schemas, with or without .json "
        "(default: simulation_result)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Write the report as JSON instead of text"
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search subdirectories as well (default: this directory only)",
    )
    args = parser.parse_args(argv)
    try:
        report = validate_directory(Path(args.records), args.schema, args.recursive)
    except (ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.json:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_human(report) + "\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
