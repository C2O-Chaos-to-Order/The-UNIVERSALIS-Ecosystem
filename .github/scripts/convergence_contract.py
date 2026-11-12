#!/usr/bin/env python3
"""Validate portable convergence contracts and a disposable DSSE/Ed25519 fixture."""
from __future__ import annotations
import base64, copy, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "schemas/convergence/convergence-contracts.v1.schema.json").read_text())
FIXTURE = json.loads((ROOT / "examples/convergence/convergence-fixtures.v1.json").read_text())

def canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def validate_semantics(groups: dict) -> None:
    intents = groups["shared_intent_contracts"]
    for item in intents:
        refs = {p["participant_ref"] for p in item["participants"]}
        reading_refs = [r["participant_ref"] for r in item["problem_readings"]]
        if len(reading_refs) != len(set(reading_refs)) or set(reading_refs) != refs:
            raise ValueError("shared intent must include exactly one reading per participant")
        if item["status"] == "locked":
            if item.get("unresolved_issues", []):
                raise ValueError("locked intent cannot conceal unresolved issues")
            if not all(r["included"] for r in item["problem_readings"]):
                raise ValueError("locked intent omitted a participant reading")
            terms = [t["term"].casefold() for t in item["key_terms"]]
            if len(terms) != len(set(terms)):
                raise ValueError("locked intent has duplicate term definitions")
    for item in groups["consensus_certificates"]:
        people = item["participants"]
        if len({p["participant_ref"] for p in people}) != len(people):
            raise ValueError("duplicate consensus participant")
        all_pass = all(p["status"] == "pass" and p["score"] >= p["satisfaction_bar"] for p in people)
        if item["outcome"] == "converged" and not all_pass:
            raise ValueError("converged certificate requires every participant to clear its satisfaction bar")
        if item["outcome"] != "converged" and item["selected_option"] is not None:
            raise ValueError("non-converged outcome must not publish a selected consensus option")
        if item["outcome"] == "converged" and item["selected_option"] not in item["options_considered"]:
            raise ValueError("selected consensus option was not considered")
    for item in groups["negotiation_transcripts"]:
        parties = set(item["parties"])
        if len(item["parties"]) != len(parties):
            raise ValueError("duplicate negotiation party")
        seq = [m["sequence"] for m in item["moves"]]
        if seq != sorted(seq) or len(seq) != len(set(seq)):
            raise ValueError("negotiation move sequence must be unique and ordered")
        if any(m["actor_ref"] not in parties for m in item["moves"]):
            raise ValueError("negotiation move actor is not a party")
        if item["outcome"] == "agreement":
            if set(item["accepted_by"]) != parties:
                raise ValueError("agreement requires explicit acceptance by every party")
            if item["batna_claim"] == "verified_safe":
                checks = {c["party_ref"]: c for c in item["reservation_checks"]}
                if set(checks) != parties or any(checks[p]["result"] != "pass" or checks[p]["method"] == "not_disclosed" for p in parties):
                    raise ValueError("BATNA-safe claim requires verified passing check for every party")
        elif item["batna_claim"] == "verified_safe":
            raise ValueError("BATNA-safe claim requires an agreement outcome")
    for item in groups["merge_plans"]:
        if len({o["operation_id"] for o in item["operations"]}) != len(item["operations"]):
            raise ValueError("duplicate merge operation ID")
        open_conflicts = [c for c in item["conflicts"] if c["status"] != "resolved"]
        if item["status"] == "applied":
            if not item["approval_ref"] or not item["applied_at"]:
                raise ValueError("applied merge requires review approval and apply timestamp")
            if open_conflicts:
                raise ValueError("applied merge cannot retain unresolved conflicts")
            if item["observed_target_digest"] != item["expected_target_digest"]:
                raise ValueError("stale target: apply precondition digest changed")
        if item["status"] in {"proposed","reviewed","approved","rejected","stale"} and item["applied_at"] is not None:
            raise ValueError("non-applied merge cannot claim applied timestamp")
    for item in groups["ontology_alignment_receipts"]:
        accepted = item["status"] == "accepted"
        if accepted:
            if not item["reviewer_ref"] or item["round_trip_validation"] != "passed":
                raise ValueError("accepted alignment requires independent reviewer and passing round-trip validation")
            if any(c["relation"] != "unmapped" and not c["evidence_refs"] for c in item["correspondences"]):
                raise ValueError("accepted correspondence lacks evidence")
        if any(c["relation"] == "unmapped" and c["target_concept_ref"] is not None for c in item["correspondences"]):
            raise ValueError("unmapped correspondence must not invent a target concept")
    for item in groups["argumentation_receipts"]:
        known = {a["argument_ref"] for a in item["arguments"]}
        threshold = item.get("acceptance_threshold", 1.0)
        if any(e["attacker_ref"] not in known or e["target_ref"] not in known for e in item["attack_edges"]):
            raise ValueError("argument attack edge references an unknown argument")
        if any(e["confidence"] < threshold for e in item["attack_edges"]):
            raise ValueError("attack edge is below the declared inclusion threshold")
        if not set(item["accepted_argument_refs"]).issubset(known) or not set(item["rejected_argument_refs"]).issubset(known):
            raise ValueError("argumentation outcome references unknown argument")
    for item in groups["dispute_outcomes"]:
        parties = set(item["parties"])
        if any(a["party_ref"] not in parties for a in item["awards"]):
            raise ValueError("dispute award references a non-party")
        if item["outcome"] == "settled":
            if not item["awards"] or abs(sum(a["percentage"] for a in item["awards"]) - 100.0) > 1e-6:
                raise ValueError("settled dispute awards must sum to 100 percent")
        elif item["awards"]:
            raise ValueError("unresolved or referred dispute cannot distribute settlement awards")
        if item["enforcement_authorized"] is not False:
            raise ValueError("portable dispute outcome must not itself authorize enforcement")

