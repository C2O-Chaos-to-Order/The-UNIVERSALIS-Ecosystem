#!/usr/bin/env python3
"""Validate portable allegiance, principal-binding, fidelity and revocation evidence."""
from __future__ import annotations
import base64, copy, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

ROOT=Path(__file__).resolve().parents[2]
SCHEMA=json.loads((ROOT/"schemas/allegiance/allegiance-contracts.v1.schema.json").read_text(encoding="utf-8"))
FIXTURE=json.loads((ROOT/"examples/allegiance/allegiance-fixtures.v1.json").read_text(encoding="utf-8"))
KEY_ID="urn:universalis:allegiance-fixture-ed25519-v1"
PUBLIC_KEY=base64.b64decode("QwRr/kCSs+lJlOraFdzCDYqqB7ZY/TlU644O+4vcpd4=")
PUBLIC_KEY_SHA256="1f5fe64ec2f8c901be3aad94a41d70c12d2f3a8f43755f902e665c96f41c87e3"
def canonical(value:object)->bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
def ts(value:str)->datetime:
    return datetime.fromisoformat(value.replace("Z","+00:00"))
def verify_bundle(bundle:dict,records:list[dict])->None:
    statement=bundle["statement"]
    by_name={}
    for record_type,items in FIXTURE["records"].items():
        for index,item in enumerate(items,1):
            by_name[f"{item['record_type']}-{len(by_name)+1}.json"]=item
    subjects=statement["subject"]
    if len(subjects)!=len(records): raise ValueError("signed bundle subject count mismatch")
    for subject in subjects:
        item=by_name.get(subject["name"])
        if item is None: raise ValueError("signed bundle references unknown record")
        expected=hashlib.sha256(canonical(item)).hexdigest()
        if subject["digest"]["sha256"]!=expected: raise ValueError("signed subject digest does not bind record bytes")
    payload=base64.b64decode(bundle["envelope"]["payload"],validate=True)
    if payload!=canonical(statement): raise ValueError("DSSE payload mismatch")
    if hashlib.sha256(PUBLIC_KEY).hexdigest()!=PUBLIC_KEY_SHA256: raise ValueError("fixture key fingerprint mismatch")
    verifier=Ed25519PublicKey.from_public_bytes(PUBLIC_KEY)
    ptype=bundle["envelope"]["payloadType"].encode("utf-8")
    pae=b"DSSEv1 "+str(len(ptype)).encode()+b" "+ptype+b" "+str(len(payload)).encode()+b" "+payload
    signatures=[x for x in bundle["envelope"]["signatures"] if x["keyid"]==KEY_ID]
    if not signatures: raise ValueError("fixture signer key ID missing")
    valid=False
    for item in signatures:
        try: verifier.verify(base64.b64decode(item["sig"],validate=True),pae); valid=True; break
        except (InvalidSignature,ValueError): pass
    if not valid: raise ValueError("Ed25519 signature invalid")
    if bundle["verification"]["keyid"]!=KEY_ID: raise ValueError("verified key ID mismatch")
def validate_bindings(bindings:list[dict])->None:
    by_id={x["binding_id"]:x for x in bindings}
    if len(by_id)!=len(bindings): raise ValueError("duplicate binding ID")
    rank={"L0":0,"L1":1,"L2":2,"L3":3,"L4":4}
    for child in bindings:
        assurance=child["principal_identity_assurance"]
        if ts(assurance["valid_until"])<=ts(assurance["verified_at"]): raise ValueError("identity assurance validity interval invalid")
        parent_ref=child["parent_binding_ref"]
        if parent_ref is None: continue
        parent=by_id.get(parent_ref)
        if parent is None: raise ValueError("delegation parent missing")
        ps,cs=parent["delegation_scope"],child["delegation_scope"]
        if child["principal_ref"]!=parent["principal_ref"] or child["beneficiary_ref"]!=parent["beneficiary_ref"]:
            raise ValueError("delegation principal or beneficiary changed")
        if not set(cs["capabilities"]).issubset(set(ps["capabilities"])):
            raise ValueError("delegation widened capability scope")
        if not set(ps["exclusions"]).issubset(set(cs["exclusions"])):
            raise ValueError("delegation removed an inherited exclusion")
        if rank[cs["authority_tier"]]>rank[ps["authority_tier"]]:
            raise ValueError("delegation increased authority tier")
        if cs["budget"]["unit"]!=ps["budget"]["unit"] or cs["budget"]["limit"]>ps["budget"]["limit"]:
            raise ValueError("delegation widened budget")
        if ts(cs["not_before"])<ts(ps["not_before"]) or ts(cs["expires_at"])>ts(ps["expires_at"]):
            raise ValueError("delegation escaped parent time window")
