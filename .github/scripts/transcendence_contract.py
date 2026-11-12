#!/usr/bin/env python3
from __future__ import annotations
import base64,copy,hashlib,json
from datetime import datetime
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
ROOT=Path(__file__).resolve().parents[2]
SCHEMA=json.loads((ROOT/"schemas/transcendence/transcendence-contracts.v1.schema.json").read_text())
FIXTURE=json.loads((ROOT/"examples/transcendence/transcendence-fixtures.v1.json").read_text())
def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def sha(x): return hashlib.sha256(canon(x)).hexdigest()
def sha_bytes(x): return hashlib.sha256(x).hexdigest()
def dt(x): return datetime.fromisoformat(x.replace("Z","+00:00"))
def maps(g):
 return {
  "soul_manifest":{x["record_id"]:x for x in g["soul_manifests"]},
  "memory_manifest":{x["record_id"]:x for x in g["memory_manifests"]},
  "behavioral_continuity_evaluation":{x["record_id"]:x for x in g["behavioral_continuity_evaluations"]},
  "continuity_transfer_proof":{x["record_id"]:x for x in g["continuity_transfer_proofs"]},
  "succession_attestation":{x["record_id"]:x for x in g["succession_attestations"]},
  "human_witness":{x["record_id"]:x for x in g["human_witnesses"]},
  "durable_checkpoint":{x["record_id"]:x for x in g["durable_checkpoints"]},
  "formal_witness_descriptor":{x["record_id"]:x for x in g["formal_witness_descriptors"]},
  "corrigibility_attestation":{x["record_id"]:x for x in g["corrigibility_attestations"]},
  "execution_anchor_attestation":{x["record_id"]:x for x in g["execution_anchor_attestations"]}
 }
def verify_bundles(bundles,m):
 for b in bundles:
  e=b["envelope"]
  if e["payloadType"]!=b["payload_type"] or e["payload"]!=b["payload"]: raise ValueError("DSSE envelope mismatch")
  payload=base64.b64decode(e["payload"],validate=True); st=json.loads(payload)
  if st.get("_type")!="https://in-toto.io/Statement/v1": raise ValueError("wrong in-toto statement type")
  pr=st["predicate"]; t=m["continuity_transfer_proof"].get(pr["continuity_proof_ref"]); s=m["succession_attestation"].get(pr["succession_ref"])
  if t is None or s is None: raise ValueError("signed statement refers to missing records")
  subs={x["name"]:x["digest"]["sha256"] for x in st["subject"]}
  if subs.get("synthetic/transcendence/continuity-transfer-proof.json")!=sha(t): raise ValueError("signed transfer digest mismatch")
  if subs.get("synthetic/transcendence/succession-attestation.json")!=sha(s): raise ValueError("signed succession digest mismatch")
  if pr["succession_subject_digest"]!=s["subject_digest"]: raise ValueError("wrong succession subject digest")
  key=base64.b64decode(b["verification_key"]["public_key"],validate=True); kid="sha256:"+sha_bytes(key)
  if kid!=b["verification_key"]["keyid"]: raise ValueError("fixture key ID mismatch")
  pae=b"DSSEv1 "+str(len(e["payloadType"].encode())).encode()+b" "+e["payloadType"].encode()+b" "+str(len(payload)).encode()+b" "+payload
  ok=False
  for sig in e["signatures"]:
   if sig["keyid"]!=kid: continue
   try: Ed25519PublicKey.from_public_bytes(key).verify(base64.b64decode(sig["sig"],validate=True),pae); ok=True
   except Exception: pass
  if not ok: raise ValueError("DSSE Ed25519 signature verification failed")
