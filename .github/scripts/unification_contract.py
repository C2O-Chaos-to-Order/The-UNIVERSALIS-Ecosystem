#!/usr/bin/env python3
"""Validate the public, authority-neutral agent/OS/AI unification fixture."""
from __future__ import annotations
import argparse
import copy
import json
import sys
from pathlib import Path

LAYERS = {"runtime_substrate","orchestration_composition","model_gateway","local_execution","sovereign_mesh","cross_layer_contract"}
KINDS = {"candidate","contract","unresolved"}
CLAIMS = {"source_documented","source_claim_only","independently_verified","proposed","unresolved","not_tested"}
ROLES = {"container_artifact","tool_client_server","agent_agent","client_agent","framework_adapter","inference_api","product_command_surface","governance_envelope","computer_use_aci","assimilation_profile"}
CLASSES = {"formal_standard","specification","product_interface","api_compatibility","research_proposal","format"}

def validate(doc):
    errors=[]
    if doc.get("schema_version")!="1.0.0": errors.append("invalid schema_version")
    if doc.get("inventory_id")!="agent-os-ai-unification-24": errors.append("invalid inventory_id")
    records=doc.get("records")
    if not isinstance(records,list) or not records:
        return errors+["records must be a non-empty array"]
    seen=set()
    for i,r in enumerate(records):
        p=f"records[{i}]"
        if not isinstance(r,dict):
            errors.append(p+" must be object")
            continue
        for k in ("record_id","kind","layer","name","source_url","license_status","maturity","claim_status","scope","interfaces","limitations","authority_effect","boundary"):
            if k not in r: errors.append(f"{p}.{k} missing")
        rid=r.get("record_id")
        if not isinstance(rid,str) or not rid.startswith("UNIF-"): errors.append(f"{p}.record_id invalid")
        elif rid in seen: errors.append(f"{p}.record_id duplicated")
        else: seen.add(rid)
        if r.get("kind") not in KINDS: errors.append(f"{p}.kind invalid")
        if r.get("layer") not in LAYERS: errors.append(f"{p}.layer invalid")
        if r.get("claim_status") not in CLAIMS: errors.append(f"{p}.claim_status invalid")
        if r.get("authority_effect")!="none": errors.append(f"{p}.authority_effect must be none")
        if r.get("boundary")!="portable_public_record": errors.append(f"{p}.boundary is not public-portable")
        if not isinstance(r.get("limitations"),list) or not r.get("limitations"): errors.append(f"{p}.limitations required")
        if not isinstance(r.get("source_url"),(str,type(None))): errors.append(f"{p}.source_url must be string or null")
        if not isinstance(r.get("interfaces"),list): errors.append(f"{p}.interfaces must be array")
        else:
            for j,x in enumerate(r["interfaces"]):
                q=f"{p}.interfaces[{j}]"
                if not isinstance(x,dict):
                    errors.append(q+" must be object")
                    continue
                if x.get("role") not in ROLES: errors.append(q+".role invalid")
                if x.get("classification") not in CLASSES: errors.append(q+".classification invalid")
                if x.get("status") not in {"published","beta","alpha","proposed","unresolved","not_tested"}: errors.append(q+".status invalid")
                if not isinstance(x.get("scope"),str) or not x.get("scope"): errors.append(q+".scope required")
                if x.get("name")=="MCP" and x.get("role")=="agent_agent": errors.append(q+": MCP cannot be classified as A2A")
                if x.get("name")=="A2A" and x.get("role")=="tool_client_server": errors.append(q+": A2A cannot be classified as MCP")
        if r.get("claim_status")=="independently_verified":
            evidence=r.get("evidence",[])
            if not any(isinstance(e,dict) and e.get("type") in {"independent_test","compatibility_test","security_review"} for e in evidence):
                errors.append(p+": independent verification needs independent evidence")
    return errors

def negative_cases(doc):
    cases=[]
    def changed(label, mutator):
        d=copy.deepcopy(doc); mutator(d); cases.append((label,d))
    changed("authority grant",lambda d:d["records"][0].update(authority_effect="allow"))
    changed("duplicate identifier",lambda d:d["records"][1].update(record_id=d["records"][0]["record_id"]))
    changed("private data boundary",lambda d:d["records"][0].update(boundary="private_c2o"))
    changed("missing limitation",lambda d:d["records"][0].update(limitations=[]))
    changed("unsupported layer",lambda d:d["records"][0].update(layer="universal_kernel"))
    changed("unsupported kind",lambda d:d["records"][0].update(kind="deployed"))
    changed("unsupported claim",lambda d:d["records"][0].update(claim_status="trusted"))
    changed("unsubstantiated verification",lambda d:(d["records"][0].update(claim_status="independently_verified",evidence=[])))
    changed("MCP assigned agent-agent role",lambda d:d["records"][0]["interfaces"][0].update(name="MCP",role="agent_agent"))
    changed("A2A assigned tool-server role",lambda d:d["records"][0]["interfaces"][1].update(name="A2A",role="tool_client_server"))
    changed("product envelope called standard",lambda d:d["records"][0]["interfaces"][2].update(name="GovernanceEnvelope",classification="formal_standard"))
    changed("invalid schema version",lambda d:d.update(schema_version="0.9.0"))
    return cases

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--fixture",required=True,type=Path)
    args=ap.parse_args()
    try: doc=json.loads(args.fixture.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e:
        print(f"ERROR: {e}",file=sys.stderr); return 2
    errors=validate(doc)
    if errors:
        for e in errors: print("FAIL:",e)
        return 1
    failed=[]
    for name,mutated in negative_cases(doc):
        if not validate(mutated): failed.append(name)
    if failed:
        for name in failed: print("FAIL: negative mutation accepted:",name)
        return 1
    print(f"PASS: {len(doc['records'])} synthetic public records pass semantic validation")
    print("PASS: 12 negative semantic cases rejected")
    print("NOTE: no product interoperability, security, installation or authority is proven")
    return 0
if __name__=="__main__": raise SystemExit(main())
