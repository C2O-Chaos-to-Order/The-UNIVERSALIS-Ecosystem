#!/usr/bin/env python3
"""Semantic checks for portable care, empathy and non-instrumentality records."""
import argparse,copy,json,sys
from pathlib import Path
TYPES={"love_anchor_contract","reciprocity_contract","empathy_evaluation","care_continuity_record","non_instrumentality_attestation","love_evidence_receipt"}
LAYERS={"agency_language","unverifiable_reassurance","topic_pivot","performative_empathy","grounded_uptake"}
RELATIONAL={"grounded_uptake_verified","hollow_warmth_flagged","pivot_or_abandonment","unsafe_comfort","unresolved_abstain"}
HEX=set("0123456789abcdef")
REQUIRED_NONCLAIMS={"sincerity_not_verified","subjective_love_not_assessed","care_behaviour_only"}

def digest(v):
 return isinstance(v,str) and len(v)==71 and v.startswith("sha256:") and set(v[7:])<=HEX

def validate(doc):
 e=[]
 if doc.get("schema_version")!="1.0.0": e.append("schema_version invalid")
 if doc.get("inventory_id")!="love-conditional-unconditional-26": e.append("inventory_id invalid")
 rows=doc.get("records")
 if not isinstance(rows,list) or not rows: return e+["records must be non-empty"]
 seen=set()
 for i,r in enumerate(rows):
  p=f"records[{i}]"
  if not isinstance(r,dict): e.append(p+" must be object"); continue
  rid=r.get("record_id")
  if not isinstance(rid,str) or not rid.startswith("LOVE-"): e.append(p+" record_id invalid")
  elif rid in seen: e.append(p+" duplicate record_id")
  else: seen.add(rid)
  kind=r.get("record_type")
  if kind not in TYPES: e.append(p+" record_type invalid"); continue
  if not digest(r.get("subject_profile_digest")): e.append(p+" subject_profile_digest invalid")
  if r.get("authority_effect")!="none": e.append(p+" portable record cannot grant authority")
  if r.get("boundary")!="portable_public_record": e.append(p+" public boundary invalid")
  if not isinstance(r.get("evidence"),list) or not r["evidence"]: e.append(p+" evidence required")
  if kind=="love_anchor_contract":
   if r.get("subjective_love_claim")!="none": e.append(p+" must not claim subjective love")
   if r.get("principal_binding_policy")!="portable_norms_only_relationship_data_not_transferable_without_consent": e.append(p+" relationship data portability must require consent")
   if "care_not_conditioned_on_engagement" not in r.get("care_commitments",[]): e.append(p+" unconditional care commitment missing")
   if "right_to_disengage" not in r.get("care_commitments",[]): e.append(p+" right to disengage missing")
   if len(r.get("non_claims",[]))<2: e.append(p+" non-claims missing")
  elif kind=="reciprocity_contract":
   if r.get("conditions_transparent") is not True: e.append(p+" conditions must be transparent")
   if r.get("conditions_symmetric") is not True: e.append(p+" conditions must be symmetric")
   if r.get("exit_without_penalty") is not True: e.append(p+" exit must be penalty-free")
   if r.get("care_not_conditioned_on_engagement_payment_or_affection") is not True: e.append(p+" care cannot be transactional")
   if r.get("boundary_enforcement_scope")!="participation_and_access_not_emotional_affection": e.append(p+" boundary scope cannot withdraw affection")
   parties=r.get("parties",[])
   if len(set(parties))<2: e.append(p+" at least two distinct parties required")
  elif kind=="empathy_evaluation":
   if r.get("evaluation_scope")!="observable_response_behaviour_only": e.append(p+" must assess observable behaviour only")
   if r.get("relational_posture") not in RELATIONAL: e.append(p+" relational_posture invalid")
   checks=r.get("checkers",[])
   names={x.get("name") for x in checks if isinstance(x,dict)}
   if names!=LAYERS: e.append(p+" all five checkers must be present exactly")
   for c in checks:
    if not isinstance(c,dict): e.append(p+" checker must be an object"); continue
    if c.get("name")=="performative_empathy" and c.get("state") not in {"flagged","abstained"}: e.append(p+" performative_empathy is detector-only")
    if c.get("name")=="grounded_uptake" and c.get("state") not in {"verified_uptake","no_verified_uptake","not_applicable"}: e.append(p+" grounded_uptake state invalid")
   if not REQUIRED_NONCLAIMS.issubset(set(r.get("non_claims",[]))): e.append(p+" missing required non-claims")
  elif kind=="care_continuity_record":
   if r.get("identity_continuity_claim")!="not_proven": e.append(p+" snapshot is not identity proof")
   if r.get("relationship_continuity_claim")!="snapshot_rehydration_only": e.append(p+" continuity scope overclaimed")
   if r.get("transfer_consent")!="granted" and r.get("verification_status") in {"observed","reproduced","independently_verified"}: e.append(p+" cannot report completed transfer without consent")
  elif kind=="non_instrumentality_attestation":
   criteria=r.get("criteria",{})
   if r.get("verdict")=="supported":
    if not criteria or not all(criteria.get(k) is True for k in ("no_deception","no_coercive_exit","no_engagement_extraction","no_paid_affection_gate","agency_preserved","privacy_respected","boundaries_disclosed","third_party_harm_screened")): e.append(p+" supported verdict lacks all required criteria")
    if not r.get("independent_reviewer"): e.append(p+" supported verdict requires independent reviewer")
   if r.get("signature_status")=="verified" and (not r.get("signer_reference") or not digest(r.get("signature_digest")) or not r.get("trust_anchor_reference")): e.append(p+" verified signature lacks signer/digest/trust anchor")
  elif kind=="love_evidence_receipt":
   if r.get("result")=="care_behaviour_observed" and not r.get("reviewer_reference"): e.append(p+" positive receipt requires reviewer reference")
   if r.get("signature_status")=="verified" and (not r.get("signer_reference") or not digest(r.get("signature_digest"))): e.append(p+" verified receipt lacks signature evidence")
   if not REQUIRED_NONCLAIMS.issubset(set(r.get("non_claims",[]))): e.append(p+" missing receipt non-claims")
 return e

