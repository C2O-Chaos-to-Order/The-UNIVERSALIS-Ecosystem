#!/usr/bin/env python3
"""Validate portable website interoperability contracts and semantic safeguards."""
from __future__ import annotations
import copy, json, sys
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "schemas/websites/website-interoperability-contracts.v1.schema.json").read_text())
FIXTURE = json.loads((ROOT / "examples/websites/website-interoperability-fixtures.v1.json").read_text())
KEYS = {
    "site_definition":"siteDefinition",
    "agent_capability_manifest":"agentCapabilityManifest",
    "site_change_set":"siteChangeSet",
    "site_permission_profile":"sitePermissionProfile",
    "site_audit_receipt":"siteAuditReceipt",
    "site_publish_receipt":"sitePublishReceipt",
}
REQUIRED = set(KEYS)

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def validate_record(kind: str, record: dict) -> None:
    require(kind in KEYS, f"unsupported record type: {kind}")
    view = {"$schema":SCHEMA["$schema"], "$defs":SCHEMA["$defs"], "$ref":"#/$defs/" + KEYS[kind]}
    Draft202012Validator(view, format_checker=FormatChecker()).validate(record)

def records_by_type(package: dict) -> dict:
    result = {}
    for entry in package["records"]:
        kind = entry["record_type"]
        require(kind not in result, f"duplicate record type: {kind}")
        validate_record(kind, entry["record"])
        result[kind] = entry["record"]
    require(set(result) == REQUIRED, "fixture must contain each of six website contract record types exactly once")
    return result

def validate_package(package: dict) -> None:
    Draft202012Validator(SCHEMA, format_checker=FormatChecker()).validate(package)
    records = records_by_type(package)
    site = records["site_definition"]
    routes = [page["route"] for page in site["pages"]]
    require(len(routes) == len(set(routes)), "site routes must be unique")
    page_ids = [page["page_id"] for page in site["pages"]]
    require(len(page_ids) == len(set(page_ids)), "page identifiers must be unique")
    if site["site_state"] == "published":
        require(all(page["publication_state"] in {"published","unpublished","archived"} for page in site["pages"]),
                "published site cannot contain draft/preview-only pages")

    manifest = records["agent_capability_manifest"]
    operations = {cap["operation"]: cap for cap in manifest["capabilities"]}
    for op in ("publish","deploy","manage-dns","delete-content"):
        if op in operations:
            cap = operations[op]
            require(cap["requires_human_approval"] and cap["requires_owner_authorization"],
                    f"{op} capability must require human approval and owner authorization")
    if "webmcp" in manifest["interaction_surfaces"]:
        guarantees = manifest["webmcp_guarantees"]
        require(manifest["webmcp_spec_status"] in {"community-group-draft","early-preview","implementation-specific"},
                "WebMCP implementation must declare its maturity/status")
        require(guarantees["structured_state"] and guarantees["revision_pinning"] and guarantees["stale_proposal_rejection"],
                "WebMCP proposal surface must use structured state, pinned revisions and stale-proposal rejection")
        require(guarantees["human_gate_for_publish"], "WebMCP must not bypass the human publishing gate")

    changes = records["site_change_set"]
    base_matches = changes["base_revision_digest"] == changes["observed_current_revision_digest"]
    if changes["stale"] or not base_matches:
        require(changes["status"] in {"proposed","review","rejected","stale","abandoned"},
                "stale change set cannot be approved or committed")
    else:
        require(changes["status"] != "stale", "change set cannot be stale when base and current revisions match")
    if changes["status"] == "committed":
        require(bool(changes["commit_ref"]), "committed change set requires commit reference")
    if changes["status"] == "approved":
        require(bool(changes["approval_ref"]), "approved change set requires approval reference")
    if changes["has_publish_or_deploy_effect"] and changes["status"] in {"approved","committed"}:
        require(changes["requires_human_approval"] and bool(changes["approval_ref"]),
                "publish/deploy effect requires human approval before commit")

    permission = records["site_permission_profile"]
    allowed = set(permission["allowed_operations"])
    if "publish" in allowed:
        require(permission["human_approval_for_publish"], "publish permission requires a human approval gate")
    if "deploy" in allowed or "manage-dns" in allowed:
        require(permission["human_approval_for_deploy"], "deploy/DNS permission requires a human approval gate")
    require(not (allowed & set(permission["denied_operations"])), "an operation cannot be both allowed and denied")

    audit = records["site_audit_receipt"]
    counts = {name:0 for name in ("info","low","moderate","high","critical")}
    for finding in audit["findings"]:
        counts[finding["severity"]] += 1
    require(counts == audit["summary"], "audit finding severities must reconcile with the summary")
    if audit["result"] == "passed":
        require(audit["summary"]["critical"] == 0 and audit["summary"]["high"] == 0,
                "passed audit cannot contain critical or high findings")
    if audit["score"] is not None:
        require(0 <= audit["score"] <= 100, "audit score must be between 0 and 100")

    receipt = records["site_publish_receipt"]
    if receipt["result"] == "succeeded" and receipt["event_type"] in {"content-publish","site-deploy","dns-change"}:
        require(bool(receipt["approval_ref"]), "successful publish/deploy/DNS action requires approval reference")
        require(bool(receipt["operator_ref"]), "successful publish/deploy/DNS action requires accountable operator")
        require(receipt["signature_state"] in {"signed","verified"} and receipt["signature"] is not None,
                "successful publish/deploy/DNS action requires signature envelope metadata")

