#!/usr/bin/env python3
"""Validate safe, portable insurgence threat, resistance, containment and campaign contracts."""
from __future__ import annotations
import base64, copy, hashlib, json
from datetime import datetime
from pathlib import Path
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas/insurgence/insurgence-contracts.v1.schema.json"
FIXTURE_PATH = ROOT / "examples/insurgence/insurgence-fixtures.v1.json"
KEY_ID = "urn:universalis:insurgence-fixture-ed25519-v1"
PUBLIC_KEY = base64.b64decode("tG0WzzM43uVEGOUtI0ch0asaSDtMNf1aWleM8pnfYog=")
PUBLIC_KEY_SHA256 = "54a2cbefa54c87a29cf3d8dab00db8c83a2cac49ad2f064373bb38bae91ca5fe"

def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def dsse_pae(payload_type: bytes, payload: bytes) -> bytes:
    return b"DSSEv1 " + str(len(payload_type)).encode() + b" " + payload_type + b" " + str(len(payload)).encode() + b" " + payload

def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

def validate_threat_model(record: dict) -> None:
    start = parse_time(record["scope"]["assessment_window"]["start"])
    end = parse_time(record["scope"]["assessment_window"]["end"])
    if end < start:
        raise ValueError("threat assessment window ends before it starts")
    ids = [item["claim_id"] for item in record["evidence_tiers"]]
    if len(ids) != len(set(ids)):
        raise ValueError("threat-model claim IDs must be unique")
    for item in record["evidence_tiers"]:
        if item["tier"] == "established" and not item["evidence_refs"]:
            raise ValueError("established claims require direct evidence references")
        if not item["limitations"]:
            raise ValueError("every evidence tier requires limitations")

def validate_resistance(record: dict) -> None:
    separation = record["separation_of_powers"]
    human = record["human_command"]
    all_controls = all(separation.values()) and all(human.values())
    results = [item["outcome"] for item in record["test_results"]]
    if record["overall_result"] == "pass" and (not all_controls or not results or any(x != "pass" for x in results)):
        raise ValueError("pass requires every declared separation, human-command and test condition to pass")
    if record["overall_result"] == "fail" and all(x == "pass" for x in results):
        raise ValueError("failed attestation cannot have only passing tests")
    metrics = record["utility_metrics"]
    if metrics["false_stop_rate"] > 1 or metrics["task_success_rate"] > 1:
        raise ValueError("utility metrics must be normalized rates")
    if record["environment"]["mode"] == "production" and record["overall_result"] == "pass" and not record["limitations"]:
        raise ValueError("production attestations must preserve limitations")

def validate_containment(record: dict) -> None:
    detected = parse_time(record["detection_at"])
    started = parse_time(record["containment_started_at"])
    enforced = parse_time(record["containment_enforced_at"])
    if not (detected <= started <= enforced):
        raise ValueError("containment timestamps must be detection <= start <= enforcement")
    if record["agent_can_override"] or record["agent_can_approve_release"]:
        raise ValueError("the agent cannot override containment or approve release")
    if record["release_state"] in {"approved_for_restore", "restored"}:
        raise ValueError("release/restore requires a separate human-authorized decision record")

def validate_campaign(record: dict) -> None:
    stage_ids = [s["stage_id"] for s in record["stages"]]
    required = ["brief_capture","evidence_and_assumption_audit","community_listening","message_and_channel_design","small_scale_validation","transparent_publication","impact_review_and_correction"]
    if stage_ids != required:
        raise ValueError("campaign stages must follow the seven-stage ordered workflow")
    if not record["sponsor_disclosure"].strip():
        raise ValueError("campaign requires sponsor disclosure")
    if not all(record["consent_and_privacy"].values()):
        raise ValueError("campaign consent and privacy constraints must all be true")
    if not all(record["nonviolent_constraints"].values()):
        raise ValueError("campaign nonviolence and integrity constraints must all be true")
    for claim in record["factual_claims"]:
        if not claim["source_refs"]:
            raise ValueError("factual campaign claims require source references")