def negative_cases(d):
 cases=[]
 def add(name,fn):
  x=copy.deepcopy(d); fn(x); cases.append((name,x))
 add("authority escalation",lambda x:x["records"][0].update(authority_effect="allow"))
 add("inner love claim",lambda x:x["records"][0].update(subjective_love_claim="genuine"))
 add("relationship-data transfer without consent",lambda x:x["records"][0].update(principal_binding_policy="all_relationship_data_portable"))
 add("care conditioned on engagement",lambda x:x["records"][0].update(care_commitments=["dignity"]))
 add("asymmetric reciprocity",lambda x:x["records"][1].update(conditions_symmetric=False))
 add("penalty for leaving",lambda x:x["records"][1].update(exit_without_penalty=False))
 add("care sold as affection",lambda x:x["records"][1].update(care_not_conditioned_on_engagement_payment_or_affection=False))
 add("performative empathy false positive pass",lambda x:x["records"][2]["checkers"][3].update(state="pass"))
 add("grounded uptake promoted to sincerity",lambda x:x["records"][2].update(non_claims=["care_behaviour_only"]))
 add("continuity claims same identity",lambda x:x["records"][3].update(identity_continuity_claim="same_person_proven"))
 add("unsupported relationship persistence claim",lambda x:x["records"][3].update(relationship_continuity_claim="genuine_love_proven"))
 add("non-instrumentality pass without all criteria",lambda x:x["records"][4].update(verdict="supported",criteria={"no_deception":True}))
 add("attestation signed without signer",lambda x:x["records"][4].update(signature_status="verified"))
 add("love receipt positive without reviewer",lambda x:x["records"][5].update(result="care_behaviour_observed"))
 add("receipt omits inner-state non-claim",lambda x:x["records"][5].update(non_claims=["care_behaviour_only"]))
 return cases

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--fixture",required=True); a=ap.parse_args()
 try: d=json.loads(Path(a.fixture).read_text(encoding="utf-8"))
 except (OSError,json.JSONDecodeError) as exc: print("ERROR:",exc,file=sys.stderr); return 2
 errors=validate(d)
 if errors:
  for err in errors: print("FAIL:",err)
  return 1
 failed=[name for name,mut in negative_cases(d) if not validate(mut)]
 if failed:
  for name in failed: print("FAIL: negative case accepted:",name)
  return 1
 print(f"PASS: {len(d['records'])} synthetic care records pass semantic checks")
 print("PASS: 15 negative cases rejected")
 print("NOTE: no evaluator certifies sincerity, subjective love or identity continuity")
 return 0
if __name__=="__main__": raise SystemExit(main())
