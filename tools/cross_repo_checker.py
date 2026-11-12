#!/usr/bin/env python3
"""Public-safe Cross-repo Compatibility Checker skeleton (UNIVERSALIS).

Read-only. Fail-closed. Public allowlist only.
A pass is not authorization, scientific validation, or independent verification.
Does not access private repositories or credentials.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PUBLIC_DEFAULT_ALLOWLIST = [
    "The-UNIVERSALIS-Ecosystem",
    "Research-for-the-UNIVERSALIS-Ecosystem",
    "The-UNIVERSALIS-Ontology",
    "The-UNIVERSALIS-Human-Knowledge",
    "The-UNIVERSALIS-Human-Capabilities",
    "The-UNIVERSALIS-Human-Skills",
    "The-UNIVERSALIS-Human-Powers",
    "The-UNIVERSALIS-Intelligence-Knowledge",
    "The-UNIVERSALIS-Intelligence-Capabilities",
    "The-UNIVERSALIS-Intelligence-Skills",
    "The-UNIVERSALIS-Intelligence-Powers",
    "The-UNIVERSALIS-Encyclopedias",
]


def run_check(allowlist: list[str]) -> dict[str, Any]:
    results = []
    for repo in allowlist:
        results.append({
            "check": f"public_contract_and_provenance:{repo}",
            "status": "UNKNOWN",
            "detail": "public skeleton — live inspection not yet implemented",
        })
    return {
        "run_id": f"uni-cross-repo-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "schema_version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "allowlist": allowlist,
        "results": results,
        "limitations": "Public skeleton only. Operates solely on public repositories. Does not perform live validation yet. A pass is not authorization.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="UNIVERSALIS public Cross-repo Compatibility Checker (skeleton)"
    )
    parser.add_argument(
        "--allowlist",
        nargs="*",
        default=PUBLIC_DEFAULT_ALLOWLIST,
        help="Public repository names (defaults to the public UNIVERSALIS catalog)",
    )
    parser.add_argument("--output", type=Path, help="Write JSON run record")
    args = parser.parse_args(argv)

    # Hard guard: refuse any name that looks private
    private_markers = ("C2O", "private", "internal")
    for name in args.allowlist:
        if any(m.lower() in name.lower() for m in private_markers) and not name.startswith("The-UNIVERSALIS"):
            print(f"refusing potentially private repository name: {name}", file=sys.stderr)
            return 2

    record = run_check(args.allowlist)
    text = json.dumps(record, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
