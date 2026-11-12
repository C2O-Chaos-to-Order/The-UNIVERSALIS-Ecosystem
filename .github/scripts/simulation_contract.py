#!/usr/bin/env python3
"""Locally validate portable simulation contracts, replay evidence and world-model claims."""
from __future__ import annotations
import base64
import copy
import hashlib
import json
from pathlib import Path
from collections import defaultdict
from jsonschema import Draft202012Validator, FormatChecker
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas/simulation/simulation-contracts.v1.schema.json"
FIXTURE_PATH = ROOT / "examples/simulation/simulation-fixtures.v1.json"
GENESIS = "GENESIS"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_replay_signature(receipt: dict, verification_key: dict) -> None:
    signature = receipt["signature"]
    body = copy.deepcopy(receipt)
    body.pop("signature")
    body_bytes = canonical(body)
    require(sha256_bytes(body_bytes) == signature["signed_body_digest"], "replay receipt signed-body digest mismatch")
    public_key = base64.b64decode(verification_key["public_key_base64"], validate=True)
    key_id = sha256_bytes(public_key)
    require(key_id == verification_key["key_id"] == signature["key_id"], "replay receipt verification key identity mismatch")
    require(verification_key["algorithm"] == signature["algorithm"] == "Ed25519", "replay receipt signature algorithm mismatch")
    require(verification_key["trust_anchor_kind"] == signature["trust_anchor_kind"], "replay receipt trust-anchor class mismatch")
    Ed25519PublicKey.from_public_bytes(public_key).verify(
        base64.b64decode(signature["signature_base64"], validate=True), body_bytes
    )


