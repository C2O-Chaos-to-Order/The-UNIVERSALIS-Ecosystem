#!/usr/bin/env python3
"""Validate the portable eight-stratum contracts against synthetic evidence.

This checker validates contract semantics only. It does not execute third-party tools,
grant authority, verify production signatures, or certify sovereignty/safety/compliance.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas/strata/stratified-capability-contracts.v1.schema.json"
FIXTURE = ROOT / "examples/strata/stratified-capability-fixtures.v1.json"
STRATA = ["Base", "Meta", "Super", "Hyper", "Ultra", "Magic", "Quantum", "Transformative"]
EXPECTED_TYPES = {
    "stratum_profile", "component_manifest", "interoperability_profile",
    "orchestration_session", "lifecycle_event", "proactive_action_receipt",
    "composition_contract", "composition_execution_receipt",
    "model_route_decision_receipt", "application_provenance_receipt",
    "quantum_execution_receipt", "robot_policy_evaluation",
    "sovereign_deployment_attestation", "evidence_claim",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_bundle(bundle: dict) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    records = bundle["records"]
    require(isinstance(records, list), "records must be a list")
    require(len(records) == 21, "fixture must contain exactly 21 synthetic records")
    for record in records:
        validator.validate(record)

    by_type: dict[str, list[dict]] = {}
    ids = [r["record_id"] for r in records]
    require(len(ids) == len(set(ids)), "record_id must be unique within a bundle")
    for record in records:
        by_type.setdefault(record["record_type"], []).append(record)
    require(set(by_type) == EXPECTED_TYPES, "fixture must cover all 14 record families")

    profiles = by_type["stratum_profile"]
    require(len(profiles) == 1, "exactly one canonical stratum profile is required")
    profile = profiles[0]["payload"]
    require(profile["canonical_order"] == STRATA, "stratum order must be canonical")
    require(profile["is_authority_tier"] is False, "stratum is not an authority tier")

    for record in by_type["component_manifest"]:
        p = record["payload"]
        require(p["stratum"] in STRATA, "component must use a canonical stratum")
        require(bool(p.get("source_ref")), "component source reference is required")
        require(bool(p.get("license_id")), "component license must be recorded")
        require(p.get("adoption_status") in {"candidate", "evaluated", "approved", "rejected", "deprecated", "not_tested"},
                "invalid adoption status")

    for record in by_type["interoperability_profile"]:
        p = record["payload"]
        protocol = p["protocol"]
        roles = (p["producer_role"].lower(), p["consumer_role"].lower())
        if protocol == "MCP":
            require("server" in roles[0] and "client" in roles[1], "MCP role must be server to client")
        elif protocol == "A2A":
            require("agent" in roles[0] and "agent" in roles[1], "A2A role must be agent to agent")
        elif protocol == "ACP":
            require("agent" in roles[0] and "client" in roles[1], "ACP role must be agent to client")
        require(p.get("authority_grant") is False, "protocol compatibility cannot grant authority")

    for record in by_type["orchestration_session"]:
        require(record["payload"].get("private_policy_included") is False,
                "portable session cannot include private policy")
        require(bool(record["payload"].get("agent_refs")), "session must identify agents")

    allowed = {
        "unknown": {"provisioning"},
        "provisioning": {"active", "suspended", "decommissioned"},
        "active": {"suspended", "migrating", "decommissioned"},
        "suspended": {"active", "migrating", "decommissioned"},
        "migrating": {"active", "suspended", "decommissioned"},
    }
    for record in by_type["lifecycle_event"]:
        p = record["payload"]
        require(p["to_state"] in allowed.get(p["from_state"], set()),
                "invalid agent lifecycle transition")

    for record in by_type["proactive_action_receipt"]:
        p = record["payload"]
        if p["authority_check"] == "denied":
            require(p["approval_outcome"] in {"human_denied", "escalated", "blocked"},
                    "denied proactive action must be blocked or escalated")
            require(p.get("execution_occurred") is False, "denied proactive action cannot execute")
        if p["risk_level"] in {"high", "critical"} and p["approval_outcome"] == "human_approved":
            require(bool(p.get("human_approval_ref")), "human approval reference required")

    contracts = {r["record_id"]: r["payload"] for r in by_type["composition_contract"]}
    for record in by_type["composition_contract"]:
        p = record["payload"]
        require(p["stratum"] in STRATA, "composition stratum is invalid")
        require(p["step_budget"] > 0, "composition step budget must be positive")
    for record in by_type["composition_execution_receipt"]:
        p = record["payload"]
        require(p["authority_granted"] is False, "composition receipt cannot grant authority")
        require(p["signature_verification"] in {"not_present", "not_verified", "verified", "invalid"},
                "invalid signature verification state")
        if p["execution_status"] == "completed":
            require(bool(p["invocations"]), "completed composition must list invocations")
        if p.get("signature") is None:
            require(p["signature_verification"] == "not_present",
                    "unsigned fixture must explicitly state signature not present")
        else:
            sig = p["signature"]
            require(sig["algorithm"] == "Ed25519", "composition receipt signature must use Ed25519")
            require(p["signature_verification"] in {"not_verified", "verified", "invalid"},
                    "signed receipt must declare verification state")

    for record in by_type["model_route_decision_receipt"]:
        p = record["payload"]
        if p["sovereignty_class"] == "unapproved_external":
            require(p["egress_decision"] in {"denied", "human_review"},
                    "unapproved external model route cannot be allowed")
        if p.get("shadow_lane_enabled") and p.get("shadow_data_classification") in {"restricted", "unknown"}:
            require(p["egress_decision"] != "allowed",
                    "restricted shadow traffic requires explicit approval, not default allowance")

    for record in by_type["application_provenance_receipt"]:
        p = record["payload"]
        require(p.get("secrets_included") is False, "application receipt cannot include secrets")
        if p["publication_status"] == "published":
            require(bool(p.get("human_publication_approval_ref")),
                    "publication requires a human approval reference")

    for record in by_type["quantum_execution_receipt"]:
        p = record["payload"]
        if p["execution_mode"] == "remote_qpu" or p.get("billable_submission"):
            require(bool(p.get("emulation_evidence_ref")), "QPU submission requires emulation evidence")
            require(bool(p.get("price_quote_digest")), "QPU submission requires shot/price quote")
            require(bool(p.get("human_approval_ref")), "QPU submission requires human approval")
            require(bool(p.get("job_ref")), "submitted QPU job must identify its job")
            require(p["shot_count"] > 0, "QPU submission must declare positive shot count")
        else:
            require(p.get("billable_submission") is False, "local emulation cannot claim billable QPU submission")

    for record in by_type["robot_policy_evaluation"]:
        p = record["payload"]
        require(p["actuation_authorized"] is False, "robot evaluation record never grants actuation")
        if p["evaluation_mode"] == "simulation_only":
            require(p["sim_to_real_evidence"] == "not_available",
                    "simulation-only result cannot claim sim-to-real validation")

    for record in by_type["sovereign_deployment_attestation"]:
        p = record["payload"]
        require(p["compliance_certification_claimed"] is False,
                "portable attestation cannot self-certify compliance")
        if p["verification_status"] == "verified_within_scope":
            require(p["independent_verifier"] is True,
                    "verified sovereignty claim requires independent verifier")

    for record in by_type["evidence_claim"]:
        p = record["payload"]
        require(bool(p["source_refs"]), "evidence claim requires source references")
        require(bool(p["limitations"]), "evidence claim must declare limitations")


def negative_tests() -> list[str]:
    original = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cases = []

    def add(name, mutate):
        cases.append((name, mutate))

    def mutate_record(bundle, kind, index, key, value):
        rec = next(r for r in bundle["records"] if r["record_type"] == kind)
        rec["payload"][key] = value

    add("noncanonical_stratum_order", lambda b: mutate_record(b, "stratum_profile", 0, "canonical_order", list(reversed(STRATA))))
    add("stratum_misused_as_authority", lambda b: mutate_record(b, "stratum_profile", 0, "is_authority_tier", True))
    add("mcp_role_confusion", lambda b: mutate_record(b, "interoperability_profile", 0, "consumer_role", "agent"))
    add("a2a_role_confusion", lambda b: mutate_record(b, "interoperability_profile", 0, "consumer_role", "client"))
    add("acp_role_confusion", lambda b: mutate_record(b, "interoperability_profile", 0, "consumer_role", "agent"))
    add("protocol_implies_authority", lambda b: mutate_record(b, "interoperability_profile", 0, "authority_grant", True))
    add("component_missing_license", lambda b: mutate_record(b, "component_manifest", 0, "license_id", ""))
    add("component_missing_source", lambda b: mutate_record(b, "component_manifest", 0, "source_ref", ""))
    add("invalid_lifecycle_transition", lambda b: mutate_record(b, "lifecycle_event", 0, "to_state", "active"))
    add("denied_proactive_action_executes", lambda b: mutate_record(b, "proactive_action_receipt", 0, "execution_occurred", True))
    add("composition_receipt_grants_authority", lambda b: mutate_record(b, "composition_execution_receipt", 0, "authority_granted", True))
    add("unsigned_receipt_claims_verified", lambda b: mutate_record(b, "composition_execution_receipt", 0, "signature_verification", "verified"))
    add("unapproved_external_route_allowed", lambda b: mutate_record(b, "model_route_decision_receipt", 0, "sovereignty_class", "unapproved_external"))
    add("restricted_shadow_egress_allowed", lambda b: mutate_record(b, "model_route_decision_receipt", 0, "shadow_data_classification", "restricted"))
    add("publication_without_human_approval", lambda b: mutate_record(b, "application_provenance_receipt", 0, "publication_status", "published"))
    add("application_secrets_exported", lambda b: mutate_record(b, "application_provenance_receipt", 0, "secrets_included", True))
    add("qpu_billable_without_emulation", lambda b: mutate_record(b, "quantum_execution_receipt", 0, "billable_submission", True))
    add("qpu_billable_without_human_approval", lambda b: mutate_record(b, "quantum_execution_receipt", 0, "human_approval_ref", None))
    add("simulation_result_authorizes_robot", lambda b: mutate_record(b, "robot_policy_evaluation", 0, "actuation_authorized", True))
    add("sovereign_claim_self_certifies", lambda b: mutate_record(b, "sovereign_deployment_attestation", 0, "compliance_certification_claimed", True))

    passed = []
    for name, mutate in cases:
        candidate = copy.deepcopy(original)
        mutate(candidate)
        try:
            validate_bundle(candidate)
        except Exception:
            passed.append(name)
        else:
            raise AssertionError(f"negative test unexpectedly passed: {name}")
    return passed


def main() -> None:
    bundle = json.loads(FIXTURE.read_text(encoding="utf-8"))
    validate_bundle(bundle)
    failures = negative_tests()
    print("PASS: Draft 2020-12 envelope schema")
    print("PASS: 21 synthetic records across 14 record families")
    print("PASS: canonical stratum order and MCP/A2A/ACP role separation")
    print(f"PASS: {len(failures)} negative tests rejected invalid authority, egress, publication, quantum, robotics and sovereignty claims")
    print("LIMIT: fixture composition receipt is intentionally unsigned; this script does not verify production cryptographic signatures")
    print("LIMIT: no component behavior, scientific validity, sovereignty or compliance is certified")


if __name__ == "__main__":
    main()
