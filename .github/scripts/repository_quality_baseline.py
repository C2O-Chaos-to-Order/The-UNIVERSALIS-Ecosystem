#!/usr/bin/env python3
"""Dependency-free baseline checks for repository JSON contracts and manifests."""
from __future__ import annotations
import argparse,json,sys,tempfile
from pathlib import Path
EXCLUDED_DIRS={".git",".venv","venv","node_modules","dist","build","vendor"}
CONTRACT_DIRS={"schema","schemas","manifest","manifests","contracts","capabilities","skills"}
CONTRACT_FILENAMES={"package.json","tsconfig.json"}
def is_contract_json(path):
 p=[x.lower() for x in path.parts]
 return path.name.lower() in CONTRACT_FILENAMES or any(x in CONTRACT_DIRS for x in p[:-1])
def find_contract_json(root):
 return sorted(x for x in root.rglob("*.json") if x.is_file() and not any(p in EXCLUDED_DIRS for p in x.relative_to(root).parts) and is_contract_json(x.relative_to(root)))
def validate_json_file(path):
 try:
  with path.open("r",encoding="utf-8") as f: json.load(f)
 except (OSError,UnicodeError,json.JSONDecodeError) as e: return f"{path}: {e}"
 return None
def self_test():
 with tempfile.TemporaryDirectory() as t:
  r=Path(t); d=r/"schemas"; d.mkdir()
  (d/"valid.schema.json").write_text('{"type":"object"}',encoding="utf-8")
  (d/"invalid.schema.json").write_text('{"type":',encoding="utf-8")
  (r/"ordinary.json").write_text('{"ignored":true}',encoding="utf-8")
  files=find_contract_json(r); assert len(files)==2,files
  errors=[validate_json_file(p) for p in files]; assert sum(x is not None for x in errors)==1,errors
 print("Repository quality baseline self-test: PASS")
def check(root):
 files=find_contract_json(root); errors=[e for p in files if (e:=validate_json_file(p))]
 if errors:
  print("JSON contract validation: FAIL"); [print(" - "+e) for e in errors]; return 1
 print(f"JSON contract validation: PASS ({len(files)} contract/config JSON file(s) checked)")
 if not files: print("No contract/config JSON files exist yet; the check will cover them when added.")
 return 0
def main():
 p=argparse.ArgumentParser(description=__doc__); p.add_argument("--self-test",action="store_true"); p.add_argument("--check",action="store_true"); p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2]); a=p.parse_args()
 if a.self_test: self_test()
 if a.check: return check(a.root.resolve())
 if not a.self_test: p.error("choose --self-test and/or --check")
 return 0
if __name__=="__main__": sys.exit(main())