def validate_fixture(fixture: dict) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    records = fixture["records"]
    flattened = [item for group in records.values() for item in group]
    for item in flattened:
        validator.validate(item)

    ids = [x["record_id"] for x in flattened]
    require(len(ids) == len(set(ids)), "record_id values must be globally unique within a fixture bundle")
    contracts = {x["simulation_id"]: x for x in records["simulation_contracts"]}
    runs = defaultdict(list)
    for event in records["trace_events"]:
        runs[(event["simulation_id"], event["run_id"])].append(event)

    # A trace is verifiable only when every event hash and predecessor link is recomputed.
    for (simulation_id, run_id), events in runs.items():
        events.sort(key=lambda x: x["sequence"])
        previous = GENESIS
        for expected_seq, event in enumerate(events):
            require(event["simulation_id"] == simulation_id and event["run_id"] == run_id, "trace grouping mismatch")
            require(event["sequence"] == expected_seq, "trace sequence must be contiguous and start at zero")
            require(event["previous_event_hash"] == previous, "trace predecessor hash mismatch")
            body = copy.deepcopy(event)
            claimed_hash = body.pop("event_hash")
            require(sha256_bytes(canonical(body)) == claimed_hash, "trace event hash mismatch")
            previous = claimed_hash

    trace_by_id = {x["record_id"]: x for x in records["trace_events"]}
    for decision in records["agent_decisions"]:
        event = trace_by_id.get(decision["action_trace_ref"])
        require(event is not None, "agent decision references an unknown action trace event")
        require(event["event_kind"] == "action", "agent decision must bind to an action event")
        require(event["simulation_id"] == decision["simulation_id"] and event["run_id"] == decision["run_id"], "agent decision and action trace scope mismatch")
        require(event["action_digest"] == decision["action_digest"], "agent decision action digest does not match trace event")

    replay_by_id = {x["record_id"]: x for x in records["replay_receipts"]}
    for receipt in records["replay_receipts"]:
        contract = contracts.get(receipt["simulation_id"])
        require(contract is not None, "replay receipt references an unknown simulation contract")
        require(receipt["contract_digest"] == digest(contract), "replay receipt contract digest mismatch")
        require(receipt["model_digest"] == contract["model"]["model_digest"], "replay receipt model digest mismatch")
        require(receipt["environment_digest"] == contract["environment"]["environment_digest"], "replay receipt environment digest mismatch")
        require(receipt["inputs_digest"] == contract["inputs_digest"], "replay receipt input digest mismatch")
        require(receipt["parameters_digest"] == contract["execution"]["parameters_digest"], "replay receipt parameter digest mismatch")
        run_events = runs.get((receipt["simulation_id"], receipt["run_id"]), [])
        require(bool(run_events), "replay receipt references a run with no trace events")
        require(receipt["trace_root"] == run_events[-1]["event_hash"], "replay receipt trace root mismatch")
        require(receipt["final_state_digest"] == run_events[-1]["after_state_digest"], "replay receipt final state does not match trace")
        if receipt["replay_outcome"] == "exact_match":
            require(receipt["determinism_class"] == "deterministic" and receipt["repeat_count"] >= 2, "exact replay requires deterministic declaration and repeated execution")
        verify_replay_signature(receipt, fixture["verification_key"])

    # Uncertainty decisions are evidence, never authority. Unsatisfied constraints cannot produce a go-like verdict.
    for decision in records["decision_receipts"]:
        require(decision["replay_receipt_ref"] in replay_by_id, "decision receipt references an unknown replay receipt")
        if any(not x["satisfied"] for x in decision["constraints"]):
            require(decision["verdict"] in {"escalate", "stop"}, "unsatisfied risk constraint cannot result in proceed_to_human_review")

    # A synthetic or simulated reference set cannot be presented as external-world validation.
    validations = {x["model_digest"]: x for x in records["world_model_validations"]}
    for item in records["world_model_validations"]:
        if item["external_validation_completed"]:
            require(item["reference_evidence_class"] in {"observed", "measured", "mixed"}, "external validation needs observed/measured reference evidence")
            require(item["independent_evaluator"] is True, "external validation requires an independent evaluator")
            require(item["holdout_digest"] is not None, "external validation requires a declared holdout digest")
            if item["training_data_digest"] is not None:
                require(item["training_data_digest"] != item["holdout_digest"], "training and holdout digests must differ")
    for contract in records["simulation_contracts"]:
        if contract["study_scope"]["validity_claim"] == "validated_within_declared_scope":
            item = validations.get(contract["model"]["model_digest"])
            require(item is not None and item["validation_status"] == "within_scope_supported" and item["external_validation_completed"], "contract cannot claim external validity without matching world-model validation evidence")

    for critic in records["critic_verdicts"]:
        if critic["verdict"] == "accept_within_declared_scope":
            require(critic["independent_of_model_author"] is True, "critic acceptance requires reviewer independence")
            require(bool(critic["accepted_scope"]), "critic acceptance must name its bounded scope")
            require(all(x["result"] == "pass" for x in critic["checks"]), "critic acceptance requires every declared check to pass")


def expect_failure(name: str, mutate) -> str:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    mutate(fixture)
    try:
        validate_fixture(fixture)
    except Exception:
        return name
    raise AssertionError(f"negative test unexpectedly passed: {name}")


