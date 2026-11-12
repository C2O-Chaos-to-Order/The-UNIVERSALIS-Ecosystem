#!/usr/bin/env python3
"""Validate portable platform-interoperability contracts and semantic safeguards."""
from __future__ import annotations
import copy, json, sys
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "schemas/platform/platform-interoperability-contracts.v1.schema.json").read_text())
FIXTURE = json.loads((ROOT / "examples/platform/platform-interoperability-fixtures.v1.json").read_text())
KEYS = {
    "os_artifact":"osArtifact", "runtime_profile":"runtimeProfile", "skill_manifest":"skillManifest",
    "workflow_blueprint":"workflowBlueprint", "cicd_event":"cicdEvent", "telemetry_record":"telemetryRecord",
    "network_route":"networkRoute", "storage_interface":"storageInterface", "evaluation_receipt":"evaluationReceipt",
}
REQUIRED_TYPES = set(KEYS)

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def validate_record(kind: str, record: dict) -> None:
    require(kind in KEYS, f"unsupported record type: {kind}")
    view = {"$schema":SCHEMA["$schema"], "$defs":SCHEMA["$defs"], "$ref":"#/$defs/" + KEYS[kind]}
    Draft202012Validator(view, format_checker=FormatChecker()).validate(record)

def records_by_type(package: dict) -> dict:
    records = {}
    for entry in package["records"]:
        kind = entry["record_type"]
        require(kind not in records, f"duplicate record type: {kind}")
        validate_record(kind, entry["record"])
        records[kind] = entry["record"]
    require(set(records) == REQUIRED_TYPES, "fixture must contain each of the nine platform contract record types exactly once")
    return records

def validate_package(package: dict) -> None:
    Draft202012Validator(SCHEMA, format_checker=FormatChecker()).validate(package)
    records = records_by_type(package)
    artifact = records["os_artifact"]
    if artifact["artifact_kind"] == "bootable-os":
        require(artifact["bootable"] is True and artifact["boot_metadata"] is not None, "bootable OS artifacts require boot metadata")
    if artifact["artifact_kind"] == "container-image":
        require(artifact["bootable"] is False, "OCI container metadata must not imply a bootable OS")

    graph = records["workflow_blueprint"]
    node_ids = [node["node_id"] for node in graph["nodes"]]
    require(len(node_ids) == len(set(node_ids)), "workflow node identifiers must be unique")
    known = set(node_ids)
    indegree = {node:0 for node in node_ids}
    adjacency = {node:[] for node in node_ids}
    for edge in graph["edges"]:
        require(edge["from"] in known and edge["to"] in known, "workflow edges must reference declared nodes")
        adjacency[edge["from"]].append(edge["to"])
        indegree[edge["to"]] += 1
    ready = [node for node, degree in indegree.items() if degree == 0]
    visited = 0
    while ready:
        node = ready.pop()
        visited += 1
        for child in adjacency[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    require(visited == len(node_ids), "workflow blueprint must be acyclic")
    if graph["status"] == "approved" and graph["approval_mode"] in {"human-required","owner-required"}:
        require(bool(graph["approval_ref"]), "approved blueprint requires its approval reference")

    ci = records["cicd_event"]
    require(ci["passed_count"] + ci["failed_count"] + ci["skipped_count"] == ci["test_count"], "CI test totals must reconcile")
    if ci["status"] == "passed":
        require(ci["failed_count"] == 0, "passed CI event cannot contain failed tests")
    if ci["status"] == "failed":
        require(ci["failed_count"] > 0, "failed CI event requires at least one failed test")

    require(records["telemetry_record"]["redacted"] is True, "portable telemetry must be redacted before export")

    route = records["network_route"]
    if route["decision"] == "allow":
        require(bool(route["authentication_profile_ref"]) and bool(route["authorization_policy_ref"]) and bool(route["egress_scope_ref"]),
                "allowed network routes require authentication, authorization and egress-scope references")
    if route["decision"] in {"deny","quarantine","approval-required"}:
        require(route["execution_status"] == "not-executed", "denied, quarantined or approval-required routes must not be recorded as executed")

    storage = records["storage_interface"]
    if storage["data_classification"] in {"confidential","secret"}:
        require(storage["encryption_at_rest"] and storage["encryption_in_transit"],
                "confidential and secret storage interfaces require encryption at rest and in transit")

    evaluation = records["evaluation_receipt"]
    require(evaluation["passed_count"] + evaluation["failed_count"] + evaluation["skipped_count"] == evaluation["test_count"],
            "evaluation totals must reconcile")
    if evaluation["status"] == "passed":
        require(evaluation["failed_count"] == 0 and evaluation["test_count"] > 0, "passed evaluation requires a non-empty test set with no failures")
    if evaluation["status"] == "failed":
        require(evaluation["failed_count"] > 0, "failed evaluation requires at least one failed test")

def mutate(package: dict, kind: str, fn) -> dict:
    result = copy.deepcopy(package)
    entry = next(item for item in result["records"] if item["record_type"] == kind)
    fn(entry["record"])
    return result

def run_negative_tests() -> int:
    cases = [
        ("container incorrectly marked bootable", lambda p: mutate(p,"os_artifact",lambda r:r.update(bootable=True))),
        ("duplicate workflow node", lambda p: mutate(p,"workflow_blueprint",lambda r:r["nodes"].append(copy.deepcopy(r["nodes"][0])))),
        ("workflow cycle", lambda p: mutate(p,"workflow_blueprint",lambda r:r["edges"].append({"from":"test","to":"build","condition_ref":None}))),
        ("approved blueprint without approval", lambda p: mutate(p,"workflow_blueprint",lambda r:r.update(status="approved",approval_ref=None))),
        ("CI pass with failed test", lambda p: mutate(p,"cicd_event",lambda r:r.update(failed_count=1))),
        ("allowed route without authorization", lambda p: mutate(p,"network_route",lambda r:r.update(authorization_policy_ref=None))),
        ("unredacted telemetry", lambda p: mutate(p,"telemetry_record",lambda r:r.update(redacted=False))),
        ("confidential storage without transit encryption", lambda p: mutate(p,"storage_interface",lambda r:r.update(data_classification="confidential",encryption_in_transit=False))),
        ("evaluation totals inconsistent", lambda p: mutate(p,"evaluation_receipt",lambda r:r.update(test_count=9))),
        ("denied route marked executed", lambda p: mutate(p,"network_route",lambda r:r.update(decision="deny",execution_status="executed"))),
    ]
    for label, mutation in cases:
        try:
            validate_package(mutation(FIXTURE))
        except (ValidationError, ValueError, KeyError):
            print(f"PASS negative: {label}")
        else:
            raise AssertionError(f"negative case was accepted: {label}")
    return len(cases)

def main() -> int:
    try:
        validate_package(FIXTURE)
        print(f"PASS positive fixture: {len(FIXTURE['records'])} platform records")
        count = run_negative_tests()
        print(f"PASS {count} negative cases")
        return 0
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
