#!/usr/bin/env python3
"""Validate portable divergence reports, behavioral axes and DSSE attribution receipts."""
from __future__ import annotations
import base64, copy, hashlib, json
from datetime import datetime
from pathlib import Path
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas/divergence/divergence-contracts.v1.schema.json"
FIXTURE_PATH = ROOT / "examples/divergence/divergence-fixtures.v1.json"
KEY_ID = "urn:universal-is:development-divergence-fixture-ed25519-v1"
PUBLIC_KEY = base64.b64decode("GDg9xodG/+f5kttZylZAw+tcHmRQa5CGSx9cUlgoIt4=")
PUBLIC_KEY_SHA256 = "8e811e90a2db78a863f1dc4a75473ed4190b46313f7ca3aa711376e791d8b37c"

def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def dsse_pae(payload_type: bytes, payload: bytes) -> bytes:
    return b"DSSEv1 " + str(len(payload_type)).encode() + b" " + payload_type + b" " + str(len(payload)).encode() + b" " + payload

def validate_report(report: dict, axes: dict) -> None:
    if report["comparison"]["window_end"] < report["comparison"]["window_start"]:
        raise ValueError("comparison window ends before it starts")
    findings = report["findings"]
    if report["status"] == "no_divergence_detected" and findings:
        raise ValueError("no-divergence report cannot contain findings")
    if report["status"] == "divergent" and not findings:
        raise ValueError("divergent report requires findings")
    for item in report["axis_scores"]:
        if item["axis_id"] not in axes:
            raise ValueError("axis score references undefined axis")
        interval = item.get("uncertainty")
        if interval:
            if interval["lower"] > interval["upper"]:
                raise ValueError("confidence interval lower exceeds upper")
            if interval["sample_count"] != item["sample_count"]:
                raise ValueError("interval sample count differs from score sample count")
    if report["domain"] == "identity_federation":
        usable = [x for x in report.get("identity_claims", []) if x["claim"] in {"present", "absent"}]
        if report["status"] == "no_divergence_detected":
            if len(usable) < 2 or len({x["source_ref"] for x in usable}) < 2:
                raise ValueError("identity agreement requires two usable claims from distinct sources")
        if report["status"] == "divergent" and not report["findings"]:
            raise ValueError("identity divergence requires explicit finding")

def verify_receipt(receipt: dict, reports: dict) -> None:
    statement = receipt["statement"]
    predicate = statement["predicate"]
    report = reports.get(predicate["divergence_report_id"])
    if report is None:
        raise ValueError("receipt references unknown report")
    if predicate["report_digest"] != report["report_digest"]:
        raise ValueError("receipt report digest mismatch")
    if statement["subject"][0]["digest"] != report["report_digest"]:
        raise ValueError("in-toto subject does not bind report digest")
    if hashlib.sha256(PUBLIC_KEY).hexdigest() != PUBLIC_KEY_SHA256:
        raise ValueError("fixture public key fingerprint mismatch")
    payload_type = receipt["envelope"]["payloadType"].encode("utf-8")
    payload = base64.b64decode(receipt["envelope"]["payload"], validate=True)
    if payload != canonical_json(statement):
        raise ValueError("DSSE payload mismatch")
    signatures = [s for s in receipt["envelope"]["signatures"] if s["keyid"] == KEY_ID]
    if not signatures:
        raise ValueError("no signature for fixture verifier key")
    verifier = Ed25519PublicKey.from_public_bytes(PUBLIC_KEY)
    pae = dsse_pae(payload_type, payload)
    valid = False
    for sig in signatures:
        try:
            verifier.verify(base64.b64decode(sig["sig"], validate=True), pae)
            valid = True
            break
        except (InvalidSignature, ValueError):
            pass
    if not valid:
        raise ValueError("Ed25519 DSSE signature verification failed")
    if receipt["verification"]["keyid"] != KEY_ID:
        raise ValueError("verification keyid mismatch")
    observed = datetime.fromisoformat(predicate["observed_at"].replace("Z", "+00:00"))
    verified = datetime.fromisoformat(receipt["verification"]["verified_at"].replace("Z", "+00:00"))
    if verified < observed:
        raise ValueError("verification timestamp precedes observation")