def dsse_pae(payload_type: bytes, payload: bytes) -> bytes:
    return b"DSSEv1 " + str(len(payload_type)).encode() + b" " + payload_type + b" " + str(len(payload)).encode() + b" " + payload

def verify_bundles(bundles: list[dict], groups: dict) -> None:
    cert = groups["consensus_certificates"][0]
    expected_cert = hashlib.sha256(canonical(cert)).hexdigest()
    for bundle in bundles:
        env = bundle["envelope"]
        if env["payloadType"] != bundle["payload_type"] or env["payload"] != bundle["payload"]:
            raise ValueError("DSSE envelope/payload mismatch")
        payload = base64.b64decode(env["payload"], validate=True)
        statement = json.loads(payload)
        if statement.get("_type") != "https://in-toto.io/Statement/v1":
            raise ValueError("wrong in-toto statement type")
        subject = statement["subject"][0]["digest"]["sha256"]
        if subject != expected_cert or subject != bundle["expected_subject_digest"]:
            raise ValueError("signed statement does not bind the expected consensus certificate")
        key = base64.b64decode(bundle["verification_key"]["public_key"], validate=True)
        if "sha256:" + hashlib.sha256(key).hexdigest() != bundle["verification_key"]["keyid"]:
            raise ValueError("verification key ID mismatch")
        pae = dsse_pae(env["payloadType"].encode(), payload)
        sigs = env["signatures"]
        if not sigs:
            raise ValueError("DSSE envelope has no signatures")
        verified = False
        for sig in sigs:
            if sig["keyid"] != bundle["verification_key"]["keyid"]:
                continue
            try:
                Ed25519PublicKey.from_public_bytes(key).verify(base64.b64decode(sig["sig"], validate=True), pae)
                verified = True
            except Exception:
                continue
        if not verified:
            raise ValueError("DSSE Ed25519 signature verification failed")

def reject(name: str, fn) -> None:
    try:
        fn()
    except (ValueError, KeyError, TypeError, ValidationError):
        return
    raise AssertionError("negative test unexpectedly passed: " + name)

