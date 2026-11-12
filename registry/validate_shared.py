"""Minimal extension: validate instances against the public shared artifact contract.

Uses the same fail-closed style as registry/validate.py. Standard library only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Re-use the core validator from the sibling module when run as part of the package.
try:
    from registry.validate import validate_instance, load_json
except ImportError:  # direct execution
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from registry.validate import validate_instance, load_json

SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "shared_artifact_contract_public.schema.json"


def validate_shared_artifact(instance_path: Path) -> list[str]:
    schema = load_json(SCHEMA_PATH)
    instance = load_json(instance_path)
    return validate_instance(instance, schema, str(instance_path))


def main(argv: list[str] | None = None) -> int:
    if len(sys.argv) < 2:
        print("usage: python -m registry.validate_shared <instance.json>", file=sys.stderr)
        return 2
    errors = validate_shared_artifact(Path(sys.argv[1]))
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1
    print("shared artifact ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
