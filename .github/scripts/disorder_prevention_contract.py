#!/usr/bin/env python3
"""Validate the portable, authority-neutral disorder-prevention fixture."""
from __future__ import annotations
import argparse, copy, json, sys
from pathlib import Path

LAYERS={"Communication","Cognition","Structure","Knowledge","Normative"}
REGIMES={"Controlled","Hedge","Chaos","undetermined"}
TYPES={"disorder_taxonomy_profile","disorder_event","chaos_experiment","stability_receipt","containment_attestation","resilience_index"}
HEX=set("0123456789abcdef")

def digest(x):
    return isinstance(x,str) and len(x)==71 and x.startswith("sha256:") and set(x[7:])<=HEX

def validate(doc):
    errors=[]
    if doc.get("schema_version")!="1.0.0": errors.append("schema_version must be 1.0.0")
    if doc.get("inventory_id")!="disorder-chaos-prevention-25": errors.append("inventory_id mismatch")
    records=doc.get("records")
    if not isinstance(records,list) or not records: return errors+["records must be a non-empty list"]
    seen=set()
    for i,r in enumerate(records):
        p=f"records[{i}]"
        if not isinstance(r,dict): errors.append(p+" must be an object"); continue
        rid=r.get("record_id")
        if not isinstance(rid,str) or not rid.startswith("DP-"): errors.append(p+" invalid record_id")
        elif rid in seen: errors.append(p+" duplicate record_id")
        else: seen.add(rid)
        if r.get("record_type") not in TYPES: errors.append(p+" unsupported record_type")
        if not digest(r.get("system_profile_digest")): errors.append(p+" invalid system_profile_digest")
        if r.get("authority_effect")!="none": errors.append(p+" authority_effect must be none")
        if r.get("boundary")!="portable_public_record": errors.append(p+" public boundary violated")
        if r.get("verification_status") not in {"proposed","observed","reproduced","independently_verified","inconclusive","not_tested"}: errors.append(p+" invalid verification_status")
        kind=r.get("record_type")
        if kind=="disorder_taxonomy_profile":
            if set(r.get("disorder_layers",[]))!=LAYERS: errors.append(p+" taxonomy must include the five defined layers")
            if set(r.get("collapse_regimes",[]))!={"Controlled","Hedge","Chaos"}: errors.append(p+" must declare Controlled/Hedge/Chaos regimes")
        elif kind=="disorder_event":
            if r.get("disorder_layer") not in LAYERS: errors.append(p+" invalid disorder_layer")
            if r.get("regime") not in REGIMES: errors.append(p+" invalid regime")
            if not isinstance(r.get("severity"),int) or not 0<=r["severity"]<=5: errors.append(p+" severity must be integer 0..5")
            if r.get("trigger_type") not in {"external","internal","environmental","unknown"}: errors.append(p+" trigger_type invalid")
            if r.get("cause_status") not in {"confirmed","suspected","unknown","not_investigated"}: errors.append(p+" cause_status invalid")
        elif kind=="chaos_experiment":
            if r.get("environment_class") not in {"synthetic","isolated_test","staging"}: errors.append(p+" production or unknown target environment is prohibited")
            if not digest(r.get("target_profile_digest")): errors.append(p+" target profile digest invalid")
            if not r.get("fault_classes"): errors.append(p+" fault_classes required")
            if not r.get("cleanup_plan"): errors.append(p+" cleanup_plan required")
            if not r.get("preconditions"): errors.append(p+" safety preconditions required")
            if not isinstance(r.get("max_duration_seconds"),int) or not 1<=r["max_duration_seconds"]<=86400: errors.append(p+" invalid bounded duration")
        elif kind=="stability_receipt":
            if not isinstance(r.get("value"),(int,float)) or not isinstance(r.get("threshold"),(int,float)): errors.append(p+" value and threshold must be numeric")
            if not r.get("unit") or not r.get("metric_definition"): errors.append(p+" metric unit/definition required")
            if r.get("verdict") not in {"stable","throttled","quarantined","halted","unknown"}: errors.append(p+" verdict invalid")
            u=r.get("uncertainty",{})
            if isinstance(u,dict) and u.get("lower") is not None and u.get("upper") is not None and u["lower"]>u["upper"]: errors.append(p+" uncertainty bounds reversed")
        elif kind=="containment_attestation":
            if r.get("action") not in {"throttle","quarantine","rollback","halt","release_after_review","none"}: errors.append(p+" invalid containment action")
            if r.get("outcome")=="effective" and r.get("independent_readback") is not True: errors.append(p+" cannot claim effective containment without independent readback")
            if r.get("verification_status")=="independently_verified" and r.get("outcome")!="effective": errors.append(p+" independent containment status conflicts with outcome")
            if r.get("signature_status")=="verified" and (not r.get("signer_reference") or not digest(r.get("signature_digest"))): errors.append(p+" verified signature lacks signer/digest")
        elif kind=="resilience_index":
            n,d=r.get("numerator"),r.get("denominator")
            v=r.get("value_percent")
            if not isinstance(n,int) or not isinstance(d,int) or d<=0 or n<0 or n>d: errors.append(p+" numerator/denominator invalid")
            elif not isinstance(v,(int,float)) or abs(v-(100*n/d))>0.01: errors.append(p+" value_percent inconsistent with counts")
            ci=r.get("confidence_interval",{})
            if isinstance(ci,dict) and ci.get("lower_percent") is not None and ci.get("upper_percent") is not None:
                if ci["lower_percent"]>ci["upper_percent"]: errors.append(p+" confidence interval bounds reversed")
    return errors

