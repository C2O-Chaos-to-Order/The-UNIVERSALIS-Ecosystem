"""Validate standalone record files against one scaffold schema.

Usage:

    python scaffold/tools/validate_records.py <records-dir> [--schema NAME] [--json] [--recursive]

``validate_programme.py`` validates a whole programme package: manifest,
ledgers, links, counts and traceability. It has no entry point for a
directory of record files on their own. This tool fills that gap and does
nothing else. It reads each ``*.json`` file in one directory, asks whether
the object conforms to one schema in ``scaffold/schemas``, and reports what
it finds.

SUPPORTED KEYWORDS
------------------
``type``, ``enum``, ``const``, ``required``, ``properties``,
``additionalProperties``, ``items``, ``minLength``, ``maxLength``,
``pattern``, ``minimum``, ``maximum``.

Every keyword in that list is applied with JSON Schema semantics, and each
one has positive, negative and boundary fixtures in
``scaffold/tests/test_validate_records.py``.

UNSUPPORTED KEYWORDS ARE AN ERROR, NOT A SILENT PASS
----------------------------------------------------
If a schema uses a keyword this tool does not implement (``$ref``,
``oneOf``, ``anyOf``, ``allOf``, ``not``, ``format``, ``minItems``,
``maxItems``, ``uniqueItems``, ``multipleOf``, ``exclusiveMinimum``,
``exclusiveMaximum``, ``patternProperties``, ``propertyNames``,
``dependentRequired``, ``if``/``then``/``else``, ``contains``, ``prefixItems``),
the run stops with exit 2 and names the keyword and the schema path. A
validator that ignored a constraint it does not understand would report a
pass it has not earned, which is the specific failure mode this tool exists
to prevent. The check is recursive, so an unsupported keyword buried in one
nested subschema stops the run too.

This is therefore NOT a complete JSON Schema implementation. It is a
deliberate subset, sized to the keyword set the scaffold's own schemas use,
and it refuses to guess outside that subset. It does not claim to validate
against the JSON Schema specification as a whole.

SEMANTICS THAT DIFFER FROM A NAIVE READING
------------------------------------------
``additionalProperties`` follows the specification, including its default.
JSON Schema permits extra properties unless a schema says
``"additionalProperties": false``. None of the scaffold's schemas declares
it, so extra properties are permitted here and are reported as a WARNING,
not a failure. A schema that wants them forbidden must say so. Rejecting
them unconditionally would be this tool inventing a constraint the schema
never stated, and the two scaffold validators previously disagreed on
exactly this point.

``enum`` and ``const`` compare by JSON type as well as value, so ``true``
does not equal ``1`` and ``1`` does not equal ``1.0``. In Python those pairs
compare equal, which would let a boolean satisfy an integer enum.

``pattern`` uses ``re.search`` as the specification requires, not
``re.fullmatch``: an unanchored pattern is a substring match, and anchoring
it here would reject values the schema permits.

TYPE SEMANTICS
--------------
Type checking is imported from ``validate_programme`` rather than rewritten,
so ``integer`` means an ``int`` and never a ``bool`` or a float such as
``1.0``, and ``number`` rejects a non-finite float.

THE UNSPECIFIED SENTINEL
------------------------
A field whose value is the literal string ``"UNSPECIFIED"`` is reported as a
WARNING, not a failure: a record may declare a field unspecified rather than
invent a value. The exception is a field the schema constrains by ``enum`` or
``const``: there the schema's vocabulary governs, ``"UNSPECIFIED"`` is not in
it, and the record fails. This tool does not widen a schema's vocabulary.

EMPTY INPUT IS AN ERROR
-----------------------
An empty directory is an error, not a pass. A gate that found nothing to
check has cleared nothing, and a mistyped path must not read as a green
light. It exits 2, the same convention ``validate_programme.py`` uses for an
absent package directory.

WHAT A PASS PROVES, AND WHAT IT DOES NOT
----------------------------------------
A pass proves that the record's keys, required fields, enumerated values,
constants, JSON types, string lengths, patterns and numeric bounds agree
with the named schema under the keyword subset above.

A pass does not prove that the record is true, that the simulation it
describes was ever run, that the evidence was reviewed or accepted, that
the research behind it was conducted, or that anything is validated,
certified, production-ready or authorized. Structural conformance is not
scientific validation and never substitutes for it.

Exit codes: 0 for no failures (warnings alone still exit 0), 1 when any
record fails, 2 when the run could not be performed at all, which includes
an unsupported schema keyword.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from validate_programme import SCHEMA_DIR, is_number, load_schema, matches_type

UNSPECIFIED = "UNSPECIFIED"
SCHEMA_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
RENDER_LIMIT = 80

SCOPE = (
    "Schema conformance of standalone record files under a documented keyword "
    "subset. A pass proves that each record's keys, required fields, enumerated "
    "values, constants, JSON types, string lengths, patterns and numeric bounds "
    "agree with the named schema. It does not prove that a record is true, that "
    "the run it describes happened, that any research was conducted, or that "
    "anything was reviewed, accepted, validated, certified or authorized. "
    "Unsupported schema keywords stop the run rather than being ignored."
)

# Every keyword this tool implements, with JSON Schema semantics.
SUPPORTED_KEYWORDS = frozenset(
    {
        "type",
        "enum",
        "const",
        "required",
        "properties",
        "additionalProperties",
        "items",
        "minLength",
        "maxLength",
        "pattern",
        "minimum",
        "maximum",
    }
)

# Annotation and identification keywords carry no assertion. They may appear
# anywhere and are skipped by the support gate.
ANNOTATION_KEYWORDS = frozenset(
    {
        "$schema",
        "$id",
        "$comment",
        "title",
        "description",
        "default",
        "examples",
        "deprecated",
        "readOnly",
        "writeOnly",
    }
)

# Keywords that do assert but which this tool does not implement. Listing them
# explicitly means a schema cannot slip one past the gate by using a name the
# gate has never heard of: anything unknown is refused too.
KNOWN_UNSUPPORTED_KEYWORDS = frozenset(
    {
        "$ref",
        "$defs",
        "definitions",
        "oneOf",
        "anyOf",
        "allOf",
        "not",
        "if",
        "then",
        "else",
        "format",
        "minItems",
        "maxItems",
        "uniqueItems",
        "contains",
        "prefixItems",
        "patternProperties",
        "propertyNames",
        "dependentRequired",
        "dependentSchemas",
        "multipleOf",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "minProperties",
        "maxProperties",
        "unevaluatedProperties",
        "unevaluatedItems",
        "contentEncoding",
        "contentMediaType",
    }
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


class UnsupportedKeyword(ValueError):
    """A schema uses a keyword this validator does not implement."""


def unsupported_keywords(schema: object, path: str = "") -> list[tuple[str, str]]:
    """Return ``(schema path, keyword)`` for every keyword the tool cannot apply.

    Walks the whole schema, including nested subschemas, so an unsupported
    keyword cannot hide inside ``properties`` or ``items``. Returns an empty
    list when every assertion keyword is supported.

    Structural keys inside ``properties`` are field names, not keywords, so the
    walk descends into each property's subschema and does not judge the names
    themselves. The same applies to keys under ``$defs``-style maps, which this
    tool refuses wholesale anyway.
    """
    found: list[tuple[str, str]] = []

    def walk(node: object, where: str) -> None:
        if not isinstance(node, dict):
            if isinstance(node, list):
                for index, item in enumerate(node):
                    walk(item, f"{where}[{index}]")
            return
        for key, value in node.items():
            here = f"{where}.{key}" if where else key
            if key in ("properties", "patternProperties", "dependentSchemas", "$defs", "definitions"):
                # These maps hold field names or definition names, not keywords.
                if key in KNOWN_UNSUPPORTED_KEYWORDS:
                    found.append((where or "(root)", key))
                    continue
                if isinstance(value, dict):
                    for name, subschema in value.items():
                        walk(subschema, f"{here}.{name}")
                continue
            if key in ANNOTATION_KEYWORDS:
                continue
            if key not in SUPPORTED_KEYWORDS:
                found.append((where or "(root)", key))
                continue
            walk(value, here)

    walk(schema, path)
    return found


def require_supported_keywords(schema: dict, schema_name: str) -> None:
    """Raise ``UnsupportedKeyword`` naming every keyword the tool cannot apply."""
    problems = unsupported_keywords(schema)
    if not problems:
        return
    listed = ", ".join(f"{keyword!r} at {where}" for where, keyword in problems)
    raise UnsupportedKeyword(
        f"UNSUPPORTED_KEYWORD: schema {schema_name} uses {listed}. "
        "This tool implements only "
        + ", ".join(sorted(SUPPORTED_KEYWORDS))
        + ". Ignoring an unimplemented constraint would report a pass that was "
        "not earned, so the run stops instead."
    )


def json_equal(left: object, right: object) -> bool:
    """Compare two JSON values by type as well as by value.

    ``True == 1`` and ``1 == 1.0`` in Python, but JSON distinguishes boolean,
    integer and number. Without this, a boolean would satisfy an integer enum
    and ``1.0`` would satisfy ``1``.
    """
    if isinstance(left, bool) != isinstance(right, bool):
        return False
    if isinstance(left, bool):
        return left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        if isinstance(left, float) and left.is_integer() and not isinstance(right, float):
            return left == right
        if isinstance(right, float) and right.is_integer() and not isinstance(left, float):
            return left == right
        return type(left) is type(right) and left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(
            json_equal(a, b) for a, b in zip(left, right)
        )
    if isinstance(left, dict):
        return set(left) == set(right) and all(json_equal(left[k], right[k]) for k in left)
    return left == right


def matches_any_json(value: object, candidates: list) -> bool:
    """True when ``value`` equals any candidate under JSON type-aware equality."""
    return any(json_equal(value, candidate) for candidate in candidates)


def schema_problems(value: object, node: dict, path: str) -> list[dict]:
    """Return every conformance problem in ``value`` against schema ``node``.

    Applies the supported keyword subset with JSON Schema semantics. An
    ``enum`` or ``const`` mismatch and a ``type`` mismatch each stop descent
    into that value, because every further constraint would be checked against
    a value the schema has already rejected.
    """
    problems: list[dict] = []

    def add(kind: str, reason: str, where: str | None = None) -> None:
        problems.append({"field": field_label(where if where is not None else path), "kind": kind, "reason": reason})

    if "const" in node and not json_equal(value, node["const"]):
        add("CONST", f"must be {render(node['const'])}, found {render(value)}")
        return problems
    if "enum" in node and not matches_any_json(value, node["enum"]):
        add(
            "ENUM",
            (
                f"{render(value)} is not one of the {len(node['enum'])} "
                f"permitted values {render(node['enum'])}"
            ),
        )
        return problems

    declared = node.get("type")
    types = [declared] if isinstance(declared, str) else list(declared or [])
    if types and not matches_type(value, types):
        add(
            "TYPE",
            f"must be {' or '.join(types)}, found {json_type(value)} {render(value)}",
        )
        return problems

    # String constraints apply only to strings, as the specification requires.
    if isinstance(value, str):
        min_length = node.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            add(
                "MIN_LENGTH",
                f"must be at least {min_length} character(s), found {len(value)} {render(value)}",
            )
        max_length = node.get("maxLength")
        if isinstance(max_length, int) and len(value) > max_length:
            add(
                "MAX_LENGTH",
                f"must be at most {max_length} character(s), found {len(value)}",
            )
        pattern = node.get("pattern")
        if isinstance(pattern, str):
            # The specification specifies a substring match, not a whole-string
            # match. Anchoring an unanchored pattern here would reject values
            # the schema permits.
            try:
                matched = re.search(pattern, value) is not None
            except re.error as exc:
                raise UnsupportedKeyword(
                    f"UNSUPPORTED_PATTERN: {field_label(path)} pattern {pattern!r} "
                    f"is not a valid regular expression ({exc})"
                ) from exc
            if not matched:
                add("PATTERN", f"does not match the required pattern {pattern!r}")

    # Numeric bounds apply to numbers only, and never to booleans.
    if is_number(value):
        minimum = node.get("minimum")
        if is_number(minimum) and value < minimum:
            add("MINIMUM", f"must be at least {minimum}, found {value}")
        maximum = node.get("maximum")
        if is_number(maximum) and value > maximum:
            add("MAXIMUM", f"must be at most {maximum}, found {value}")

    if isinstance(value, dict) and ("properties" in node or "additionalProperties" in node or "required" in node):
        for key in node.get("required", []):
            if key not in value:
                add(
                    "MISSING_REQUIRED",
                    "required field is missing",
                    f"{path}.{key}" if path else key,
                )
        properties = node.get("properties") or {}
        extra = node.get("additionalProperties", True)
        for key in value:
            child = f"{path}.{key}" if path else key
            if key in properties and isinstance(properties[key], dict):
                problems.extend(schema_problems(value[key], properties[key], child))
            elif key not in properties:
                # JSON Schema permits undeclared properties unless the schema
                # sets additionalProperties to false. The record may not state a
                # constraint the schema never made.
                if extra is False:
                    add(
                        "UNKNOWN_FIELD",
                        "field is not declared by the schema and the schema forbids additional properties",
                        child,
                    )
                elif isinstance(extra, dict):
                    problems.extend(schema_problems(value[key], extra, child))
                else:
                    add(
                        "UNDECLARED_FIELD",
                        "field is not declared by the schema; permitted, because the schema does not set additionalProperties: false",
                        child,
                    )
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
    require_supported_keywords(schema, schema_path.name)
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
    permitted_extra: list[dict] = []
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
        # Undeclared-but-permitted fields are reported, not failed: the schema
        # did not forbid them. Every other kind is a failure.
        permitted = [p for p in problems if p["kind"] == "UNDECLARED_FIELD"]
        problems = [p for p in problems if p["kind"] != "UNDECLARED_FIELD"]
        for problem in problems:
            failures.append({"file": label, **problem})
        if problems:
            failed_files += 1

        # A path that already failed is not a permitted "unspecified": the
        # schema enumerated the field and UNSPECIFIED is not in its
        # vocabulary. Reporting it twice would blur that distinction.
        for extra in permitted:
            permitted_extra.append(
                {
                    "file": label,
                    "field": extra["field"],
                    "reason": "field is not declared by the schema, and the schema permits it",
                }
            )

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
    permitted_extra.sort(key=lambda item: (item["file"], item["field"]))
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
        "permitted_extra_fields": permitted_extra,
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