def main() -> None:
    schema=json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    data=json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    v=Draft202012Validator(schema,format_checker=FormatChecker())
    axes={}
    for axis in data["behavioral_axis_contracts"]:
        v.validate(axis)
        if axis["score_range"] != {"minimum":0,"maximum":1}:
            raise ValueError("axis range must be normalized [0,1]")
        if axis["axis_id"] in axes:
            raise ValueError("duplicate axis id")
        axes[axis["axis_id"]]=axis
    reports={}
    for item in data["divergence_reports"]:
        v.validate(item)
        validate_report(item,axes)
        reports[item["report_id"]]=item
    for receipt in data["attribution_receipts"]:
        v.validate(receipt)
        verify_receipt(receipt,reports)
    tests=[]
    item=copy.deepcopy(data["behavioral_axis_contracts"][0]); item["score_range"]["maximum"]=2
    tests.append(("non-normalized axis",lambda: (v.validate(item), (_ for _ in ()).throw(ValueError()) if item["score_range"]["maximum"]!=1 else None)))
    item=copy.deepcopy(data["divergence_reports"][0]); item["axis_scores"][0]["axis_id"]="unknown.axis"
    tests.append(("undefined axis",lambda: validate_report(item,axes)))
    item=copy.deepcopy(data["divergence_reports"][0]); item["axis_scores"][0]["uncertainty"]["lower"]=0.9
    tests.append(("invalid confidence interval",lambda: validate_report(item,axes)))
    item=copy.deepcopy(data["divergence_reports"][0]); item["status"]="no_divergence_detected"
    tests.append(("no-divergence with findings",lambda: validate_report(item,axes)))
    item=copy.deepcopy(data["divergence_reports"][7]); item["domain"]="identity_federation"; item["status"]="no_divergence_detected"; item["identity_claims"]=[]
    tests.append(("identity agreement with no claims",lambda: validate_report(item,axes)))
    item=copy.deepcopy(data["divergence_reports"][7]); item["domain"]="identity_federation"; item["status"]="no_divergence_detected"; item["identity_claims"]=[{"source_ref":"s1","vantage_ref":None,"claim":"error","observed_at":"2026-11-12T10:00:00Z"},{"source_ref":"s2","vantage_ref":None,"claim":"error","observed_at":"2026-11-12T10:00:00Z"}]
    tests.append(("identity agreement from errors",lambda: validate_report(item,axes)))
    item=copy.deepcopy(data["attribution_receipts"][0]); item["envelope"]["payload"]=base64.b64encode(b"{}").decode()
    tests.append(("DSSE payload mismatch",lambda: verify_receipt(item,reports)))
    item=copy.deepcopy(data["attribution_receipts"][0]); item["envelope"]["signatures"][0]["sig"]=base64.b64encode(b"bad").decode()
    tests.append(("tampered signature",lambda: verify_receipt(item,reports)))
    item=copy.deepcopy(data["attribution_receipts"][0]); item["statement"]["predicate"]["report_digest"]={"sha256":"f"*64}
    tests.append(("wrong report digest",lambda: verify_receipt(item,reports)))
    item=copy.deepcopy(data["attribution_receipts"][0]); item["verification"]["keyid"]="untrusted"
    tests.append(("verification key mismatch",lambda: verify_receipt(item,reports)))
    item=copy.deepcopy(data["attribution_receipts"][0]); item["verification"]["verified_at"]="2026-11-11T10:00:00Z"
    tests.append(("verification predates observation",lambda: verify_receipt(item,reports)))
    for name,fn in tests:
        try: fn()
        except (ValueError,KeyError,TypeError): continue
        raise AssertionError("negative test unexpectedly passed: "+name)
    print(f"PASS: {len(axes)} behavioral axes; {len(reports)} domain reports; {len(data['attribution_receipts'])} signed attribution receipt; {len(tests)} negative tests.")

if __name__ == "__main__":
    main()