def negative_cases(doc):
    cases=[]
    def add(name,mutate):
        d=copy.deepcopy(doc); mutate(d); cases.append((name,d))
    add("authority escalation",lambda d:d["records"][0].update(authority_effect="allow"))
    add("private boundary",lambda d:d["records"][0].update(boundary="private_c2o"))
    add("invalid taxonomy layer",lambda d:d["records"][0].update(disorder_layers=["Communication"]))
    add("unknown disorder layer",lambda d:d["records"][1].update(disorder_layer="Hardware"))
    add("unsupported regime",lambda d:d["records"][1].update(regime="Unbounded"))
    add("severity out of range",lambda d:d["records"][1].update(severity=9))
    add("production chaos target",lambda d:d["records"][2].update(environment_class="production"))
    add("unbounded experiment duration",lambda d:d["records"][2].update(max_duration_seconds=999999))
    add("missing cleanup",lambda d:d["records"][2].update(cleanup_plan=""))
    add("unitless stability metric",lambda d:d["records"][3].update(unit=""))
    add("unknown stability verdict",lambda d:d["records"][3].update(verdict="guaranteed"))
    add("effective containment without readback",lambda d:d["records"][4].update(outcome="effective",independent_readback=False))
    add("verified signature without signer",lambda d:d["records"][4].update(signature_status="verified",signature_digest=None,signer_reference=None))
    add("resilience over 100 percent",lambda d:d["records"][5].update(value_percent=120))
    add("invalid denominator",lambda d:d["records"][5].update(denominator=0))
    return cases

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--fixture",required=True,type=Path); args=ap.parse_args()
    try: doc=json.loads(args.fixture.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: print(f"ERROR: {exc}",file=sys.stderr); return 2
    errors=validate(doc)
    if errors:
        for e in errors: print("FAIL:",e)
        return 1
    failed=[name for name,mutated in negative_cases(doc) if not validate(mutated)]
    if failed:
        for name in failed: print("FAIL: negative case accepted:",name)
        return 1
    print(f"PASS: {len(doc['records'])} synthetic records pass semantic checks")
    print("PASS: 15 negative cases rejected")
    print("NOTE: a fixture pass proves neither product behavior nor production safety.")
    return 0
if __name__=="__main__": raise SystemExit(main())