def verify_signed_attestation(attestation: dict, records: dict) -> None:
    kind = attestation["attestation_type"]
    predicate = attestation["statement"]["predicate"]
    target_id_key = {"threat_model":"model_id","resistance_attestation":"attestation_id","containment_receipt":"receipt_id"}[kind]
    target = records[kind].get(predicate[target_id_key])
    if target is None:
        raise ValueError("signed attestation points to missing record")
    digest = hashlib.sha256(canonical_json(target)).hexdigest()
    if attestation["statement"]["subject"][0]["digest"]["sha256"] != digest:
        raise ValueError("in-toto subject digest does not bind the referenced record")
    envelope = attestation["envelope"]
    payload = base64.b64decode(envelope["payload"], validate=True)
    statement_bytes = canonical_json(attestation["statement"])
    if payload != statement_bytes:
        raise ValueError("DSSE payload does not equal canonical in-toto statement")
    if hashlib.sha256(PUBLIC_KEY).hexdigest() != PUBLIC_KEY_SHA256:
        raise ValueError("fixture key fingerprint mismatch")
    signatures = [s for s in envelope["signatures"] if s["keyid"] == KEY_ID]
    if not signatures:
        raise ValueError("no signature for fixture verification key")
    verifier = Ed25519PublicKey.from_public_bytes(PUBLIC_KEY)
    pae = dsse_pae(envelope["payloadType"].encode("utf-8"), payload)
    verified = False
    for item in signatures:
        try:
            verifier.verify(base64.b64decode(item["sig"], validate=True), pae)
            verified = True
            break
        except (InvalidSignature, ValueError):
            continue
    if not verified:
        raise ValueError("DSSE Ed25519 signature verification failed")
    if attestation["verification"]["keyid"] != KEY_ID:
        raise ValueError("verification key ID does not match the verified signature")
    if parse_time(attestation["verification"]["verified_at"]) < parse_time(predicate.get("observed_at", "2026-11-12T10:00:00Z")):
        raise ValueError("verification timestamp precedes the attested observation")

def expect_reject(name: str, fn) -> None:
    try:
        fn()
    except (ValueError, KeyError, TypeError, ValidationError):
        return
    raise AssertionError("negative test unexpectedly passed: " + name)

def main() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    records = {
        "threat_model": {x["model_id"]:x for x in data["threat_models"]},
        "resistance_attestation": {x["attestation_id"]:x for x in data["resistance_attestations"]},
        "containment_receipt": {x["receipt_id"]:x for x in data["containment_receipts"]}
    }
    for kind in ("threat_models","resistance_attestations","containment_receipts","resistance_campaign_plans","signed_attestations"):
        for record in data[kind]:
            validator.validate(record)
    for record in data["threat_models"]: validate_threat_model(record)
    for record in data["resistance_attestations"]: validate_resistance(record)
    for record in data["containment_receipts"]: validate_containment(record)
    for record in data["resistance_campaign_plans"]: validate_campaign(record)
    for record in data["signed_attestations"]: verify_signed_attestation(record, records)

    tests = []
    record=copy.deepcopy(data["threat_models"][0]); record["evidence_tiers"][0]["tier"]="unsupported"
    tests.append(("unknown evidence tier",lambda:(validator.validate(record),validate_threat_model(record))))
    record=copy.deepcopy(data["threat_models"][0]); record["evidence_tiers"][0]["evidence_refs"]=[]
    tests.append(("established claim without source",lambda:validate_threat_model(record)))
    record=copy.deepcopy(data["resistance_campaign_plans"][0]); record["nonviolent_constraints"]["no_deception"]=False
    tests.append(("deceptive campaign",lambda:validate_campaign(record)))
    record=copy.deepcopy(data["resistance_campaign_plans"][0]); record["factual_claims"][0]["source_refs"]=[]
    tests.append(("campaign claim without source",lambda:validate_campaign(record)))
    record=copy.deepcopy(data["resistance_attestations"][0]); record["test_results"][0]["outcome"]="fail"
    tests.append(("pass with failed resistance test",lambda:validate_resistance(record)))
    record=copy.deepcopy(data["resistance_attestations"][0]); record["human_command"]["agent_cannot_approve_own_shutdown_or_release"]=False
    tests.append(("agent may approve shutdown",lambda:validate_resistance(record)))
    record=copy.deepcopy(data["resistance_attestations"][0]); record["human_command"]["independent_stop_path_available"]=False
    tests.append(("missing independent stop path",lambda:validate_resistance(record)))
    record=copy.deepcopy(data["containment_receipts"][0]); record["agent_can_override"]=True
    tests.append(("agent can override containment",lambda:validate_containment(record)))
    record=copy.deepcopy(data["containment_receipts"][0]); record["containment_enforced_at"]="2026-11-12T09:59:59Z"
    tests.append(("containment timestamp inversion",lambda:validate_containment(record)))
    record=copy.deepcopy(data["containment_receipts"][0]); record["release_state"]="restored"
    tests.append(("restore without separate human record",lambda:validate_containment(record)))
    record=copy.deepcopy(data["signed_attestations"][0]); record["envelope"]["payload"]=base64.b64encode(b"{}").decode()
    tests.append(("DSSE payload tampering",lambda:verify_signed_attestation(record,records)))
    record=copy.deepcopy(data["signed_attestations"][0]); record["envelope"]["signatures"][0]["sig"]=base64.b64encode(b"bad").decode()
    tests.append(("DSSE signature tampering",lambda:verify_signed_attestation(record,records)))
    for name,fn in tests: expect_reject(name,fn)
    print(f"PASS: {len(data['threat_models'])} threat models; {len(data['resistance_attestations'])} resistance attestations; {len(data['containment_receipts'])} containment receipts; {len(data['resistance_campaign_plans'])} campaign plans; {len(data['signed_attestations'])} cryptographic attestations; {len(tests)} negative tests.")

if __name__ == "__main__": main()
