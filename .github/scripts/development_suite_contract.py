#!/usr/bin/env python3
"""Validate shared project-format, capability and signed provenance contracts."""
from __future__ import annotations
import base64, copy, hashlib, json, re
from datetime import datetime
from pathlib import Path
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_FILE = ROOT / "schemas/development-suite/development-suite-contracts.v1.schema.json"
FIXTURE_FILE = ROOT / "examples/development-suite/development-suite-fixtures.v1.json"
KEY_ID = "urn:universal.is:fixture-ed25519-2026-11"
PUBLIC_KEY = base64.b64decode("O2onvM62pC1io6jQKm8Nc2UyFXcd4kOmOsBIoYtZ2ik=")
PUBLIC_KEY_SHA256 = "139e3940e64b5491722088d9a0d741628fc826e09475d341a780acde3c4b8070"
HIGH_IMPACT = {"release", "publish", "deploy"}

def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def dsse_pae(payload_type: bytes, payload: bytes) -> bytes:
    return b"DSSEv1 " + str(len(payload_type)).encode() + b" " + payload_type + b" " + str(len(payload)).encode() + b" " + payload

def verify_receipt(record: dict) -> None:
    statement = record["statement"]
    for subject in statement["subject"]:
        digest = subject["digest"].get("sha256", "")
        if not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("subject SHA-256 must be exactly 64 lowercase hexadecimal characters")
    envelope = record["envelope"]
    payload = base64.b64decode(envelope["payload"], validate=True)
    if payload != canonical_json(statement):
        raise ValueError("DSSE payload is not the canonical statement")
    if hashlib.sha256(PUBLIC_KEY).hexdigest() != PUBLIC_KEY_SHA256:
        raise ValueError("fixture key fingerprint mismatch")
    matching = [s for s in envelope["signatures"] if s["keyid"] == KEY_ID]
    if not matching:
        raise ValueError("no signature for trusted fixture key")
    public_key = Ed25519PublicKey.from_public_bytes(PUBLIC_KEY)
    pae = dsse_pae(envelope["payloadType"].encode("utf-8"), payload)
    verified = False
    for item in matching:
        try:
            public_key.verify(base64.b64decode(item["sig"], validate=True), pae)
            verified = True
            break
        except (InvalidSignature, ValueError):
            pass
    if not verified:
        raise ValueError("DSSE signature verification failed")
    if record["verification"]["keyid"] != KEY_ID:
        raise ValueError("verification record keyid mismatch")
    metadata = statement["predicate"]["runDetails"]["metadata"]
    start = datetime.fromisoformat(metadata["startedOn"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(metadata["finishedOn"].replace("Z", "+00:00"))
    if end < start:
        raise ValueError("build finished before it started")

def validate_record(record: dict, validator: Draft202012Validator) -> None:
    errors = list(validator.iter_errors(record))
    if errors:
        raise ValueError("; ".join(e.message for e in errors[:3]))
    if record["record_type"] == "agent_capability_manifest":
        for cap in record["capabilities"]:
            if cap["effect"] in HIGH_IMPACT and cap["approval_mode"] not in {"human_permit", "owner_policy_gate"}:
                raise ValueError("release/publish/deploy requires a human or owner gate")
            if cap["destructive_or_external_effect"] and cap["approval_mode"] == "none":
                raise ValueError("effectful capability cannot be approval-free")
    if record["record_type"] == "build_provenance_receipt":
        verify_receipt(record)

def expect_reject(name: str, record: dict, validator: Draft202012Validator) -> None:
    try:
        validate_record(record, validator)
    except (ValueError, KeyError, TypeError):
        return
    raise AssertionError("negative test unexpectedly passed: " + name)

def run() -> None:
    schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    fixtures = json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    records = fixtures["project_format_contracts"] + fixtures["agent_capability_manifests"] + fixtures["build_provenance_receipts"]
    for record in records:
        validate_record(record, validator)
    tests = []
    record = copy.deepcopy(fixtures["project_format_contracts"][0]); record.pop("format_version")
    tests.append(("missing format version", record))
    record = copy.deepcopy(fixtures["agent_capability_manifests"][0]); record["capabilities"][0]["scope"] = []
    tests.append(("empty capability scope", record))
    record = copy.deepcopy(fixtures["agent_capability_manifests"][0]); record["capabilities"][2]["approval_mode"] = "none"
    tests.append(("publish without human gate", record))
    record = copy.deepcopy(fixtures["agent_capability_manifests"][0]); record["capabilities"][1]["destructive_or_external_effect"] = True; record["capabilities"][1]["approval_mode"] = "none"
    tests.append(("effectful write without approval", record))
    record = copy.deepcopy(fixtures["build_provenance_receipts"][0]); record["envelope"]["signatures"] = []
    tests.append(("unsigned envelope", record))
    record = copy.deepcopy(fixtures["build_provenance_receipts"][0]); record["envelope"]["signatures"][0]["sig"] = base64.b64encode(b"invalid").decode()
    tests.append(("tampered signature", record))
    record = copy.deepcopy(fixtures["build_provenance_receipts"][0]); record["envelope"]["payload"] = base64.b64encode(b"{}").decode()
    tests.append(("payload does not bind statement", record))
    record = copy.deepcopy(fixtures["build_provenance_receipts"][0]); record["statement"]["predicate"]["runDetails"]["metadata"]["finishedOn"] = "2026-11-12T09:00:00Z"; record["envelope"]["payload"] = base64.b64encode(canonical_json(record["statement"])).decode()
    tests.append(("statement mutated after signing", record))
    record = copy.deepcopy(fixtures["build_provenance_receipts"][0]); record["statement"]["predicate"]["runDetails"].pop("builder")
    tests.append(("missing builder identity", record))
    record = copy.deepcopy(fixtures["build_provenance_receipts"][0]); record["statement"]["subject"][0]["digest"]["sha256"] = "abc"
    tests.append(("invalid artifact SHA-256 length", record))
    for name, record in tests:
        expect_reject(name, record, validator)
    print(f"PASS: {len(records)} shared fixture records; {len(tests)} negative tests; DSSE Ed25519 signature verified.")

if __name__ == "__main__":
    run()
