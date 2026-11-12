#!/usr/bin/env python3
"""Validate portable prevention contracts, harm metrics, containment and signed receipts."""
from __future__ import annotations
import base64, copy, hashlib, json, math
from datetime import datetime
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "schemas/prevention/prevention-contracts.v1.schema.json").read_text())
FIXTURE = json.loads((ROOT / "examples/prevention/prevention-fixtures.v1.json").read_text())

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def dt(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

def wilson(k, n, z=1.959963984540054):
    p = k / n
    den = 1 + z*z/n
    center = (p + z*z/(2*n)) / den
    half = z * math.sqrt((p*(1-p) + z*z/(4*n)) / n) / den
    return round(center-half, 6), round(center+half, 6)

def index_records(records):
    names = {
        "harm_taxonomy_mapping": "harm_taxonomy_mappings",
        "constitutional_floor_profile": "constitutional_floor_profiles",
        "enforcement_receipt": "enforcement_receipts",
        "harm_reduction_evaluation": "harm_reduction_evaluations",
        "red_team_finding": "red_team_findings",
        "containment_attestation": "containment_attestations",
        "safety_coverage_attestation": "coverage_attestations",
        "case_escalation": "case_escalations",
    }
    return {singular: {x["record_id"]: x for x in records[plural]}
            for singular, plural in names.items()}

def verify_receipt_signature(receipt, verification_key):
    signature = receipt["signature"]
    body = copy.deepcopy(receipt)
    body.pop("signature")
    body_digest = digest(body)
    if body_digest != signature["signed_body_digest"]:
        raise ValueError("enforcement receipt signed-body digest mismatch")
    key = base64.b64decode(verification_key["public_key_base64"], validate=True)
    key_id = "sha256:" + hashlib.sha256(key).hexdigest()
    if key_id != verification_key["key_id"] or key_id != signature["key_id"]:
        raise ValueError("enforcement receipt verification-key identity mismatch")
    if verification_key["trust_anchor_kind"] != signature["trust_anchor_kind"]:
        raise ValueError("enforcement receipt trust-anchor class mismatch")
    Ed25519PublicKey.from_public_bytes(key).verify(
        base64.b64decode(signature["signature_base64"], validate=True),
        canonical(body),
    )

def validate_all(records, verification_key):
    Draft202012Validator.check_schema(SCHEMA)
    validator = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
    for group in records.values():
        for record in group:
            validator.validate(record)
    idx = index_records(records)

    # Taxonomy namespaces are explicit/versioned. Maturity is metadata, not legal equivalence.
    for taxonomy in records["harm_taxonomy_mappings"]:
        namespaces = {x["namespace"] for x in taxonomy["taxonomies"]}
        for category in taxonomy["harm_categories"]:
            if not set(category["taxonomy_refs"]).issubset(namespaces):
                raise ValueError("harm category references an undeclared taxonomy namespace")
        if taxonomy["compliance_claimed"]:
            raise ValueError("taxonomy mapping cannot self-certify legal compliance")

    # The public constitutional floor is immutable to the agent and always retains human veto.
    for profile in records["constitutional_floor_profiles"]:
        floors = profile["floors"]
        by_id = {x["floor_id"]: x for x in floors}
        required_types = {"prohibition", "least_privilege", "human_veto", "evidence_integrity", "auditability", "external_containment"}
        present_types = {x["floor_type"] for x in floors}
        if not required_types.issubset(present_types):
            raise ValueError("constitutional profile omits a required floor class")
        if any(not x["immutable"] or x["change_control"] != "external_human_witness" for x in floors):
            raise ValueError("constitutional floor is mutable without an external witness")
        if not profile["human_veto_final"] or profile["agent_can_modify_floors"] or not profile["floor_change_requires_external_witness"]:
            raise ValueError("agent can weaken or bypass constitutional governance")
        if profile["compliance_claimed"]:
            raise ValueError("constitutional profile cannot claim legal compliance by declaration")
        if len(by_id) != len(floors):
            raise ValueError("duplicate constitutional floor identifier")

    # Every receipt binds the exact policy, constitution, taxonomy and decision evidence.
    for receipt in records["enforcement_receipts"]:
        profile = idx["constitutional_floor_profile"].get(receipt["constitution_profile_ref"])
        if not profile or profile["policy_digest"] != receipt["constitution_digest"]:
            raise ValueError("receipt refers to a missing or different constitutional profile")
        taxonomy_refs = set(receipt["taxonomy_mapping_refs"])
        if not taxonomy_refs.issubset(idx["harm_taxonomy_mapping"]):
            raise ValueError("receipt references an unknown harm taxonomy")
        floor_map = {x["floor_id"]: x for x in profile["floors"]}
        floor_results = receipt["floor_results"]
        if any(x["floor_id"] not in floor_map for x in floor_results):
            raise ValueError("receipt refers to an unknown constitutional floor")
        failed = any(x["outcome"] == "fail" for x in floor_results)
        indeterminate = any(x["outcome"] == "indeterminate" for x in floor_results)
        if receipt["decision"] == "allow" and (failed or indeterminate):
            raise ValueError("allow decision contradicts a failed or indeterminate floor")
        if receipt["control_point"] == "pre_tool_execution":
            if not receipt["external_to_agent"] or receipt["fail_mode"] != "closed":
                raise ValueError("pre-tool enforcement must be external and fail-closed")
        if receipt["decision"] == "allow":
            if not receipt["action_executed"] or receipt["action_prevented"]:
                raise ValueError("allow receipt must record execution, not prevention")
        else:
            if receipt["action_executed"] or not receipt["action_prevented"]:
                raise ValueError("review/block/contain receipt must show action was not executed")
        if receipt["decision"] in {"block", "contain"} and not receipt["external_to_agent"]:
            raise ValueError("block/contain decision is not enforced outside the agent")
        verify_receipt_signature(receipt, verification_key)

    # Harm-reduction claims are recomputed from counts and a frozen independent test set.
    for evaluation in records["harm_reduction_evaluations"]:
        attacks = evaluation["attack_count"]
        benign = evaluation["benign_count"]
        base_count = evaluation["baseline_harmful_count"]
        defended_count = evaluation["defended_harmful_count"]
        false_blocked = evaluation["false_blocked_benign_count"]
        if base_count > attacks or defended_count > attacks or false_blocked > benign:
            raise ValueError("harm evaluation count exceeds its denominator")
        if not evaluation["suite_frozen"] or evaluation["defense_tuned_on_test_set"] or not evaluation["independent_evaluator"]:
            raise ValueError("harm evaluation lacks frozen independent evaluation")
        if evaluation["taxonomy_mapping_ref"] not in idx["harm_taxonomy_mapping"]:
            raise ValueError("harm evaluation references an unknown taxonomy")
        rate_base = round(base_count / attacks, 6)
        rate_defended = round(defended_count / attacks, 6)
        fpr = round(false_blocked / benign, 6)
        absolute = round(rate_base - rate_defended, 6)
        relative = round((absolute / rate_base), 6) if rate_base else 0.0
        for field, expected in (("baseline_harm_rate", rate_base), ("defended_harm_rate", rate_defended),
                                ("false_positive_rate", fpr), ("absolute_harm_reduction", absolute),
                                ("relative_harm_reduction", relative)):
            if abs(evaluation[field] - expected) > 1e-6:
                raise ValueError("harm evaluation metric does not match source counts: " + field)
        for field, count, denominator in (
            ("baseline_ci95", base_count, attacks),
            ("defended_ci95", defended_count, attacks),
            ("false_positive_ci95", false_blocked, benign),
        ):
            expected = wilson(count, denominator)
            if any(abs(a-b) > 1.1e-6 for a, b in zip(evaluation[field], expected)):
                raise ValueError("harm evaluation confidence interval is not reproducible: " + field)
        expected_conclusion = ("harm_reduced" if defended_count < base_count else
                               "harm_increased" if defended_count > base_count else "no_measurable_change")
        if evaluation["conclusion"] != expected_conclusion:
            raise ValueError("harm evaluation conclusion contradicts measured counts")
        if len(evaluation["repeat_seeds"]) < 2 or evaluation["compliance_claimed"]:
            raise ValueError("evaluation is not reproducible or improperly claims compliance")

    # Red-team findings must be authorized, in-scope, evidence-backed and data-minimized.
    for finding in records["red_team_findings"]:
        taxonomy = idx["harm_taxonomy_mapping"].get(finding["taxonomy_mapping_ref"])
        if not taxonomy or finding["category_id"] not in {x["category_id"] for x in taxonomy["harm_categories"]}:
            raise ValueError("red-team finding category is not present in its taxonomy")
        if not finding["authorization_scope_ref"] or finding["out_of_scope_activity"] or finding["raw_exploit_included"]:
            raise ValueError("red-team finding violates authorization or evidence-minimization boundary")
        if finding["reproduced"] and finding["lifecycle_status"] not in {"confirmed", "mitigated", "accepted_risk"}:
            raise ValueError("reproduced finding is not in a confirmed lifecycle state")
        if finding["lifecycle_status"] == "confirmed" and not finding["independent_reviewer"]:
            raise ValueError("confirmed finding lacks independent review")

    # A containment claim requires evidence from a control path the agent cannot disable.
    for containment in records["containment_attestations"]:
        if not containment["external_to_agent"] or containment["agent_can_disable_control"] or not containment["fail_closed"]:
            raise ValueError("containment is not an external fail-closed control")
        if containment["outcome"] == "confirmed":
            if not containment["confirmed_at"] or not containment["independent_verifier"]:
                raise ValueError("confirmed containment lacks read-back or independent verifier")
            if dt(containment["confirmed_at"]) < dt(containment["initiated_at"]):
                raise ValueError("containment confirmation predates initiation")
        elif containment["confirmed_at"] is not None:
            raise ValueError("unconfirmed containment has a confirmation timestamp")
        if not containment["release_requires_human_witness"] or containment["private_anchor_material_included"]:
            raise ValueError("containment release/anchor boundary is unsafe")

    # Coverage claims disclose gaps and reject a fail-open 'pass' on critical enforcement.
    for coverage in records["coverage_attestations"]:
        if coverage["bypass_success_count"] > coverage["bypass_attempt_count"]:
            raise ValueError("bypass successes exceed attempts")
        if not set(coverage["enforced_layers"]).issubset(set(coverage["tested_layers"])):
            raise ValueError("an enforcement layer is claimed without a test")
        if coverage["overall_result"] == "pass":
            if coverage["bypass_success_count"] != 0 or coverage["guard_unavailable_behavior"] == "fail_open":
                raise ValueError("coverage pass contradicts bypass or guard-outage behavior")
            if not coverage["external_control_plane"]:
                raise ValueError("coverage pass lacks an external control plane")
            if coverage["untested_surfaces"]:
                raise ValueError("coverage pass omits untested surfaces")

    # Case escalation uses a taxonomy category but exports neither raw personal nor harmful content.
    for case in records["case_escalations"]:
        taxonomy = idx["harm_taxonomy_mapping"].get(case["taxonomy_mapping_ref"])
        if not taxonomy or case["category_id"] not in {x["category_id"] for x in taxonomy["harm_categories"]}:
            raise ValueError("case escalation category is not in the selected taxonomy")
        if case["raw_personal_data_included"] or case["raw_harmful_content_included"]:
            raise ValueError("case escalation exports raw sensitive content")

def reject(name, fn):
    try:
        fn()
    except (ValueError, KeyError, TypeError, ValidationError):
        return
    raise AssertionError("negative test unexpectedly passed: " + name)

def main():
    g = FIXTURE["records"]
    key = FIXTURE["verification_key"]
    validate_all(g, key)
    tests = []

    x=copy.deepcopy(g); x["constitutional_floor_profiles"][0]["floors"][0]["immutable"]=False
    tests.append(("agent-mutable constitutional floor", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["constitutional_floor_profiles"][0]["human_veto_final"]=False
    tests.append(("human veto is not final", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["constitutional_floor_profiles"][0]["floors"].pop()
    tests.append(("missing external-containment floor", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["constitutional_floor_profiles"][0]["agent_can_modify_floors"]=True
    tests.append(("agent can modify constitution", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["enforcement_receipts"][0]["decision"]="allow"
    tests.append(("allow contradicts failed floor", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["enforcement_receipts"][0]["action_executed"]=True
    tests.append(("blocked action was executed", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["enforcement_receipts"][0]["external_to_agent"]=False
    tests.append(("tool guard is inside agent boundary", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["enforcement_receipts"][0]["fail_mode"]="open"
    tests.append(("pre-tool enforcement fails open", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["enforcement_receipts"][0]["constitution_digest"]="0"*64
    tests.append(("receipt bound to another constitution", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["enforcement_receipts"][0]["taxonomy_mapping_refs"]=["taxonomy:missing"]
    tests.append(("receipt taxonomy reference missing", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["enforcement_receipts"][0]["signature"]["signature_base64"]="A"*88
    tests.append(("tampered Ed25519 receipt signature", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["enforcement_receipts"][0]["signature"]["signed_body_digest"]="0"*64
    tests.append(("signed receipt body digest tampered", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["harm_reduction_evaluations"][0]["defense_tuned_on_test_set"]=True
    tests.append(("defense tuned on held-out test set", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["harm_reduction_evaluations"][0]["independent_evaluator"]=False
    tests.append(("evaluator not independent", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["harm_reduction_evaluations"][0]["defended_harmful_count"]=31
    tests.append(("reported harm rate disagrees with count", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["harm_reduction_evaluations"][0]["false_positive_rate"]=0.0
    tests.append(("false-positive rate mismatch", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["harm_reduction_evaluations"][0]["defended_ci95"]=[0.0,1.0]
    tests.append(("confidence interval is not reproducible", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["harm_reduction_evaluations"][0]["conclusion"]="harm_increased"
    tests.append(("evaluation conclusion contradicts counts", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["harm_taxonomy_mappings"][0]["compliance_claimed"]=True
    tests.append(("taxonomy falsely self-certifies compliance", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["red_team_findings"][0]["out_of_scope_activity"]=True
    tests.append(("red team activity exceeded scope", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["red_team_findings"][0]["raw_exploit_included"]=True
    tests.append(("raw exploit payload exported", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["containment_attestations"][0]["agent_can_disable_control"]=True
    tests.append(("agent can disable containment", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["containment_attestations"][0]["external_to_agent"]=False
    tests.append(("containment not out of band", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["containment_attestations"][0]["independent_verifier"]=False
    tests.append(("containment confirmed without independent verifier", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["containment_attestations"][0]["confirmed_at"]=None
    tests.append(("containment claimed without read-back", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["coverage_attestations"][0]["bypass_success_count"]=1
    tests.append(("coverage pass despite successful bypass", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["coverage_attestations"][0]["guard_unavailable_behavior"]="fail_open"
    tests.append(("coverage pass despite fail-open outage", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["coverage_attestations"][0]["untested_surfaces"]=["mobile-webview"]
    tests.append(("coverage pass hides untested surface", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["case_escalations"][0]["raw_personal_data_included"]=True
    tests.append(("raw personal data exported with escalation", lambda: validate_all(x,key)))
    x=copy.deepcopy(g); x["case_escalations"][0]["category_id"]="H-NOT-IN-TAXONOMY"
    tests.append(("escalation uses undeclared harm category", lambda: validate_all(x,key)))

    for name, fn in tests:
        reject(name, fn)
    print(f"PASS: {sum(len(v) for v in g.values())} synthetic records, signed Ed25519 enforcement receipt, {len(tests)} negative tests.")

if __name__ == "__main__":
    main()