def main() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    validator = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
    groups = FIXTURE["records"]
    total = 0
    for records in groups.values():
        for record in records:
            validator.validate(record)
            total += 1
    validate_semantics(groups)
    verify_bundles(FIXTURE["signed_bundles"], groups)
    tests = []
    x=copy.deepcopy(groups["consensus_certificates"][0]); x["participants"][1]["status"]="below_bar"
    tests.append(("consensus below satisfaction bar",lambda:validate_semantics({**groups,"consensus_certificates":[x]})))
    x=copy.deepcopy(groups["consensus_certificates"][0]); x["participants"][0]["score"]=0.2
    tests.append(("score below declared bar",lambda:validate_semantics({**groups,"consensus_certificates":[x]})))
    x=copy.deepcopy(groups["shared_intent_contracts"][0]); x["problem_readings"][1]["included"]=False
    tests.append(("locked intent excludes participant reading",lambda:validate_semantics({**groups,"shared_intent_contracts":[x]})))
    x=copy.deepcopy(groups["shared_intent_contracts"][0]); x["key_terms"].append(copy.deepcopy(x["key_terms"][0]))
    tests.append(("duplicate semantic term",lambda:validate_semantics({**groups,"shared_intent_contracts":[x]})))
    x=copy.deepcopy(groups["negotiation_transcripts"][0]); x["accepted_by"].pop()
    tests.append(("agreement without unanimous acceptance",lambda:validate_semantics({**groups,"negotiation_transcripts":[x]})))
    x=copy.deepcopy(groups["negotiation_transcripts"][0]); x["reservation_checks"][0]["result"]="unverified"
    tests.append(("BATNA-safe claim with unverified party",lambda:validate_semantics({**groups,"negotiation_transcripts":[x]})))
    x=copy.deepcopy(groups["merge_plans"][0]); x["status"]="applied"; x["applied_at"]="2026-11-12T19:40:00Z"; x["approval_ref"]=None
    tests.append(("merge applied without approval",lambda:validate_semantics({**groups,"merge_plans":[x]})))
    x=copy.deepcopy(groups["merge_plans"][0]); x["status"]="applied"; x["applied_at"]="2026-11-12T19:40:00Z"; x["conflicts"]=[{"conflict_id":"c1","status":"open","resolution_ref":None}]
    tests.append(("merge applied with open conflict",lambda:validate_semantics({**groups,"merge_plans":[x]})))
    x=copy.deepcopy(groups["merge_plans"][0]); x["status"]="applied"; x["applied_at"]="2026-11-12T19:40:00Z"; x["approval_ref"]="review"; x["observed_target_digest"]="9"*64
    tests.append(("stale merge target",lambda:validate_semantics({**groups,"merge_plans":[x]})))
    x=copy.deepcopy(groups["ontology_alignment_receipts"][0]); x["reviewer_ref"]=None
    tests.append(("accepted ontology alignment without reviewer",lambda:validate_semantics({**groups,"ontology_alignment_receipts":[x]})))
    x=copy.deepcopy(groups["ontology_alignment_receipts"][0]); x["round_trip_validation"]="not_run"
    tests.append(("accepted ontology alignment without round-trip validation",lambda:validate_semantics({**groups,"ontology_alignment_receipts":[x]})))
    x=copy.deepcopy(groups["dispute_outcomes"][0]); x["awards"][0]["percentage"]=75
    tests.append(("settlement awards do not total 100 percent",lambda:validate_semantics({**groups,"dispute_outcomes":[x]})))
    x=copy.deepcopy(groups["dispute_outcomes"][0]); x["enforcement_authorized"]=True
    tests.append(("portable dispute receipt claims enforcement authority",lambda:validator.validate(x)))
    x=copy.deepcopy(FIXTURE["signed_bundles"][0]); x["envelope"]["signatures"][0]["sig"]=base64.b64encode(b"tampered").decode()
    tests.append(("tampered DSSE signature",lambda:verify_bundles([x],groups)))
    for name,fn in tests: reject(name,fn)
    print(f"PASS: {total} convergence records; {len(FIXTURE['signed_bundles'])} DSSE bundle; {len(tests)} negative tests.")
if __name__ == "__main__":
    main()
