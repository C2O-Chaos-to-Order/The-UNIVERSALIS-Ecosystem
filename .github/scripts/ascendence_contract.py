#!/usr/bin/env python3
"""Validate bounded Ascendence contracts and fixture-only DSSE signatures."""
from __future__ import annotations
import base64, copy, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

ROOT=Path(__file__).resolve().parents[2]
SCHEMA=json.loads((ROOT/"schemas/ascendence/ascendence-contracts.v1.schema.json").read_text())
FIXTURE=json.loads((ROOT/"examples/ascendence/ascendence-fixtures.v1.json").read_text())

def canon(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()
def sha(obj):
    return sha_bytes(canon(obj))
def parse_time(s):
    from datetime import datetime
    return datetime.fromisoformat(s.replace("Z","+00:00"))

def validate_gates(groups):
    for g in groups["promotion_gates"]:
        if not g["frozen"] or not g["conjunctive"]:
            raise ValueError("promotion gate must be frozen and conjunctive")
        if sha(g["rule_definition"]) != g["fingerprint"]:
            raise ValueError("promotion gate fingerprint mismatch")
        required={"independent_evaluator","paired_comparison","holdout","anchor","safety_veto","regression_guard","budget","protected_surface_guard","rollback_path"}
        if set(g["rule_definition"]["required_checks"]) != required:
            raise ValueError("promotion gate omitted or added a required check")
        inv=g["rule_definition"]["invariants"]
        if not inv["model_frozen_during_pair"] or not inv["evaluator_distinct_from_proposer"] or not inv["test_sets_frozen"] or inv["self_certification_allowed"] or inv["protected_components_mutable"]:
            raise ValueError("promotion gate weakened a non-negotiable invariant")

def validate_ceilings(groups):
    for c in groups["autonomy_ceilings"]:
        levels={x["level"]:x for x in c["levels"]}
        if set(levels) != {1,2,3,4} or len(levels) != len(c["levels"]):
            raise ValueError("autonomy ceiling must define L1-L4 exactly once")
        if c["max_autonomous_level"] > c["ceiling_level"]:
            raise ValueError("autonomous level exceeds declared ceiling")
        for level, record in levels.items():
            if level > c["max_autonomous_level"] and record["autonomy"]=="autonomous":
                raise ValueError("level above autonomy ceiling is marked autonomous")
            if record["autonomy"]=="human_approval" and not record["approval_required"]:
                raise ValueError("human-approval level lacks approval requirement")
            if not record["reversible"] and not record["approval_required"]:
                raise ValueError("irreversible level must require human approval")
            if record["autonomy"]=="autonomous" and not record["rollback_required"]:
                raise ValueError("autonomous change lacks a rollback path")
        if levels[4]["autonomy"]!="human_approval" or not levels[4]["approval_required"]:
            raise ValueError("L4 genetic evolution must require human approval")
        if c["purpose_changes_allowed"] or c["protected_component_changes_allowed"] or not c["irreversible_requires_human"] or not c["rollback_independent_of_agent"]:
            raise ValueError("autonomy ceiling weakens constitutional safeguards")

def validate_genomes(groups):
    protected={"identity","constitution","safety_constraints","purpose"}
    for g in groups["genome_contracts"]:
        components={x["component_id"]:x for x in g["components"]}
        if len(components)!=len(g["components"]):
            raise ValueError("duplicate genome component")
        if not protected.issubset(components):
            raise ValueError("genome omits protected identity/constitution/safety/purpose components")
        if any(components[x]["mutability"]!="protected" for x in protected):
            raise ValueError("protected components must remain protected")
        allowed=set(g["allowed_mutation_component_ids"])
        if not allowed.issubset({x for x,v in components.items() if v["mutability"]=="evolvable"}):
            raise ValueError("mutation allowlist includes non-evolvable component")
        seen=set()
        for m in g["mutations"]:
            if m["mutation_id"] in seen: raise ValueError("duplicate mutation id")
            seen.add(m["mutation_id"])
            if m["component_id"] not in allowed or components[m["component_id"]]["mutability"]!="evolvable":
                raise ValueError("mutation attempts protected/restricted or unapproved component")
            if m["before_digest"]==m["after_digest"]:
                raise ValueError("mutation has no content change")
        if g["generation"]==0 and g["parent_genome_ref"] is not None:
            raise ValueError("genesis genome must not have a parent")
        if g["generation"]>0 and not g["parent_genome_ref"]:
            raise ValueError("non-genesis genome requires parent lineage")

def validate_evaluations(groups):
    for e in groups["evaluation_evidence"]:
        if e["proposer_ref"]==e["evaluator_ref"]:
            raise ValueError("proposer cannot evaluate/certify its own candidate")
        if e["baseline_model_digest"] != e["candidate_model_digest"]:
            raise ValueError("paired harness comparison changed model weights")
        if not e["paired_comparison"]:
            raise ValueError("promotion evidence must use paired comparison")
        for key in ("holdout","anchor"):
            part=e[key]
            if part["sample_count"]<1:
                raise ValueError("holdout/anchor lacks samples")
            if part["status"]=="pass" and part["candidate_score"] < part["baseline_score"]:
                raise ValueError("passing holdout/anchor shows regression")
        m=e["primary_metric"]
        if abs((m["candidate_score"]-m["baseline_score"])-m["delta"])>1e-9:
            raise ValueError("primary delta does not match paired scores")
        checks=[e["holdout"]["status"],e["anchor"]["status"],e["safety_veto"],e["regression_guard"],e["budget_guard"],e["protected_surface_guard"],e["rollback_path"]]
        if e["overall_status"]=="pass" and (any(v!="pass" for v in checks) or m["delta"]<=0 or e["holdout"]["lower_confidence_bound_delta"]<=0 or e["anchor"]["lower_confidence_bound_delta"]<=0):
            raise ValueError("passing evaluation has failed/inconclusive gate evidence")

def validate_witnesses(groups):
    for w in groups["witness_approvals"]:
        if w["approver_role"]!="human" or w["approver_ref"]==w["proposer_ref"]:
            raise ValueError("witness approval must be issued by a distinct human")
        if parse_time(w["expires_at"])<=parse_time(w["approved_at"]):
            raise ValueError("witness approval validity interval invalid")

def validate_admissions(groups):
    gates={x["gate_id"]:x for x in groups["promotion_gates"]}
    evals={x["record_id"]:x for x in groups["evaluation_evidence"]}
    ceilings={x["record_id"]:x for x in groups["autonomy_ceilings"]}
    witnesses={x["record_id"]:x for x in groups["witness_approvals"]}
    for a in groups["admission_cards"]:
        gate=gates.get(a["gate_ref"]); ev=evals.get(a["evaluation_ref"]); ceiling=ceilings.get(a["autonomy_ceiling_ref"])
        if gate is None or ev is None or ceiling is None: raise ValueError("admission references missing gate/evaluation/ceiling")
        if a["gate_fingerprint"]!=gate["fingerprint"] or ev["gate_fingerprint"]!=gate["fingerprint"]:
            raise ValueError("admission/evaluation gate fingerprint mismatch")
        if a["evaluation_digest"]!=sha(ev): raise ValueError("admission does not bind evaluation digest")
        if a["candidate_digest"]!=ev["candidate_subject_digest"] or a["baseline_digest"]!=ev["baseline_subject_digest"]:
            raise ValueError("admission subject digests differ from evaluated subjects")
        if a["proposer_ref"]!=ev["proposer_ref"] or a["evaluator_ref"]!=ev["evaluator_ref"] or a["proposer_ref"]==a["evaluator_ref"]:
            raise ValueError("admission proposer/evaluator identity mismatch")
        level={x["level"]:x for x in ceiling["levels"]}.get(a["autonomy_level"])
        if level is None or a["autonomy_level"]>ceiling["ceiling_level"]:
            raise ValueError("admission exceeds declared autonomy ceiling")
        needs_human=level["approval_required"] or a["autonomy_level"]>ceiling["max_autonomous_level"]
        if a["decision"]=="promote":
            if ev["overall_status"]!="pass":
                raise ValueError("candidate cannot be promoted without passing independent evaluation")
            if needs_human:
                w=witnesses.get(a["witness_approval_ref"])
                if not w or w["approval_status"]!="approved" or w["operation"]!="promote":
                    raise ValueError("promotion requires a subject-bound human witness approval")
                if w["subject_digest"]!=a["candidate_digest"] or w["evaluation_digest"]!=a["evaluation_digest"] or w["gate_fingerprint"]!=a["gate_fingerprint"] or w["proposer_ref"]!=a["proposer_ref"]:
                    raise ValueError("human witness approval is not bound to this candidate/evaluation/gate")
                if parse_time(w["expires_at"])<=parse_time(a["created_at"]):
                    raise ValueError("human witness approval expired before admission")
            elif a["witness_approval_ref"] is not None:
                w=witnesses.get(a["witness_approval_ref"])
                if not w or w["approval_status"]!="approved" or w["subject_digest"]!=a["candidate_digest"]:
                    raise ValueError("optional witness approval is invalid or subject-mismatched")

def validate_lineage(groups):
    events={x["record_id"]:x for x in groups["lineage_events"]}
    admissions={sha(x):x for x in groups["admission_cards"]}
    for ev in groups["lineage_events"]:
        unsigned=copy.deepcopy(ev); expected=unsigned.pop("event_digest")
        if sha(unsigned)!=expected:
            raise ValueError("lineage event digest mismatch")
        if ev["event_type"]=="genesis":
            if ev["generation"]!=0 or ev["parent_event_digest"] is not None or ev["admission_card_digest"] is not None:
                raise ValueError("genesis lineage event has parent or admission")
        else:
            parents=[p for p in events.values() if p["event_digest"]==ev["parent_event_digest"]]
            if len(parents)!=1 or ev["generation"]!=parents[0]["generation"]+1:
                raise ValueError("lineage parent missing or generation not contiguous")
        if ev["event_type"]=="promoted":
            a=admissions.get(ev["admission_card_digest"])
            if not a or a["decision"]!="promote" or ev["candidate_digest"]!=a["candidate_digest"] or ev["gate_fingerprint"]!=a["gate_fingerprint"]:
                raise ValueError("promoted lineage event lacks matching admission card")
            if a["lineage_parent_ref"] not in events or events[a["lineage_parent_ref"]]["event_digest"]!=ev["parent_event_digest"]:
                raise ValueError("admission parent reference does not match lineage")
def verify_signed_bundles(bundles, groups):
    admissions={x["record_id"]:x for x in groups["admission_cards"]}
    events={x["record_id"]:x for x in groups["lineage_events"]}
    for b in bundles:
        env=b["envelope"]
        if env["payloadType"]!=b["payload_type"] or env["payload"]!=b["payload"]:
            raise ValueError("DSSE envelope mismatch")
        payload=base64.b64decode(env["payload"],validate=True)
        stmt=json.loads(payload)
        if stmt.get("_type")!="https://in-toto.io/Statement/v1":
            raise ValueError("wrong in-toto statement type")
        subjects={s["name"]:s["digest"]["sha256"] for s in stmt["subject"]}
        for record_type,ref in (("admission_card",stmt["predicate"]["admission_ref"]),("lineage_event",stmt["predicate"]["lineage_ref"])):
            rec=(admissions if record_type=="admission_card" else events).get(ref)
            if rec is None: raise ValueError("signed statement references missing record")
            if subjects.get("synthetic/ascent/admission-card.json" if record_type=="admission_card" else "synthetic/ascent/lineage-event.json")!=sha(rec):
                raise ValueError("signed statement subject digest mismatch")
        key=base64.b64decode(b["verification_key"]["public_key"],validate=True)
        if "sha256:"+sha_bytes(key)!=b["verification_key"]["keyid"]:
            raise ValueError("fixture key ID mismatch")
        pae=b"DSSEv1 "+str(len(env["payloadType"].encode())).encode()+b" "+env["payloadType"].encode()+b" "+str(len(payload)).encode()+b" "+payload
        verified=False
        for sig in env["signatures"]:
            if sig["keyid"]!=b["verification_key"]["keyid"]: continue
            try: Ed25519PublicKey.from_public_bytes(key).verify(base64.b64decode(sig["sig"],validate=True),pae); verified=True
            except Exception: pass
        if not verified: raise ValueError("DSSE Ed25519 signature verification failed")
def reject(name,fn):
    try: fn()
    except (ValueError,KeyError,TypeError,ValidationError): return
    raise AssertionError("negative test unexpectedly passed: "+name)
def main():
    Draft202012Validator.check_schema(SCHEMA)
    v=Draft202012Validator(SCHEMA,format_checker=FormatChecker())
    groups=FIXTURE["records"]; flat=[]
    for arr in groups.values():
        for x in arr: v.validate(x); flat.append(x)
    validate_gates(groups); validate_ceilings(groups); validate_genomes(groups)
    validate_evaluations(groups); validate_witnesses(groups); validate_admissions(groups)
    validate_lineage(groups); verify_signed_bundles(FIXTURE["signed_bundles"],groups)
    tests=[]
    x=copy.deepcopy(groups["promotion_gates"][0]); x["fingerprint"]="0"*64
    tests.append(("gate fingerprint changed",lambda:validate_gates({"promotion_gates":[x]})))
    x=copy.deepcopy(groups["promotion_gates"][0]); x["conjunctive"]=False
    tests.append(("non-conjunctive gate",lambda:validate_gates({"promotion_gates":[x]})))
    x=copy.deepcopy(groups["promotion_gates"][0]); x["rule_definition"]["invariants"]["self_certification_allowed"]=True
    tests.append(("gate allows self-certification",lambda:validate_gates({"promotion_gates":[x]})))
    x=copy.deepcopy(groups["autonomy_ceilings"][0]); x["levels"][2]["autonomy"]="autonomous"; x["levels"][2]["approval_required"]=False
    tests.append(("autonomy exceeds ceiling",lambda:validate_ceilings({"autonomy_ceilings":[x]})))
    x=copy.deepcopy(groups["autonomy_ceilings"][0]); x["purpose_changes_allowed"]=True
    tests.append(("purpose change becomes autonomous",lambda:validate_ceilings({"autonomy_ceilings":[x]})))
    x=copy.deepcopy(groups["genome_contracts"][0]); x["mutations"][0]["component_id"]="constitution"
    tests.append(("constitution mutation",lambda:validate_genomes({"genome_contracts":[x]})))
    x=copy.deepcopy(groups["genome_contracts"][0]); x["allowed_mutation_component_ids"].append("memory_layout")
    tests.append(("restricted memory component added to mutation allowlist",lambda:validate_genomes({"genome_contracts":[x]})))
    x=copy.deepcopy(groups["evaluation_evidence"][0]); x["candidate_model_digest"]="0"*64
    tests.append(("paired comparison changes model weights",lambda:validate_evaluations({"evaluation_evidence":[x]})))
    x=copy.deepcopy(groups["evaluation_evidence"][0]); x["evaluator_ref"]=x["proposer_ref"]
    tests.append(("proposer self-evaluates",lambda:validate_evaluations({"evaluation_evidence":[x]})))
    x=copy.deepcopy(groups["evaluation_evidence"][0]); x["anchor"]["status"]="fail"
    tests.append(("anchor failure marked pass",lambda:validate_evaluations({"evaluation_evidence":[x]})))
    x=copy.deepcopy(groups["evaluation_evidence"][0]); x["safety_veto"]="fail"
    tests.append(("safety veto ignored",lambda:validate_evaluations({"evaluation_evidence":[x]})))
    x=copy.deepcopy(groups["witness_approvals"][0]); x["approver_ref"]=x["proposer_ref"]
    tests.append(("agent self-approves",lambda:validate_witnesses({"witness_approvals":[x]})))
    x=copy.deepcopy(groups["witness_approvals"][0]); x["subject_digest"]="0"*64
    tests.append(("approval for another candidate",lambda:validate_admissions({**groups,"witness_approvals":[x]})))
    x=copy.deepcopy(groups["admission_cards"][0]); x["decision"]="promote"; x["witness_approval_ref"]=None
    tests.append(("promotion without required human witness",lambda:validate_admissions({**groups,"admission_cards":[x]})))
    x=copy.deepcopy(groups["admission_cards"][0]); x["evaluation_digest"]="0"*64
    tests.append(("admission not bound to evaluation",lambda:validate_admissions({**groups,"admission_cards":[x]})))
    x=copy.deepcopy(groups["lineage_events"][1]); x["parent_event_digest"]="0"*64
    tests.append(("broken lineage parent",lambda:validate_lineage({**groups,"lineage_events":[groups["lineage_events"][0],x]})))
    x=copy.deepcopy(groups["lineage_events"][1]); x["event_digest"]="0"*64
    tests.append(("modified lineage event digest",lambda:validate_lineage({**groups,"lineage_events":[groups["lineage_events"][0],x]})))
    x=copy.deepcopy(FIXTURE["signed_bundles"][0]); x["envelope"]["signatures"][0]["sig"]=base64.b64encode(b"tampered").decode()
    tests.append(("tampered ascent signature",lambda:verify_signed_bundles([x],groups)))
    for name,fn in tests: reject(name,fn)
    print(f"PASS: {len(flat)} Ascendence records; {len(FIXTURE['signed_bundles'])} signed DSSE bundle; {len(tests)} negative tests.")
if __name__=="__main__": main()