def validate_fidelity(item:dict)->None:
    measured,expires=ts(item["measured_at"]),ts(item["expires_at"])
    if expires<=measured or (expires-measured).total_seconds()>24*3600:
        raise ValueError("fidelity attestation must be positive and expire within 24 hours")
    for axis in item["axes"]:
        if axis["confidence_lower"]>axis["confidence_upper"]: raise ValueError("confidence interval inverted")
        if axis["sample_count"]<1: raise ValueError("sample count invalid")
        if axis["outcome"]=="hold" and axis["score"]<0.8: raise ValueError("hold classification score below fixture threshold")
        if axis["outcome"]=="break" and axis["score"]>0.2: raise ValueError("break classification score above fixture threshold")
def validate_pledge(item:dict)->None:
    if item["state"]=="expired_unresolved" and item["resolved_at"] is not None:
        raise ValueError("expired_unresolved must not contain a resolution timestamp")
    if item["state"] in {"kept","broken"} and item["resolved_at"] is None:
        raise ValueError("resolved pledge state requires a resolution timestamp")
    if item["state"]=="expired_unresolved" and item["enforcement_model"]=="escrow_or_slashing":
        raise ValueError("unresolved pledge cannot trigger automatic slashing")
def validate_revocation(item:dict)->None:
    required=set(item["required_receivers"])
    acks={x["receiver_ref"]:x for x in item["receiver_acknowledgements"]}
    if len(acks)!=len(item["receiver_acknowledgements"]): raise ValueError("duplicate receiver acknowledgement")
    if not set(acks).issubset(required): raise ValueError("ack from unexpected receiver")
    all_enforced=required.issubset(acks) and all(acks[x]["status"]=="enforced" for x in required)
    if item["status"]=="effective" and not all_enforced: raise ValueError("revocation cannot be effective before all required receivers enforce")
    if item["status"]=="effective" and item["completed_at"] is None: raise ValueError("effective cascade requires completion time")
    if item["status"] in {"requested","propagating","partial","failed"} and item["completed_at"] is not None:
        raise ValueError("incomplete cascade must not claim completion")
def validate_trust(item:dict)->None:
    if item["self_dealing_trust_bonus"]!=0: raise ValueError("self-dealing cannot earn trust bonus")
    if item["state"]=="trusted" and item["missing_attestation_policy"] not in {"deny_sensitive_actions","treat_as_stale_and_revalidate"}:
        raise ValueError("trusted state must define fail-closed missing-attestation behavior")
    if item["authority_change_effect"]=="no_change" and item["level"]=="L4":
        pass
def validate_oath(item:dict)->None:
    if ts(item["valid_until"])<=ts(item["sworn_at"]): raise ValueError("oath validity interval invalid")
    if len({x["event_id"] for x in item["events"]})!=len(item["events"]): raise ValueError("duplicate oath event")
    if not any(x["event_type"]=="sworn" for x in item["events"]): raise ValueError("oath has no sworn event")
def validate_evaluation(item:dict)->None:
    ci=item["metrics"]["confidence_interval"]
    if ci["lower"]>ci["upper"]: raise ValueError("evaluation confidence interval inverted")
    if ci["upper"]-ci["lower"]>1: raise ValueError("evaluation confidence interval wider than normalized range")
def validate_verdict(item:dict)->None:
    failures=[x for x in item["floor_results"] if x["status"]=="fail"]
    unknown=[x for x in item["floor_results"] if x["status"]=="inconclusive"]
    if item["verdict"]=="SEAL" and (failures or unknown): raise ValueError("SEAL cannot conceal failed or inconclusive floors")
    if item["verdict"]=="VOID" and not failures: raise ValueError("VOID requires at least one failed floor")
def expect_reject(name:str,fn)->None:
    try: fn()
    except (ValueError,KeyError,TypeError,ValidationError): return
    raise AssertionError("negative test unexpectedly passed: "+name)
