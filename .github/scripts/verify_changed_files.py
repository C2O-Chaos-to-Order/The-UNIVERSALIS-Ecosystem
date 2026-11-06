#!/usr/bin/env python3
"""Validate changed repository text, documentation, and structured data.
Checks changed files only. This does not certify meaning, source authority,
security, research validity, owner acceptance, or release authorization.
"""
from __future__ import annotations
import csv, io, json, os, re, subprocess, sys
from pathlib import Path
from urllib.parse import unquote, urlparse
import yaml

ROOT = Path.cwd().resolve()
ZERO_SHA = "0" * 40
TEXT_SUFFIXES = {".md", ".markdown", ".json", ".csv", ".yaml", ".yml", ".py"}

def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout

def changed_paths() -> list[Path]:
    base = os.environ.get("BASE_SHA", "").strip()
    head = os.environ.get("HEAD_SHA", "HEAD").strip() or "HEAD"
    if not base or base == ZERO_SHA or not re.fullmatch(r"[0-9a-fA-F]{40}", base):
        base = git("rev-parse", "HEAD^").strip()
    return [Path(name) for name in git("diff", "--name-only", base, head).splitlines() if name.strip()]

def changed_whitespace_check() -> list[str]:
    """Reject new trailing spaces/tabs, allowing CRLF and Markdown hard breaks."""
    base = os.environ.get("BASE_SHA", "").strip()
    head = os.environ.get("HEAD_SHA", "HEAD").strip() or "HEAD"
    if not base or base == ZERO_SHA or not re.fullmatch(r"[0-9a-fA-F]{40}", base):
        base = git("rev-parse", "HEAD^").strip()
    diff = git("-c", "core.whitespace=cr-at-eol", "diff", "--no-ext-diff", "--unified=0", "--no-color", base, head)
    current_file = ""
    errors: list[str] = []
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:].split("\\t", 1)[0]
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        added = line[1:]
        trimmed = added.rstrip(" \t")
        trailing = len(added) - len(trimmed)
        if trailing == 0:
            continue
        suffix = Path(current_file).suffix.lower()
        # Two trailing spaces on a nonblank Markdown line are the standard
        # hard-line-break convention; blank-line whitespace and larger runs fail.
        if suffix in {".md", ".markdown"} and trailing == 2 and trimmed.strip():
            continue
        errors.append(
            f"{current_file}: added line has {trailing} trailing whitespace character(s): {added[-120:]}"
        )
    return errors

def markdown_without_fences(content: str, path: Path, errors: list[str]) -> str:
    kept: list[str] = []
    fence_char: str | None = None
    fence_len = 0
    for line in content.splitlines():
        match = re.match(r"^ {0,3}(\x60{3,}|~{3,})", line)
        if fence_char is None and match:
            token = match.group(1)
            fence_char, fence_len = token[0], len(token)
            kept.append("")
            continue
        if fence_char is not None:
            close = re.match(r"^ {0,3}(\x60+|~+)\s*$", line)
            if close and close.group(1)[0] == fence_char and len(close.group(1)) >= fence_len:
                fence_char, fence_len = None, 0
            kept.append("")
            continue
        kept.append(line)
    if fence_char is not None:
        errors.append(f"{path}: unclosed Markdown code fence")
    return "\n".join(kept)

def check_markdown(path: Path, content: str, errors: list[str]) -> None:
    visible = markdown_without_fences(content, path, errors)
    for match in re.finditer(r"!?\[[^\]]*\]\(([^)]+)\)", visible):
        destination = match.group(1).strip()
        if not destination:
            errors.append(f"{path}: empty Markdown link destination")
            continue
        if destination.startswith("<") and ">" in destination:
            destination = destination[1:destination.index(">")]
        else:
            destination = destination.split()[0]
        parsed = urlparse(destination)
        if parsed.scheme or parsed.netloc or destination.startswith("#"):
            continue
        raw_path = unquote(parsed.path)
        if not raw_path:
            continue
        target = (ROOT / raw_path.lstrip("/")) if raw_path.startswith("/") else (ROOT / path.parent / raw_path)
        target = target.resolve()
        try:
            target.relative_to(ROOT)
        except ValueError:
            errors.append(f"{path}: link escapes repository root: {destination}")
            continue
        if not target.exists():
            errors.append(f"{path}: broken local link: {destination}")

def check_csv(path: Path, content: str, errors: list[str]) -> None:
    try:
        rows = list(csv.reader(io.StringIO(content, newline="")))
    except csv.Error as exc:
        errors.append(f"{path}: malformed CSV: {exc}")
        return
    nonblank = [row for row in rows if row and any(cell.strip() for cell in row)]
    if not nonblank:
        errors.append(f"{path}: CSV has no header or records")
        return
    header = nonblank[0]
    if any(not cell.strip() for cell in header):
        errors.append(f"{path}: CSV contains an empty header")
    if len(set(header)) != len(header):
        errors.append(f"{path}: CSV contains duplicate column names")
    width = len(header)
    for row_number, row in enumerate(nonblank[1:], start=2):
        if len(row) != width:
            errors.append(f"{path}: row {row_number} has {len(row)} columns; expected {width}")

def main() -> int:
    try:
        paths = changed_paths()
    except Exception as exc:
        print(f"FAIL: cannot determine changed files: {exc}", file=sys.stderr)
        return 2
    errors = changed_whitespace_check()
    checked = 0
    for relative in paths:
        path = (ROOT / relative).resolve()
        try:
            path.relative_to(ROOT)
        except ValueError:
            errors.append(f"{relative}: changed path escapes repository root")
            continue
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"{relative}: expected UTF-8 text")
            continue
        except OSError as exc:
            errors.append(f"{relative}: cannot read file: {exc}")
            continue
        checked += 1
        suffix = path.suffix.lower()
        if suffix in {".md", ".markdown"}:
            check_markdown(relative, content, errors)
        elif suffix == ".json":
            try:
                json.loads(content)
            except (json.JSONDecodeError, ValueError) as exc:
                errors.append(f"{relative}: invalid JSON: {exc}")
        elif suffix == ".csv":
            check_csv(relative, content, errors)
        elif suffix in {".yaml", ".yml"}:
            try:
                list(yaml.safe_load_all(content))
            except yaml.YAMLError as exc:
                errors.append(f"{relative}: invalid YAML: {exc}")
        elif suffix == ".py":
            try:
                compile(content, str(relative), "exec")
            except SyntaxError as exc:
                errors.append(f"{relative}: Python syntax error: {exc}")
    if errors:
        print("Repository verification FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1
    print(f"Repository verification passed: {len(paths)} changed paths inspected; {checked} UTF-8 Markdown/JSON/CSV/YAML/Python files checked.")
    print("Local links are checked for target existence; heading anchors and external URLs are not fetched.")
    print("This is structural verification only, not semantic, security, research, or authorization approval.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
