"""Deterministic, non-executing construction from declarative JSON specs."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

SPEC_VERSION = "c2o-build-spec/v0.1"
SAFE_PATH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")


class BuildError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_spec(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read JSON specification: {exc}") from exc
    validate_spec(data)
    return data


def validate_spec(spec: dict[str, Any]) -> None:
    if not isinstance(spec, dict):
        raise BuildError("specification must be a JSON object")
    if spec.get("spec_version") != SPEC_VERSION:
        raise BuildError(f"spec_version must be {SPEC_VERSION}")
    for key in ("tool_id", "name", "version", "target_ecosystem", "files"):
        if key not in spec:
            raise BuildError(f"missing required field: {key}")
    if not isinstance(spec["tool_id"], str) or not re.fullmatch(r"[a-z][a-z0-9-]{1,62}", spec["tool_id"]):
        raise BuildError("tool_id must be a lowercase slug")
    if spec["target_ecosystem"] not in ("universalis", "c2o"):
        raise BuildError("target_ecosystem must be universalis or c2o")
    if not isinstance(spec["files"], list) or not spec["files"]:
        raise BuildError("files must be a non-empty array")
    seen: set[str] = set()
    for item in spec["files"]:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("content"), str):
            raise BuildError("each file requires string path and content")
        path = item["path"]
        parts = Path(path).parts
        if not SAFE_PATH.fullmatch(path) or path.startswith("/") or "\\" in path or ".." in parts:
            raise BuildError(f"unsafe output path: {path}")
        if path in seen:
            raise BuildError(f"duplicate output path: {path}")
        seen.add(path)


def build_plan(spec: dict[str, Any]) -> dict[str, Any]:
    validate_spec(spec)
    return {
        "plan_version": "c2o-build-plan/v0.1",
        "tool_id": spec["tool_id"],
        "target_ecosystem": spec["target_ecosystem"],
        "version": spec["version"],
        "files": [{"path": f["path"], "bytes": len(f["content"].encode("utf-8"))} for f in spec["files"]],
        "execution_policy": "generated code is never executed by this engine",
        "promotion": "owner review required; build success is not release authorization",
    }


def build(spec_path: Path, output_dir: Path) -> dict[str, Any]:
    spec = load_spec(spec_path)
    plan = build_plan(spec)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, str] = {}
    for item in spec["files"]:
        destination = output_dir / item["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = item["content"].encode("utf-8")
        destination.write_bytes(payload)
        manifest[item["path"]] = sha256_bytes(payload)
    record = {
        "record_version": "c2o-build-record/v0.1",
        "tool_id": spec["tool_id"],
        "name": spec["name"],
        "version": spec["version"],
        "target_ecosystem": spec["target_ecosystem"],
        "plan": plan,
        "files": manifest,
        "status": "BUILT_NOT_PROMOTED",
    }
    (output_dir / "build-record.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return record


def verify(output_dir: Path) -> dict[str, Any]:
    record_path = output_dir / "build-record.json"
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"missing or invalid build record: {exc}") from exc
    results = []
    for relative, expected in record.get("files", {}).items():
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or "\\" in relative:
            results.append({"path": relative, "ok": False, "reason": "unsafe manifest path"})
            continue
        target = output_dir / path
        if not target.is_file():
            results.append({"path": relative, "ok": False, "reason": "missing"})
            continue
        actual = sha256_bytes(target.read_bytes())
        results.append({"path": relative, "ok": actual == expected, "expected": expected, "actual": actual})
    ok = bool(results) and all(item["ok"] for item in results)
    return {"verification_version": "c2o-build-verification/v0.1", "ok": ok, "checked": len(results), "results": results}
