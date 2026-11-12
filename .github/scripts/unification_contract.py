#!/usr/bin/env python3
"""Semantic checks for authority-neutral agent/OS/AI unification records."""
import argparse,copy,json,sys
from pathlib import Path
LAYERS={"runtime_substrate","orchestration_composition","model_gateway","local_execution","sovereign_mesh","cross_layer_contract"}
KINDS={"candidate","contract","unresolved"}
CLAIMS={"source_documented","source_claim_only","independently_verified","proposed","unresolved","not_tested"}
ROLES={"container_artifact","tool_client_server","agent_agent","client_agent","framework_adapter","inference_api","product_command_surface","governance_envelope","computer_use_aci","assimilation_profile"}
CLASSES={"formal_standard","specification","product_interface","api_compatibility","research_proposal","format"}
PRODUCT_INTERFACES={"Universal Command Protocol","GovernanceEnvelope","Shinken ACI","Agno AgentProtocol"}
def validate(d):
 e=[]
 if d.get("schema_version")!="1.0.0": e.append("invalid schema version")
 if d.get("inventory_id")!="agent-os-ai-unification-24": e.append("invalid inventory id")
 rs=d.get("records")
 if not isinstance(rs,list) or not rs: return e+["records must be non-empty"]
 seen=set()
 for i,r in enumerate(rs):
  p=f"records[{i}]"
  if not isinstance(r,dict): e.append(p+" must be object"); continue
  for k in ("record_id","kind","layer","name","license_status","maturity","claim_status","scope","interfaces","limitations","authority_effect","boundary"):
   if k not in r: e.append(p+" missing "+k)
  rid=r.get("record_id")
  if not isinstance(rid,str) or not rid.startswith("UNIF-"): e.append(p+" bad record id")
  elif rid in seen: e.append(p+" duplicate record id")
  else: seen.add(rid)
  if r.get("kind") not in KINDS: e.append(p+" bad kind")
  if r.get("layer") not in LAYERS: e.append(p+" bad layer")
  if r.get("claim_status") not in CLAIMS: e.append(p+" bad claim status")
  if r.get("authority_effect")!="none": e.append(p+" authority effect must be none")
  if r.get("boundary")!="portable_public_record": e.append(p+" bad public boundary")
  if not isinstance(r.get("limitations"),list) or not r.get("limitations"): e.append(p+" limitations required")
  its=r.get("interfaces")
  if not isinstance(its,list): e.append(p+" interfaces must be array"); continue
  for j,x in enumerate(its):
   q=f"{p}.interfaces[{j}]"
   if not isinstance(x,dict): e.append(q+" must be object"); continue
   if x.get("role") not in ROLES: e.append(q+" bad role")
   if x.get("classification") not in CLASSES: e.append(q+" bad classification")
   if x.get("status") not in {"published","beta","alpha","proposed","unresolved","not_tested"}: e.append(q+" bad status")
   if not isinstance(x.get("scope"),str) or not x.get("scope"): e.append(q+" missing scope")
   if x.get("name")=="MCP" and x.get("role")=="agent_agent": e.append(q+" MCP is not A2A")
   if x.get("name")=="A2A" and x.get("role")=="tool_client_server": e.append(q+" A2A is not MCP")
   if x.get("name") in PRODUCT_INTERFACES and x.get("classification")=="formal_standard": e.append(q+" product-specific interface cannot be labelled a formal standard")
  if r.get("claim_status")=="independently_verified":
   ev=r.get("evidence",[])
   if not any(isinstance(x,dict) and x.get("type") in {"independent_test","compatibility_test","security_review"} for x in ev): e.append(p+" independent status lacks independent evidence")
 return e
def negatives(d):
 muts=[
 ("authority escalation",lambda x:x["records"][0].update(authority_effect="allow")),
 ("duplicate identifier",lambda x:x["records"][1].update(record_id=x["records"][0]["record_id"])),
 ("private boundary",lambda x:x["records"][0].update(boundary="private_c2o")),
 ("missing limitations",lambda x:x["records"][0].update(limitations=[])),
 ("unsupported layer",lambda x:x["records"][0].update(layer="universal_kernel")),
 ("unsupported kind",lambda x:x["records"][0].update(kind="deployed")),
 ("unsupported claim",lambda x:x["records"][0].update(claim_status="trusted")),
 ("unsubstantiated independent status",lambda x:x["records"][0].update(claim_status="independently_verified",evidence=[])),
 ("MCP misclassified",lambda x:x["records"][0]["interfaces"][0].update(name="MCP",role="agent_agent")),
 ("A2A misclassified",lambda x:x["records"][0]["interfaces"][1].update(name="A2A",role="tool_client_server")),
 ("product interface labelled standard",lambda x:x["records"][0]["interfaces"][2].update(name="Universal Command Protocol",classification="formal_standard")),
 ("empty interface scope",lambda x:x["records"][0]["interfaces"][0].update(scope=""))
 ]
 out=[]
 for label,fn in muts:
  x=copy.deepcopy(d); fn(x); out.append((label,x))
 return out
def main():
 p=argparse.ArgumentParser(); p.add_argument("--fixture",required=True); a=p.parse_args()
 try: d=json.loads(Path(a.fixture).read_text(encoding="utf-8"))
 except (OSError,json.JSONDecodeError) as exc: print("ERROR:",exc,file=sys.stderr); return 2
 errors=validate(d)
 if errors:
  for err in errors: print("FAIL:",err)
  return 1
 failed=[name for name,mut in negatives(d) if not validate(mut)]
 if failed:
  for name in failed: print("FAIL: negative case accepted:",name)
  return 1
 print(f"PASS: {len(d['records'])} synthetic records pass authored semantic checks")
 print("PASS: 12 negative cases rejected")
 print("NOTE: no product integration, interoperability, security or authority is proven")
 return 0
if __name__=="__main__": raise SystemExit(main())
