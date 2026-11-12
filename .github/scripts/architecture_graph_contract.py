#!/usr/bin/env python3
"""Dependency-free semantic checks for portable architecture/dependency graph snapshots."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from datetime import datetime

FIXTURE=Path("examples/architecture/architecture-graph.json")
FORBIDDEN={"password","token","access_token","api_key","secret_value","credential_value","private_key","authorization_header"}

def timestamp(value,label):
    if not isinstance(value,str): raise ValueError(f"{label} must be an ISO-8601 timestamp")
    try: parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc: raise ValueError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None: raise ValueError(f"{label} must include a timezone")
    return parsed

def validate(graph,profile):
    if graph.get("schema_version")!="1.0.0": raise ValueError("unsupported architecture graph version")
    timestamp(graph["captured_at"],"captured_at")
    scope=graph["scope"]
    if profile=="universalis" and scope["visibility"]=="private": raise ValueError("public UNIVERSALIS graph cannot be labelled private")
    node_ids=[node["node_id"] for node in graph["nodes"]]
    if len(node_ids)!=len(set(node_ids)): raise ValueError("duplicate node_id")
    node_set=set(node_ids)
    for node in graph["nodes"]:
        if not node.get("source_refs"): raise ValueError("every node requires provenance source references")
        if profile=="universalis":
            if node["visibility"] in {"confidential","secret"}: raise ValueError("UNIVERSALIS public graph cannot contain confidential/secret nodes")
            if node["authority_class"]=="Controlled": raise ValueError("UNIVERSALIS cannot import C2O Controlled authority")
        if profile=="c2o" and node["authority_class"]=="Controlled" and not node.get("policy_ref"):
            raise ValueError("C2O Controlled graph node requires a private policy reference")
    edge_ids=set()
    for edge in graph["edges"]:
        if edge["edge_id"] in edge_ids: raise ValueError("duplicate edge_id")
        edge_ids.add(edge["edge_id"])
        if edge["from_node"] not in node_set or edge["to_node"] not in node_set:
            raise ValueError("architecture edge points to an unknown node")
        if not edge.get("source_refs"): raise ValueError("every edge requires provenance source references")
        if edge.get("valid_from") and edge.get("valid_to") and timestamp(edge["valid_to"],"edge.valid_to") < timestamp(edge["valid_from"],"edge.valid_from"):
            raise ValueError("edge validity ends before it begins")
    for matrix in graph["matrices"]:
        for entry in matrix["entries"]:
            if entry["subject_node"] not in node_set: raise ValueError("matrix entry references unknown node")
            timestamp(entry["observed_at"],"matrix.observed_at")
    for proposal in graph["proposals"]:
        if proposal["status"]=="accepted":
            if not proposal.get("reviewed_by") or not proposal.get("decision_ref"):
                raise ValueError("accepted architecture proposal requires reviewer and decision evidence")
            if proposal["reviewed_by"]==proposal["proposed_by"]:
                raise ValueError("proposal author cannot independently accept their own architecture change")
    def walk(value):
        if isinstance(value,dict):
            leaked=FORBIDDEN.intersection(k.lower() for k in value)
            if leaked: raise ValueError("graph payload contains a forbidden credential-bearing field")
            for child in value.values(): walk(child)
        elif isinstance(value,list):
            for child in value: walk(child)
    walk(graph)

def self_test(root):
    import copy
    g=json.loads((root/FIXTURE).read_text(encoding="utf-8"))
    validate(g,"universalis"); validate(g,"c2o")
    tests=[]
    bad=copy.deepcopy(g); bad["edges"][0]["to_node"]="missing"; tests.append((bad,"dangling edge"))
    bad=copy.deepcopy(g); bad["nodes"][0]["visibility"]="confidential"; tests.append((bad,"public confidential node"))
    bad=copy.deepcopy(g); bad["nodes"][0]["authority_class"]="Controlled"; tests.append((bad,"public Controlled authority"))
    bad=copy.deepcopy(g); bad["proposals"][0]["reviewed_by"]=bad["proposals"][0]["proposed_by"]; tests.append((bad,"self-approved proposal"))
    bad=copy.deepcopy(g); bad["edges"][0]["edge_id"]=bad["edges"][0]["edge_id"]; bad["edges"].append(bad["edges"][0]); tests.append((bad,"duplicate edge"))
    bad=copy.deepcopy(g); bad["nodes"][0]["password"]="not-a-secret-fixture"; tests.append((bad,"secret-bearing field"))
    for bad,label in tests:
        try: validate(bad,"universalis")
        except (ValueError,KeyError,TypeError): continue
        raise AssertionError("negative test unexpectedly passed: "+label)
    controlled=copy.deepcopy(g); controlled["nodes"][0]["authority_class"]="Controlled"; controlled["nodes"][0]["policy_ref"]="private-policy-fixture"; validate(controlled,"c2o")
    print("Architecture graph contract self-test: PASS (2 profiles, 7 negative/positive cases)")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--profile",choices=("c2o","universalis"),default="universalis")
    p.add_argument("--self-test",action="store_true"); p.add_argument("--check",action="store_true")
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2]); a=p.parse_args(); root=a.root.resolve()
    if a.self_test: self_test(root)
    if a.check:
        try: validate(json.loads((root/FIXTURE).read_text(encoding="utf-8")),a.profile); print(f"Architecture graph validation: PASS (profile={a.profile})")
        except (OSError,UnicodeError,json.JSONDecodeError,ValueError,KeyError,TypeError) as exc: print("Architecture graph validation: FAIL: "+str(exc)); return 1
    if not a.self_test and not a.check: p.error("choose --self-test and/or --check")
    return 0
if __name__=="__main__": sys.exit(main())