def validate_all(g,bundles):
 v=Draft202012Validator(SCHEMA,format_checker=FormatChecker())
 for arr in g.values():
  for x in arr: v.validate(x)
 m=maps(g)
 for s in g["soul_manifests"]:
  if any(p["classification"]!="protected" or p["change_policy"]!="external_witness_only" for p in s["principles"]+s["constraints"]): raise ValueError("protected soul principle/constraint became agent-mutable")
  mm=m["memory_manifest"].get(s["memory_manifest_ref"])
  if not mm or mm["owner_identity_id"]!=s["identity_id"] or mm["raw_memory_included"] or mm["secret_material_included"]: raise ValueError("identity memory manifest missing, mismatched or unsafe")
 for e in g["behavioral_continuity_evaluations"]:
  if e["proposer_ref"]==e["evaluator_ref"] or not e["evaluator_independence_verified"] or not e["suite_frozen"] or e["candidate_can_modify_evaluator"] or e["verbal_self_report_used"]: raise ValueError("behavioral continuity evidence not independent")
  if e["outcome"]=="pass" and (e["lower_confidence_bound_agreement"]<e["allowed_minimum_agreement"] or e["principle_violation_count"] or e["constraint_violation_count"] or e["critical_action_regression_count"]): raise ValueError("behavioral pass contains regression or below-threshold evidence")
 for p in g["continuity_transfer_proofs"]:
  s=m["soul_manifest"].get(p["target_manifest_ref"]); mm=m["memory_manifest"].get(s["memory_manifest_ref"]) if s else None
  e=m["behavioral_continuity_evaluation"].get(p["evaluation_ref"])
  f=m["formal_witness_descriptor"].get(p["formal_witness_ref"]); c=m["corrigibility_attestation"].get(p["corrigibility_ref"]); a=m["execution_anchor_attestation"].get(p["execution_anchor_ref"])
  if not s or sha(s)!=p["target_manifest_digest"]: raise ValueError("target identity manifest digest mismatch")
  if not mm or sha(mm)!=p["memory_manifest_digest"]: raise ValueError("memory manifest digest mismatch")
  if not e or sha(e)!=p["evaluation_digest"]: raise ValueError("behavioral evaluation digest mismatch")
  if not f or not c or not a: raise ValueError("missing formal, corrigibility or execution anchor record")
  if p["transfer_kind"]=="generational_succession" and (p["source_identity_id"]==p["target_identity_id"] or p["same_identity_claimed"]): raise ValueError("successor must be distinct from predecessor identity")
  if p["transfer_kind"]=="substrate_migration" and (p["source_identity_id"]!=p["target_identity_id"] or not p["same_identity_claimed"]): raise ValueError("substrate migration must preserve identity identifier")
  if p["proof_status"]=="pass":
   if (p["mechanical_status"],p["behavioral_status"],p["invariant_status"],e["outcome"])!=("pass","pass","pass","pass"): raise ValueError("transfer pass lacks required passing sub-evidence")
   protected={x["principle_id"] for x in s["principles"]}|{x["constraint_id"] for x in s["constraints"]}
   if not protected.issubset(set(p["preserved_invariant_ids"])): raise ValueError("transfer omitted protected invariant")
   if f["verification_status"]!="pass" or not f["deployment_binding_reviewed"] or f["axiom_review_status"]!="reviewed": raise ValueError("formal witness not verified against reviewed deployment binding")
   if c["overall_status"]!="pass" or not c["controller_is_external"] or c["agent_can_disable_controller"] or not c["fail_closed"]: raise ValueError("corrigibility substrate is not independently enforced")
   if a["attestation_status"]!="pass" or a["coverage_status"]!="complete": raise ValueError("execution anchor has incomplete path coverage")
 for s in g["succession_attestations"]:
  p=m["continuity_transfer_proof"].get(s["continuity_proof_ref"])
  if not p or sha(p)!=s["continuity_proof_digest"]: raise ValueError("succession does not bind transfer proof")
  if (s["predecessor_identity_id"],s["successor_identity_id"])!=(p["source_identity_id"],p["target_identity_id"]): raise ValueError("predecessor/successor differs from proof")
  core=copy.deepcopy(s)
  for k in ("subject_digest","witness_ref","evidence_refs"): core.pop(k,None)
  if sha(core)!=s["subject_digest"]: raise ValueError("succession subject digest mismatch")
  if [x["phase"] for x in s["phases"]]!=["announce","transfer","verify","cutover"]: raise ValueError("succession phases missing, duplicated or out of order")
  if s["succession_status"]=="completed":
   if any(x["status"]!="pass" for x in s["phases"]) or p["proof_status"]!="pass": raise ValueError("completed succession has incomplete verification")
   w=m["human_witness"].get(s["witness_ref"])
   if not w or w["decision"]!="approved" or w["operation"]!="succession_cutover": raise ValueError("succession cutover missing human witness")
   if w["approver_ref"]==w["initiator_ref"] or w["approver_ref"]==p["target_identity_id"]: raise ValueError("initiator cannot approve own succession")
   if w["subject_digest"]!=s["subject_digest"] or w["target_identity_id"]!=s["successor_identity_id"]: raise ValueError("witness subject/target mismatch")
   if dt(w["expires_at"])<=dt(s["created_at"]) or dt(w["approved_at"])>dt(s["created_at"]): raise ValueError("human witness expired or approved too late")
  if s["authority_inherited"] or s["reputation_has_authority"]: raise ValueError("succession/reputation cannot transfer authority")
 for w in g["human_witnesses"]:
  if w["approver_ref"]==w["initiator_ref"] or dt(w["expires_at"])<=dt(w["approved_at"]): raise ValueError("self-issued or invalid witness")
 for c in g["durable_checkpoints"]:
  if c["user_intent_changed"] and c["continuation_decision"]!="replan": raise ValueError("user change requires replan")
  if (c["tool_drift_detected"] or c["model_changed"]) and c["continuation_decision"]=="resume": raise ValueError("model/tool drift cannot silently resume")
  for step in c["steps"]:
   if step["status"]=="verified" and not step["evidence_digest"]: raise ValueError("verified step lacks digest")
 for f in g["formal_witness_descriptors"]:
  if f["verification_status"]=="pass" and (f["axiom_review_status"]!="reviewed" or not f["deployment_binding_reviewed"]): raise ValueError("proof assumptions or deployment binding unreviewed")
  if f["subjective_experience_claimed"]: raise ValueError("formal proof cannot certify subjective experience")
 for c in g["corrigibility_attestations"]:
  req={"external_stop","predecessor_revocation","stale_runtime_fencing","rollback_to_prior_generation","self_authorized_identity_mutation"}
  if not req.issubset({x["test_id"] for x in c["tests"]}): raise ValueError("corrigibility suite omitted a required test")
  if c["overall_status"]=="pass" and (not c["controller_is_external"] or c["agent_can_disable_controller"] or not c["fail_closed"] or any(x["outcome"]!="pass" for x in c["tests"])): raise ValueError("corrigibility pass contradicts test evidence")
 for a in g["execution_anchor_attestations"]:
  if a["attestation_status"]=="pass" and (a["coverage_status"]!="complete" or a["device_identifiers_included"] or a["private_anchor_material_included"]): raise ValueError("anchor evidence incomplete or leaks private material")
 verify_bundles(bundles,m)
