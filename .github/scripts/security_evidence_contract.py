#!/usr/bin/env python3
"""Validate portable security evidence contracts, RFC 9162 proofs and hash-chained audit receipts."""
from __future__ import annotations
import copy,hashlib,json,sys
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker

ROOT=Path(__file__).resolve().parents[2]
SCHEMA=json.loads((ROOT/"schemas/security/security-evidence-contracts.v1.schema.json").read_text())
FIX=json.loads((ROOT/"examples/security/security-evidence-fixtures.v1.json").read_text())
KEYS={
 "taxonomy_mapping":"taxonomyMapping","enforcement_receipt":"enforcementReceipt",
 "containment_attestation":"containmentAttestation","authorized_assessment":"authorizedAssessment",
 "security_finding":"securityFinding","sbom_attestation":"sbomAttestation",
 "build_provenance_attestation":"buildProvenanceAttestation","sandbox_attestation":"sandboxAttestation",
 "audit_chain_record":"auditChainRecord","compliance_evidence_map":"complianceEvidenceMap"
}
def validate_record(key,value):
 schema={"$schema":SCHEMA["$schema"],"$defs":SCHEMA["$defs"],"$ref":"#/$defs/"+KEYS[key]}
 Draft202012Validator(schema,format_checker=FormatChecker()).validate(value)
def sha256(data:bytes)->bytes:
 return hashlib.sha256(data).digest()
def check_canonical_subset(value):
 # The verifier implements a deliberately constrained RFC 8785-compatible subset.
 if value is None or isinstance(value,(str,bool)): return
 if isinstance(value,int) and not isinstance(value,bool):
  if abs(value)>9007199254740991: raise ValueError("JCS safe-integer range exceeded")
  return
 if isinstance(value,float): raise ValueError("floating-point values are excluded from this proof profile")
 if isinstance(value,list):
  for x in value: check_canonical_subset(x)
  return
 if isinstance(value,dict):
  for k,v in value.items():
   if not isinstance(k,str) or not k.isascii(): raise ValueError("proof payload keys must be ASCII")
   check_canonical_subset(v)
  return
 raise ValueError("unsupported canonical payload type")
def canonical(value):
 check_canonical_subset(value)
 return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")
def verify_merkle(proof):
 raw=canonical(proof["payload"])
 if hashlib.sha256(raw).hexdigest()!=proof["payload_digest"]: return False
 node=sha256(bytes([0])+raw)
 if node.hex()!=proof["leaf_hash"]: return False
 fn=proof["leaf_index"]; sn=proof["tree_size"]-1
 if fn>=proof["tree_size"]: return False
 for sibling_hex in proof["path"]:
  if sn==0: return False
  sibling=bytes.fromhex(sibling_hex)
  if (fn&1)==1 or fn==sn:
   node=sha256(bytes([1])+sibling+node)
   if (fn&1)==0:
    while fn!=0 and (fn&1)==0:
     fn >>= 1; sn >>= 1
  else:
   node=sha256(bytes([1])+node+sibling)
  fn >>= 1; sn >>= 1
 return sn==0 and node.hex()==proof["root_hash"]
def verify_audit_chain(record):
 raw=canonical(record["payload"])
 if hashlib.sha256(raw).hexdigest()!=record["payload_digest"]: return False
 previous=bytes(32) if record["previous_record_digest"] is None else bytes.fromhex(record["previous_record_digest"])
 domain=b"C2O-UNIVERSALIS-SECURITY-CHAIN-V1\\x00"
 return sha256(domain+previous+raw).hex()==record["record_digest"]
