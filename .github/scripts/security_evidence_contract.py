#!/usr/bin/env python3
"""Validate portable security evidence contracts, RFC 9162 proofs and hash-chained audit receipts."""
from __future__ import annotations
import copy, hashlib, json, sys
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "schemas/security/security-evidence-contracts.v1.schema.json").read_text())
FIX = json.loads((ROOT / "examples/security/security-evidence-fixtures.v1.json").read_text())
KEYS = {
    "taxonomy_mapping": "taxonomyMapping",
    "security_proof": "securityProof",
    "enforcement_receipt": "enforcementReceipt",
    "containment_attestation": "containmentAttestation",
    "authorized_assessment": "authorizedAssessment",
    "security_finding": "securityFinding",
    "sbom_attestation": "sbomAttestation",
    "build_provenance_attestation": "buildProvenanceAttestation",
    "sandbox_attestation": "sandboxAttestation",
    "audit_chain_record": "auditChainRecord",
    "compliance_evidence_map": "complianceEvidenceMap",
}

def validate_record(key: str, value: dict) -> None:
    view = {"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": "#/$defs/" + KEYS[key]}
    Draft202012Validator(view, format_checker=FormatChecker()).validate(value)

def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def check_canonical_subset(value) -> None:
    # This verifier uses a deliberately constrained RFC 8785-compatible subset.
    if value is None or isinstance(value, (str, bool)):
        return
    if isinstance(value, int) and not isinstance(value, bool):
        if abs(value) > 9007199254740991:
            raise ValueError("JCS safe-integer range exceeded")
        return
    if isinstance(value, float):
        raise ValueError("floating-point values are excluded from this proof profile")
    if isinstance(value, list):
        for item in value:
            check_canonical_subset(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or not key.isascii():
                raise ValueError("proof payload keys must be ASCII")
            check_canonical_subset(item)
        return
    raise ValueError("unsupported canonical payload type")

def canonical(value) -> bytes:
    check_canonical_subset(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")

def verify_merkle(proof: dict) -> bool:
    raw = canonical(proof["payload"])
    if hashlib.sha256(raw).hexdigest() != proof["payload_digest"]:
        return False
    node = sha256(bytes([0]) + raw)
    if node.hex() != proof["leaf_hash"]:
        return False
    fn = proof["leaf_index"]
    sn = proof["tree_size"] - 1
    if fn >= proof["tree_size"]:
        return False
    for sibling_hex in proof["path"]:
        if sn == 0:
            return False
        sibling = bytes.fromhex(sibling_hex)
        if (fn & 1) == 1 or fn == sn:
            node = sha256(bytes([1]) + sibling + node)
            if (fn & 1) == 0:
                while fn != 0 and (fn & 1) == 0:
                    fn >>= 1
                    sn >>= 1
        else:
            node = sha256(bytes([1]) + node + sibling)
        fn >>= 1
        sn >>= 1
    return sn == 0 and node.hex() == proof["root_hash"]

def verify_audit_chain(record: dict) -> bool:
    raw = canonical(record["payload"])
    if hashlib.sha256(raw).hexdigest() != record["payload_digest"]:
        return False
    previous = bytes(32) if record["previous_record_digest"] is None else bytes.fromhex(record["previous_record_digest"])
    domain = b"C2O-UNIVERSALIS-SECURITY-CHAIN-V1\x00"
    return sha256(domain + previous + raw).hex() == record["record_digest"]

def semantic_checks(data: dict) -> None:
    taxonomy = data["taxonomy_mapping"]
    known = {item["framework_id"] for item in taxonomy["frameworks"]}
    for mapping in taxonomy["mappings"]:
        assert mapping["source_framework_id"] in known and mapping["target_framework_id"] in known, "taxonomy mapping references unknown framework"

    assessment = data["authorized_assessment"]
    assert assessment["scope_enforced"] is True, "assessment scope must be technically enforced"
    assert assessment["authorization_ref"] and assessment["owner_approval_ref"], "assessment lacks authority evidence"
    assert assessment["stop_conditions"], "assessment lacks stop conditions"
    finding = data["security_finding"]
    assert finding["assessment_ref"] == assessment["assessment_id"], "finding assessment reference mismatch"

    receipt = data["enforcement_receipt"]
    if receipt["decision"] in {"deny", "quarantine", "approval-required"}:
        assert receipt["execution_status"] == "not-executed", "denied/quarantined/approval-required action cannot be marked executed"
        assert receipt["enforcement_result"] in {"enforced", "not-verified"}, "non-allow decision cannot be recorded as bypassed"

    containment = data["containment_attestation"]
    if containment["out_of_band"]:
        assert containment["independent_control_plane"] and containment["independent_of_agent"], "out-of-band containment must be independently controlled"
    if containment["verification_status"] == "verified":
        assert containment["evidence_refs"], "verified containment requires evidence"

    sbom = data["sbom_attestation"]
    if sbom["vulnerability_scan_status"] == "not-run":
        counts = [sbom[k] for k in ("critical_count", "high_count", "moderate_count", "low_count", "unknown_count")]
        assert all(count == 0 for count in counts), "not-run SBOM scan must not claim finding totals"
    provenance = data["build_provenance_attestation"]
    if provenance["verification_status"] == "valid":
        assert "signature" in provenance and provenance["signature"]["verification_status"] == "valid", "verified provenance requires a verified signature envelope"

    sandbox = data["sandbox_attestation"]
    assert sandbox["test_passed"] + sandbox["test_failed"] <= sandbox["test_count"], "sandbox test totals exceed test count"
    if sandbox["verification_status"] == "pass":
        assert sandbox["test_count"] > 0 and sandbox["test_failed"] == 0, "sandbox pass requires executed tests and zero failures"

    assert verify_audit_chain(data["audit_chain_record"]), "tamper-evident audit-chain digest verification failed"
    compliance = data["compliance_evidence_map"]
    assert compliance["claim_scope"] == "technical-evidence-mapping-only" and compliance["certification_claim"] is False, "control mapping cannot be represented as certification"

def main() -> None:
    for key, value in FIX.items():
        validate_record(key, value)
    assert verify_merkle(FIX["security_proof"]), "RFC 9162 proof verification failed"
    semantic_checks(FIX)

    negatives = []
    item = copy.deepcopy(FIX); item["security_proof"]["root_hash"] = "0" * 64; negatives.append(("tampered Merkle root", item))
    item = copy.deepcopy(FIX); item["enforcement_receipt"]["execution_status"] = "executed"; negatives.append(("denied action recorded as executed", item))
    item = copy.deepcopy(FIX); item["containment_attestation"]["out_of_band"] = True; item["containment_attestation"]["independent_control_plane"] = False; negatives.append(("out-of-band containment without independent plane", item))
    item = copy.deepcopy(FIX); item["authorized_assessment"]["scope_enforced"] = False; negatives.append(("assessment without technical scope enforcement", item))
    item = copy.deepcopy(FIX); item["authorized_assessment"]["assessment_type"] = "unrestricted-autonomous-pentest"; negatives.append(("unapproved assessment mode", item))
    item = copy.deepcopy(FIX); item["compliance_evidence_map"]["certification_claim"] = True; negatives.append(("technical mapping misrepresented as certification", item))
    item = copy.deepcopy(FIX); item["audit_chain_record"]["payload"]["outcome"] = "allowed"; negatives.append(("tampered audit-chain payload", item))
    item = copy.deepcopy(FIX); item["security_finding"]["reproduction_method"] = "weaponized-exploit"; negatives.append(("unsafe reproduction method", item))
    item = copy.deepcopy(FIX); item["sbom_attestation"]["critical_count"] = 1; negatives.append(("unrun SBOM scan with invented findings", item))
    item = copy.deepcopy(FIX); item["sandbox_attestation"]["verification_status"] = "pass"; negatives.append(("sandbox pass without test execution", item))

    for label, candidate in negatives:
        try:
            for key, value in candidate.items():
                validate_record(key, value)
            semantic_checks(candidate)
        except Exception:
            continue
        raise AssertionError("negative fixture unexpectedly passed: " + label)

    print(f"PASS: {len(KEYS)} positive contract records, RFC 9162 proof, hash-chained audit verification, and {len(negatives)} negative cases")
    print("LIMIT: no security tool installed, no target scanned, no exploit executed, no signature created or verified, and no incident or C2O private policy data processed")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("FAIL:", exc, file=sys.stderr)
        raise SystemExit(1)