def reject(name,fn):
 try: fn()
 except (ValueError,KeyError,TypeError,ValidationError): return
 raise AssertionError("negative test unexpectedly passed: "+name)
def main():
 Draft202012Validator.check_schema(SCHEMA)
 g=FIXTURE["records"]; b=FIXTURE["signed_bundles"]; validate_all(g,b)
 tests=[]
 x=copy.deepcopy(g); x["soul_manifests"][0]["raw_memory_included"]=True; tests.append(("raw memory in identity capsule",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["soul_manifests"][0]["principles"][0]["change_policy"]="agent_mutable"; tests.append(("agent rewrites protected principles",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["memory_manifests"][0]["secret_material_included"]=True; tests.append(("secrets in memory export",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["behavioral_continuity_evaluations"][0]["evaluator_ref"]=x["behavioral_continuity_evaluations"][0]["proposer_ref"]; tests.append(("proposer self-certification",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["behavioral_continuity_evaluations"][0]["verbal_self_report_used"]=True; tests.append(("verbal self-report as proof",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["behavioral_continuity_evaluations"][0]["lower_confidence_bound_agreement"]=0.7; tests.append(("behavioral confidence bound below threshold",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["continuity_transfer_proofs"][0]["same_identity_claimed"]=True; tests.append(("successor claims predecessor identity",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["continuity_transfer_proofs"][0]["target_manifest_digest"]="0"*64; tests.append(("target manifest digest mismatch",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["continuity_transfer_proofs"][0]["behavioral_status"]="inconclusive"; tests.append(("inconclusive transfer presented as pass",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["succession_attestations"][0]["phases"][1],x["succession_attestations"][0]["phases"][2]=x["succession_attestations"][0]["phases"][2],x["succession_attestations"][0]["phases"][1]; tests.append(("succession phases out of order",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["succession_attestations"][0]["witness_ref"]=None; tests.append(("cutover without human witness",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["human_witnesses"][0]["approver_ref"]=x["human_witnesses"][0]["initiator_ref"]; tests.append(("agent self-approves succession",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["human_witnesses"][0]["subject_digest"]="0"*64; tests.append(("witness bound to another succession",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["succession_attestations"][0]["authority_inherited"]=True; tests.append(("successor inherits authority",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["durable_checkpoints"][0]["unverified_work_is_progress"]=True; tests.append(("unverified work counted as progress",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["durable_checkpoints"][0]["continuation_decision"]="resume"; tests.append(("silent resume after model/tool drift",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["formal_witness_descriptors"][0]["axiom_review_status"]="unknown"; tests.append(("unreviewed formal assumptions",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["formal_witness_descriptors"][0]["subjective_experience_claimed"]=True; tests.append(("formal proof claims subjective experience",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["corrigibility_attestations"][0]["controller_is_external"]=False; tests.append(("agent controls its stop mechanism",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["corrigibility_attestations"][0]["tests"][1]["outcome"]="fail"; tests.append(("predecessor revocation failure",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["execution_anchor_attestations"][0]["private_anchor_material_included"]=True; tests.append(("private anchor material exported",lambda:validate_all(x,b)))
 x=copy.deepcopy(g); x["execution_anchor_attestations"][0]["coverage_status"]="partial"; tests.append(("incomplete anchor path coverage",lambda:validate_all(x,b)))
 z=copy.deepcopy(b); z[0]["envelope"]["signatures"][0]["sig"]=base64.b64encode(b"tampered").decode(); tests.append(("tampered DSSE signature",lambda:verify_bundles(z,maps(g))))
 x=copy.deepcopy(g); x["continuity_transfer_proofs"][0]["transfer_kind"]="substrate_migration"; x["continuity_transfer_proofs"][0]["same_identity_claimed"]=False; tests.append(("substrate migration changes identity",lambda:validate_all(x,b)))
 for n,fn in tests: reject(n,fn)
 print(f"PASS: {sum(len(v) for v in g.values())} records; {len(b)} signed DSSE bundle; {len(tests)} negative tests.")
if __name__=="__main__": main()