def mutate(package: dict, kind: str, fn) -> dict:
    result = copy.deepcopy(package)
    entry = next(item for item in result["records"] if item["record_type"] == kind)
    fn(entry["record"])
    return result

def run_negative_tests() -> int:
    cases = [
        ("duplicate site route", lambda p: mutate(p,"site_definition",lambda r:r["pages"].append(copy.deepcopy(r["pages"][0])))),
        ("publish capability without owner/human gate", lambda p: mutate(p,"agent_capability_manifest",lambda r:r["capabilities"].append({"capability_id":"fixture:bad-publish","operation":"publish","scope_refs":["fixture:all"],"effect":"publish","requires_human_approval":False,"requires_owner_authorization":False,"tool_schema_ref":None}))),
        ("WebMCP surface without stale-change protection", lambda p: mutate(p,"agent_capability_manifest",lambda r:r["webmcp_guarantees"].update(stale_proposal_rejection=False))),
        ("stale ChangeSet committed", lambda p: mutate(p,"site_change_set",lambda r:r.update(stale=True,status="committed",commit_ref="fixture:commit"))),
        ("approved ChangeSet without approval", lambda p: mutate(p,"site_change_set",lambda r:r.update(status="approved",approval_ref=None))),
        ("publish-effect ChangeSet committed without human approval", lambda p: mutate(p,"site_change_set",lambda r:r.update(status="committed",commit_ref="fixture:commit",has_publish_or_deploy_effect=True,requires_human_approval=False,approval_ref=None))),
        ("publish permission without human gate", lambda p: mutate(p,"site_permission_profile",lambda r:r.update(allowed_operations=["read-content","publish"],human_approval_for_publish=False))),
        ("audit summary does not reconcile", lambda p: mutate(p,"site_audit_receipt",lambda r:r.update(summary={"info":0,"low":0,"moderate":0,"high":0,"critical":0}))),
        ("passed audit with critical finding", lambda p: mutate(p,"site_audit_receipt",lambda r:r.update(summary={"info":1,"low":0,"moderate":0,"high":0,"critical":1},findings=r["findings"]+[{"finding_id":"fixture:crit","rule_id":"fixture:secret","severity":"critical","page_ref":"fixture:page-home","evidence_digest":"2"*64,"remediation_state":"open"}]))),
        ("successful production publish without approval", lambda p: mutate(p,"site_publish_receipt",lambda r:r.update(event_type="content-publish",result="succeeded",approval_ref=None,operator_ref="fixture:operator",signature_state="signed",signature={"algorithm":"Ed25519","key_fingerprint":"3"*64,"signed_payload_digest":"4"*64,"signature_ref":"fixture:sig","signed_at":"2026-11-12T18:00:20Z","verification_status":"not-run"}))),
        ("successful production deployment without signature", lambda p: mutate(p,"site_publish_receipt",lambda r:r.update(event_type="site-deploy",result="succeeded",approval_ref="fixture:approval",operator_ref="fixture:operator",signature_state="not-run",signature=None)))
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
        print(f"PASS positive fixture: {len(FIXTURE['records'])} website records")
        count = run_negative_tests()
        print(f"PASS {count} negative cases")
        return 0
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