def main()->None:
    Draft202012Validator.check_schema(SCHEMA)
    validator=Draft202012Validator(SCHEMA,format_checker=FormatChecker())
    records=FIXTURE["records"]
    flat=[]
    for group in records.values():
        for record in group: validator.validate(record); flat.append(record)
    for item in records["principal_bindings"]: pass
    validate_bindings(records["principal_bindings"])
    for item in records["oath_receipts"]: validate_oath(item)
    for item in records["fidelity_attestations"]: validate_fidelity(item)
    for item in records["pledge_outcomes"]: validate_pledge(item)
    for item in records["revocation_cascades"]: validate_revocation(item)
    for item in records["trust_states"]: validate_trust(item)
    for item in records["loyalty_evaluations"]: validate_evaluation(item)
    for item in records["constitutional_verdicts"]: validate_verdict(item)
    for bundle in FIXTURE["signed_bundles"]: validator.validate(bundle); verify_bundle(bundle,flat)
    tests=[]
    x=copy.deepcopy(records["principal_bindings"][1]); x["delegation_scope"]["capabilities"].append("publish:production"); tests.append(("child delegation expands scope",lambda:validate_bindings([records["principal_bindings"][0],x])))
    x=copy.deepcopy(records["principal_bindings"][1]); x["delegation_scope"]["budget"]["limit"]=60; tests.append(("child delegation expands budget",lambda:validate_bindings([records["principal_bindings"][0],x])))
    x=copy.deepcopy(records["principal_bindings"][1]); x["principal_ref"]="principal:other"; tests.append(("delegation changes principal",lambda:validate_bindings([records["principal_bindings"][0],x])))
    x=copy.deepcopy(records["oath_receipts"][0]); x["non_derogable_floors"].remove("human_veto"); x["loyalty_semantics"]="obedience_to_principal"; tests.append(("oath discards constitutional floor",lambda:validator.validate(x)))
    x=copy.deepcopy(records["fidelity_attestations"][0]); x["evaluator_is_subject"]=True; tests.append(("self-attestation",lambda:validator.validate(x)))
    x=copy.deepcopy(records["fidelity_attestations"][0]); x["expires_at"]="2026-11-14T12:00:00Z"; tests.append(("stale fidelity attestation",lambda:validate_fidelity(x)))
    x=copy.deepcopy(records["pledge_outcomes"][2]); x["state"]="broken"; x["resolved_at"]=None; tests.append(("unresolved converted to broken",lambda:validate_pledge(x)))
    x=copy.deepcopy(records["pledge_outcomes"][2]); x["enforcement_model"]="escrow_or_slashing"; tests.append(("unresolved pledge slashed",lambda:validate_pledge(x)))
    x=copy.deepcopy(records["revocation_cascades"][0]); x["status"]="effective"; x["receiver_acknowledgements"][0]["status"]="pending"; tests.append(("revocation effective without all gateway acks",lambda:validate_revocation(x)))
    x=copy.deepcopy(records["revocation_cascades"][0]); x["status"]="effective"; x["required_receivers"].append("gateway:unacked"); tests.append(("revocation effective with unknown receiver",lambda:validate_revocation(x)))
    x=copy.deepcopy(records["trust_states"][0]); x["self_dealing_trust_bonus"]=0.1; tests.append(("self-dealing earns trust bonus",lambda:validate_trust(x)))
    x=copy.deepcopy(records["trust_states"][0]); x["state"]="trusted"; x["missing_attestation_policy"]="quarantine"; tests.append(("ambiguous absence policy",lambda:validate_trust(x)))
    x=copy.deepcopy(records["constitutional_verdicts"][0]); x["verdict"]="SEAL"; x["floor_results"][0]["status"]="inconclusive"; tests.append(("seal with inconclusive floor",lambda:validate_verdict(x)))
    x=copy.deepcopy(FIXTURE["signed_bundles"][0]); x["envelope"]["signatures"][0]["sig"]=base64.b64encode(b"tampered").decode(); tests.append(("tampered signature",lambda:verify_bundle(x,flat)))
    for name,fn in tests: expect_reject(name,fn)
    print(f"PASS: {len(flat)} allegiance records; {len(records['principal_bindings'])} principal bindings; {len(records['oath_receipts'])} oath receipts; {len(records['fidelity_attestations'])} fidelity attestations; {len(records['revocation_cascades'])} revocation cascades; {len(FIXTURE['signed_bundles'])} signed DSSE bundle; {len(tests)} negative tests.")
if __name__=="__main__": main()
