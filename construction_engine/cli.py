"""Command-line interface."""
import argparse
import json
from pathlib import Path

from .engine import BuildError, build, verify


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="c2o-build")
    sub = parser.add_subparsers(dest="command", required=True)
    p_build = sub.add_parser("build", help="build files from a JSON specification")
    p_build.add_argument("spec", type=Path)
    p_build.add_argument("--output", type=Path, required=True)
    p_verify = sub.add_parser("verify", help="verify a build record and file hashes")
    p_verify.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = build(args.spec, args.output) if args.command == "build" else verify(args.output)
    except BuildError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command == "build" or result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