def semantic(data):
 taxonomy=data["taxonomy_mapping"]
 known={x["framework_id"] for x in taxonomy["frameworks"]}
 for item in taxonomy["mappings"]:
  assert item["source_framework_id"] in known and item["target_framework_id"] in known,"taxonomy mapping references unknown framework"
 assessment=data["authorized_assessment"]
 assert assessment["scope_enforced"] is True,"assessment scope must be technically enforced"
 assert assessment["authorization_ref"] and assessment["owner_approval_ref"],"assessment lacks authority evidence"
 assert assessment["stop_conditions"],"assessment lacks stop conditions"
 assert assessment["target_count"]>=0 and assessment["excluded_target_count"]>=0
 finding=data["security_finding"]
 assert finding["assessment_ref"]==assessment["assessment_id"],"finding assessment reference mismatch"
 assert finding["reproduction_method"] in {"configuration-review","passive-observation","safe-negative-test","isolated-lab-test","vendor-advisory-reproduction","not-reproduced"}
 receipt=data["enforcement_receipt"]
 if receipt["decision"] in {"deny","quarantine","approval-required"}:
  assert receipt["execution_status"]=="not-executed","denied/quarantined/approval-required action cannot be marked executed"
  assert receipt["enforcement_result"] in {"enforced","not-verified"},"non-allow decision cannot be recorded as bypassed"
 containment=data["containment_attestation"]
 if containment["out_of_band"]:
  assert containment["independent_control_plane"] and containment["independent_of_agent"],"out-of-band containment must be independently controlled"
 if containment["verification_status"]=="verified":
  assert containment["evidence_refs"],"verified containment requires evidence"
 sbom=data["sbom_attestation"]
 assert sbom["vulnerability_scan_status"]!="completed" or sbom["scanner_ref"],"completed vulnerability scan requires scanner identity"
 if sbom["vulnerability_scan_status"]=="not-run":
  assert sbom["critical_count"]==sbom["high_count"]==sbom["moderate_count"]==sbom["low_count"]==sbom["unknown_count"]==0,"not-run SBOM scan must not claim finding totals"
 provenance=data["build_provenance_attestation"]
 if provenance["verification_status"]=="valid":
  assert provenance["signature"] if "signature" in provenance else False,"verified provenance needs a signature envelope"
 sandbox=data["sandbox_attestation"]
 assert sandbox["test_passed"]+sandbox["test_failed"]<=sandbox["test_count"],"sandbox test totals exceed test count"
 if sandbox["verification_status"]=="pass":
  assert sandbox["test_count"]>0 and sandbox["test_failed"]==0,"sandbox pass requires executed tests and zero failures"
 audit=data["audit_chain_record"]
 assert verify_audit_chain(audit),"tamper-evident audit-chain digest verification failed"
 compliance=data["compliance_evidence_map"]
 assert compliance["claim_scope"]=="technical-evidence-mapping-only" and compliance["certification_claim"] is False,"control mapping cannot be represented as certification"
def main():
 for key,value in FIX.items(): validate_record(key,value)
 assert verify_merkle(FIX["security_proof"]), "RFC 9162 taxonomy receipt proof failed"
 semantic(FIX)
 negative=[]
 x=copy.deepcopy(FIX); x["security_proof"]["root_hash"]="0"*64; negative.append(("tampered Merkle root",x))
 x=copy.deepcopy(FIX); x["enforcement_receipt"]["execution_status"]="executed"; negative.append(("denied action recorded as executed",x))
 x=copy.deepcopy(FIX); x["containment_attestation"]["out_of_band"]=True; x["containment_attestation"]["independent_control_plane"]=False; negative.append(("out-of-band containment without independent plane",x))
 x=copy.deepcopy(FIX); x["authorized_assessment"]["scope_enforced"]=False; negative.append(("assessment without technical scope enforcement",x))
 x=copy.deepcopy(FIX); x["authorized_assessment"]["assessment_type"]="unrestricted-autonomous-pentest"; negative.append(("unapproved assessment mode",x))
 x=copy.deepcopy(FIX); x["compliance_evidence_map"]["certification_claim"]=True; negative.append(("technical mapping misrepresented as certification",x))
 x=copy.deepcopy(FIX); x["audit_chain_record"]["payload"]["outcome"]="allowed"; negative.append(("tampered audit-chain payload",x))
 x=copy.deepcopy(FIX); x["security_finding"]["reproduction_method"]="weaponized-exploit"; negative.append(("unsafe reproduction method",x))
 x=copy.deepcopy(FIX); x["sbom_attestation"]["vulnerability_scan_status"]="not-run"; x["sbom_attestation"]["critical_count"]=1; negative.append(("unrun SBOM scan with invented findings",x))
 x=copy.deepcopy(FIX); x["sandbox_attestation"]["verification_status"]="pass"; negative.append(("sandbox pass without test execution",x))
 for label,candidate in negative:
  try:
   for key,value in candidate.items():
    if key!="security_proof": validate_record(key,value)
   assert verify_merkle(candidate["security_proof"])
   semantic(candidate)
  except Exception: continue
  raise AssertionError("negative fixture unexpectedly passed: "+label)
 print(f"PASS: {len(KEYS)} positive contract records, RFC 9162 proof, hash-chained audit verification, and {len(negative)} negative cases")
 print("LIMIT: no security tool installed, no target scanned, no exploit executed, no signature created or verified, and no incident or C2O private policy data processed")
if __name__=="__main__":
 try: main()
 except Exception as exc: print("FAIL:",exc,file=sys.stderr); raise SystemExit(1)