def run_negative_tests() -> list[str]:
    tests = []
    def add(name, fn): tests.append((name, fn))
    add("trace_event_hash_tamper", lambda f: f["records"]["trace_events"][1].__setitem__("after_state_digest", "sha256:"+"f"*64))
    add("trace_previous_hash_tamper", lambda f: f["records"]["trace_events"][1].__setitem__("previous_event_hash", "sha256:"+"f"*64))
    add("trace_sequence_gap", lambda f: f["records"]["trace_events"][2].__setitem__("sequence", 5))
    add("receipt_signature_tamper", lambda f: f["records"]["replay_receipts"][0]["signature"].__setitem__("signature_base64", base64.b64encode(b"x"*64).decode()))
    add("receipt_signed_digest_tamper", lambda f: f["records"]["replay_receipts"][0]["signature"].__setitem__("signed_body_digest", "sha256:"+"f"*64))
    add("wrong_verification_key", lambda f: f["verification_key"].__setitem__("key_id", "sha256:"+"f"*64))
    add("contract_digest_mismatch", lambda f: f["records"]["replay_receipts"][0].__setitem__("contract_digest", "sha256:"+"f"*64))
    add("model_digest_mismatch", lambda f: f["records"]["replay_receipts"][0].__setitem__("model_digest", "sha256:"+"f"*64))
    add("environment_digest_mismatch", lambda f: f["records"]["replay_receipts"][0].__setitem__("environment_digest", "sha256:"+"f"*64))
    add("trace_root_mismatch", lambda f: f["records"]["replay_receipts"][0].__setitem__("trace_root", "sha256:"+"f"*64))
    add("unknown_contract_reference", lambda f: f["records"]["replay_receipts"][0].__setitem__("simulation_id", "simulation:missing"))
    add("decision_implies_authority", lambda f: f["records"]["decision_receipts"][0].__setitem__("authorization_implied", True))
    add("decision_missing_replay", lambda f: f["records"]["decision_receipts"][0].__setitem__("replay_receipt_ref", "replay:missing"))
    def bad_risk(f):
        d=f["records"]["decision_receipts"][0]; d["constraints"][0]["satisfied"]=False; d["verdict"]="proceed_to_human_review"
    add("unsatisfied_constraint_proceed", bad_risk)
    add("synthetic_claim_as_external_validation", lambda f: f["records"]["world_model_validations"][0].__setitem__("external_validation_completed", True))
    add("self_certified_world_model", lambda f: (f["records"]["world_model_validations"][0].update({"reference_evidence_class":"measured","external_validation_completed":True,"holdout_digest":"sha256:"+"b"*64,"independent_evaluator":False,"validation_status":"within_scope_supported"})))
    add("training_holdout_leakage", lambda f: (f["records"]["world_model_validations"][0].update({"reference_evidence_class":"measured","external_validation_completed":True,"holdout_digest":f["records"]["world_model_validations"][0]["training_data_digest"],"independent_evaluator":True,"validation_status":"within_scope_supported"})))
    add("false_contract_validity_claim", lambda f: f["records"]["simulation_contracts"][0]["study_scope"].__setitem__("validity_claim", "validated_within_declared_scope"))
    def critic_self_approval(f):
        c=f["records"]["critic_verdicts"][0]; c["independent_of_model_author"]=False; c["verdict"]="accept_within_declared_scope"; c["accepted_scope"]=["real world"]
    add("critic_self_approval", critic_self_approval)
    add("provenance_payload_export", lambda f: f["records"]["provenance_labels"][0].__setitem__("raw_source_payload_included", True))
    add("contract_private_payload_export", lambda f: f["records"]["simulation_contracts"][0].__setitem__("private_payload_included", True))
    add("duplicate_record_identifier", lambda f: f["records"]["provenance_labels"][0].__setitem__("record_id", f["records"]["simulation_contracts"][0]["record_id"]))
    add("agent_decision_action_digest_mismatch", lambda f: f["records"]["agent_decisions"][0].__setitem__("action_digest", "sha256:"+"f"*64))
    add("agent_decision_trace_scope_mismatch", lambda f: f["records"]["agent_decisions"][0].__setitem__("run_id", "run:wrong"))
    passed=[]
    for name, fn in tests:
        expect_failure(name, fn); passed.append(name)
    return passed


def main() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    validate_fixture(fixture)
    negatives = run_negative_tests()
    print("PASS: Draft 2020-12 schema is valid")
    print(f"PASS: {sum(len(x) for x in fixture['records'].values())} synthetic records validated across {len(fixture['records'])} record collections")
    print("PASS: trace sequence, SHA-256 hash chain, replay digests and Ed25519 signature verified")
    print("PASS: synthetic-only world-model validation is not misrepresented as external-world validation")
    print(f"PASS: {len(negatives)} negative tests rejected malformed, inconsistent, over-claimed or authority-implying records")
    print("LIMIT: synthetic fixture validation does not establish simulator correctness or real-world fidelity")


if __name__ == "__main__":
    main()
