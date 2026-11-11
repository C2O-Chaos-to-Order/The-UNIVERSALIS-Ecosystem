
"""Command-line entry for Engineering Doctor."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .allowlist import load_name_file
from .config import RuntimeConfig
from .constants import (
    BANNER,
    CLASSIFICATION,
    DEFAULT_GITHUB_OWNER,
    TOOL_NAME,
    TOOL_STATUS,
    TOOL_VERSION,
)
from .run import RunRequest, default_output_dir, execute, print_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="engineering_doctor",
        description=(
            f"{TOOL_NAME} v{TOOL_VERSION} ({TOOL_STATUS} / {CLASSIFICATION}). {BANNER}"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run_cmd = sub.add_parser("run", help="run a read-only inventory and suite report")
    run_cmd.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_dir(),
        help="directory for immutable run records (default: a temp dir outside the repo)",
    )
    run_cmd.add_argument(
        "--owner",
        default="",
        help="GitHub owner or organization (default: this repository's public owner, or ENGINEERING_DOCTOR_OWNER)",
    )
    run_cmd.add_argument(
        "--allowlist-file",
        type=Path,
        help="JSON list or newline-separated file of repository names that may be inventoried",
    )
    run_cmd.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="repository name that must be refused if requested (repeatable)",
    )
    run_cmd.add_argument(
        "--repo",
        action="append",
        default=[],
        help="limit inventory to a configured repository (repeatable)",
    )
    run_cmd.add_argument(
        "--skip-suites",
        action="store_true",
        help="do not clone or execute suite adapters (recorded as NOT_RUN)",
    )
    run_cmd.add_argument(
        "--skip-inventory",
        action="store_true",
        help="do not query GitHub (inventory will be empty; used in isolated tests)",
    )
    run_cmd.add_argument(
        "--no-compare-behind",
        action="store_true",
        help="skip per-PR compare API calls for behind-count",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command != "run":
        parser.print_help()
        return 2
    allowlist = tuple(load_name_file(args.allowlist_file)) if args.allowlist_file else ()
    owner = (
        args.owner.strip()
        or os.environ.get("ENGINEERING_DOCTOR_OWNER", "").strip()
        or DEFAULT_GITHUB_OWNER
    )
    config = RuntimeConfig(
        github_owner=owner,
        allowlist=allowlist,
        excluded=tuple(item.strip() for item in args.exclude if item.strip()),
    )
    print(BANNER, file=sys.stderr)
    print(f"{TOOL_NAME} v{TOOL_VERSION} — {TOOL_STATUS} / {CLASSIFICATION}", file=sys.stderr)
    result = execute(
        RunRequest(
            output_dir=args.output_dir,
            repos=args.repo or None,
            skip_suites=args.skip_suites,
            skip_inventory=args.skip_inventory,
            compare_behind=not args.no_compare_behind,
            config=config,
        )
    )
    print_summary(result)
    return 2 if result.get("scope_refused") else 0


if __name__ == "__main__":
    raise SystemExit(main())
