
"""Registered suite adapters and unittest output parsing."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from .constants import DEFAULT_GITHUB_OWNER, DEFAULT_SUITE_TIMEOUT_SEC
from .findings import Finding
from .github_client import redact

_RAN = re.compile(r"^Ran (\d+) tests? in ", re.MULTILINE)
_FAILED = re.compile(
    r"^FAILED \((?P<body>[^)]*)\)\s*$",
    re.MULTILINE,
)
_OK_SKIP = re.compile(r"^OK \(skipped=(\d+)\)\s*$", re.MULTILINE)
_OK = re.compile(r"^OK\s*$", re.MULTILINE)
_DETAIL = re.compile(r"(failures|errors|skipped|expected failures|unexpected successes)=(\d+)")


@dataclass
class ParsedUnittest:
    discovered: int
    passed: int
    failed: int
    errors: int
    skipped: int
    expected_failures: int = 0
    unexpected_successes: int = 0
    healthy_banner: bool = False

    def reconciled(self) -> bool:
        accounted = (
            self.passed
            + self.failed
            + self.errors
            + self.skipped
            + self.expected_failures
            + self.unexpected_successes
        )
        return accounted == self.discovered


def parse_unittest_output(text: str) -> ParsedUnittest:
    """Parse stdlib unittest discover output. Raises ValueError if unusable."""

    ran = _RAN.search(text)
    if not ran:
        raise ValueError("unittest output did not include a 'Ran N tests' summary")
    discovered = int(ran.group(1))
    failed = errors = skipped = expected_failures = unexpected_successes = 0
    healthy = False
    failed_match = _FAILED.search(text)
    skip_ok = _OK_SKIP.search(text)
    if failed_match:
        for key, value in _DETAIL.findall(failed_match.group("body")):
            count = int(value)
            if key == "failures":
                failed = count
            elif key == "errors":
                errors = count
            elif key == "skipped":
                skipped = count
            elif key == "expected failures":
                expected_failures = count
            elif key == "unexpected successes":
                unexpected_successes = count
    elif skip_ok:
        skipped = int(skip_ok.group(1))
        healthy = True
    elif _OK.search(text):
        healthy = True
    else:
        raise ValueError("unittest output had a Ran line but no OK or FAILED banner")
    passed = discovered - failed - errors - skipped - expected_failures - unexpected_successes
    if passed < 0:
        raise ValueError("unittest counts do not reconcile (passed would be negative)")
    parsed = ParsedUnittest(
        discovered=discovered,
        passed=passed,
        failed=failed,
        errors=errors,
        skipped=skipped,
        expected_failures=expected_failures,
        unexpected_successes=unexpected_successes,
        healthy_banner=healthy and failed == 0 and errors == 0 and unexpected_successes == 0,
    )
    if not parsed.reconciled():
        raise ValueError("unittest counts do not reconcile")
    return parsed


@dataclass
class SuiteResult:
    adapter_id: str
    repo: str
    pinned_sha: str
    resolved_sha: str | None
    command: list[str]
    workdir: str
    status: str
    discovered: int | None
    passed: int | None
    failed: int | None
    errors: int | None
    skipped: int | None
    timeout: bool
    not_run: bool
    returncode: int | None
    duration_sec: float | None
    porcelain_after: str
    output_excerpt: str
    error: str | None
    known_skip_seen: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


Cloner = Callable[[str, str, Path], str]


def default_cloner(repo: str, sha: str, dest: Path, owner: str = DEFAULT_GITHUB_OWNER) -> str:
    """Clone a repository at an exact SHA using gh/git, without logging credentials."""

    dest = dest.resolve()
    if dest.exists() and any(dest.iterdir()):
        raise RuntimeError(f"clone destination is not empty: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    clone = subprocess.run(
        ["gh", "repo", "clone", f"{owner}/{repo}", str(dest), "--", "--no-checkout"],
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if clone.returncode != 0:
        raise RuntimeError(
            redact(f"gh repo clone failed for {owner}/{repo}: {clone.stderr.strip()[-400:]}")
        )
    fetched = subprocess.run(
        ["git", "-C", str(dest), "fetch", "--quiet", "origin", sha],
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if fetched.returncode != 0:
        subprocess.run(
            ["git", "-C", str(dest), "fetch", "--quiet", "origin"],
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
        )
    checked = subprocess.run(
        ["git", "-C", str(dest), "checkout", "--quiet", "--detach", sha],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if checked.returncode != 0:
        raise RuntimeError(
            redact(f"git checkout {sha} failed in {repo}: {checked.stderr.strip()[-400:]}")
        )
    resolved = subprocess.run(
        ["git", "-C", str(dest), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return resolved.stdout.strip()


def _excerpt(text: str, limit: int = 4000) -> str:
    text = redact(text)
    if len(text) <= limit:
        return text
    return text[-limit:]


def run_suite_adapter(
    adapter: dict[str, object],
    scratch_root: Path,
    python_executable: str | None = None,
    cloner: Cloner | None = None,
    timeout_sec: int = DEFAULT_SUITE_TIMEOUT_SEC,
    existing_clones: dict[tuple[str, str], Path] | None = None,
    known_skip_markers: Sequence[str] = (),
) -> SuiteResult:
    """Run one registered adapter in a scratch clone."""

    adapter_id = str(adapter["id"])
    repo = str(adapter["repo"])
    pinned_sha = str(adapter["pinned_sha"])
    relative_workdir = str(adapter["workdir"])
    argv_suffix = tuple(adapter["argv_suffix"])  # type: ignore[arg-type]
    owner = str(adapter.get("owner") or DEFAULT_GITHUB_OWNER)
    python_exe = python_executable or sys.executable
    command = [python_exe, *argv_suffix]
    markers = tuple(adapter.get("known_skip_markers") or known_skip_markers or ())
    result = SuiteResult(
        adapter_id=adapter_id,
        repo=repo,
        pinned_sha=pinned_sha,
        resolved_sha=None,
        command=command,
        workdir=relative_workdir,
        status="UNKNOWN",
        discovered=None,
        passed=None,
        failed=None,
        errors=None,
        skipped=None,
        timeout=False,
        not_run=False,
        returncode=None,
        duration_sec=None,
        porcelain_after="",
        output_excerpt="",
        error=None,
    )
    clone_key = (repo, pinned_sha)
    cache = existing_clones if existing_clones is not None else {}
    try:
        if clone_key in cache:
            repo_root = cache[clone_key]
            resolved = subprocess.run(
                ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            ).stdout.strip()
        else:
            dest = scratch_root / f"{repo}-{pinned_sha[:12]}"
            if dest.exists():
                shutil.rmtree(dest)
            if cloner is not None:
                resolved = cloner(repo, pinned_sha, dest)
            else:
                resolved = default_cloner(repo, pinned_sha, dest, owner=owner)
            repo_root = dest
            cache[clone_key] = repo_root
        result.resolved_sha = resolved
        workdir = repo_root if relative_workdir in {".", ""} else repo_root / relative_workdir
        if not workdir.is_dir():
            result.status = "UNKNOWN"
            result.error = f"workdir does not exist: {relative_workdir}"
            return result
        started = time.monotonic()
        try:
            proc = subprocess.run(
                command,
                cwd=str(workdir),
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
        except subprocess.TimeoutExpired as exc:
            result.timeout = True
            result.status = "TIMEOUT"
            result.duration_sec = round(time.monotonic() - started, 3)
            output = ""
            if exc.stdout:
                output += exc.stdout if isinstance(exc.stdout, str) else exc.stdout.decode(
                    "utf-8", errors="replace"
                )
            if exc.stderr:
                output += "\n" + (
                    exc.stderr if isinstance(exc.stderr, str) else exc.stderr.decode(
                        "utf-8", errors="replace"
                    )
                )
            result.output_excerpt = _excerpt(output)
            result.error = f"suite exceeded {timeout_sec}s"
            return result
        result.duration_sec = round(time.monotonic() - started, 3)
        result.returncode = proc.returncode
        output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        result.output_excerpt = _excerpt(output)
        result.known_skip_seen = any(marker in output for marker in markers if marker)
        porcelain = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        result.porcelain_after = porcelain.stdout
        try:
            parsed = parse_unittest_output(output)
        except ValueError as exc:
            result.status = "PARSE_ERROR"
            result.error = str(exc)
            return result
        result.discovered = parsed.discovered
        result.passed = parsed.passed
        result.failed = parsed.failed
        result.errors = parsed.errors
        result.skipped = parsed.skipped
        if result.porcelain_after.strip():
            result.status = "DIRTY"
            result.error = "scratch checkout was modified by the suite"
            return result
        if parsed.discovered == 0:
            result.status = "ZERO_TESTS"
            result.error = "suite reported zero tests"
            return result
        if parsed.failed or parsed.errors or parsed.unexpected_successes:
            result.status = "FAILED"
            return result
        if proc.returncode != 0 and not parsed.healthy_banner:
            result.status = "FAILED"
            result.error = f"unittest exited {proc.returncode}"
            return result
        result.status = "ok"
        return result
    except Exception as exc:  # noqa: BLE001 — fail closed; do not invent a pass
        result.status = "UNKNOWN"
        result.error = redact(str(exc))
        result.not_run = result.discovered is None
        return result


def run_registered_suites(
    scratch_root: Path,
    python_executable: str | None = None,
    cloner: Cloner | None = None,
    timeout_sec: int = DEFAULT_SUITE_TIMEOUT_SEC,
    adapters: Sequence[dict[str, object]] = (),
    known_skip_markers: Sequence[str] = (),
) -> list[SuiteResult]:
    cache: dict[tuple[str, str], Path] = {}
    results = []
    for adapter in adapters:
        results.append(
            run_suite_adapter(
                adapter,
                scratch_root=scratch_root,
                python_executable=python_executable,
                cloner=cloner,
                timeout_sec=timeout_sec,
                existing_clones=cache,
                known_skip_markers=known_skip_markers,
            )
        )
    return results


def skipped_suite_placeholders(
    adapters: Sequence[dict[str, object]] = (),
) -> list[SuiteResult]:
    results = []
    for adapter in adapters:
        results.append(
            SuiteResult(
                adapter_id=str(adapter["id"]),
                repo=str(adapter["repo"]),
                pinned_sha=str(adapter["pinned_sha"]),
                resolved_sha=None,
                command=["<skipped>"],
                workdir=str(adapter["workdir"]),
                status="NOT_RUN",
                discovered=None,
                passed=None,
                failed=None,
                errors=None,
                skipped=None,
                timeout=False,
                not_run=True,
                returncode=None,
                duration_sec=None,
                porcelain_after="",
                output_excerpt="",
                error="suite adapters were skipped for this invocation",
            )
        )
    return results


def findings_from_suites(results: list[SuiteResult]) -> list[Finding]:
    findings: list[Finding] = []
    seq = 0
    for item in results:
        if item.status == "ok":
            if item.skipped:
                seq += 1
                evidence = (
                    f"{item.discovered} discovered, {item.passed} passed, "
                    f"{item.skipped} skipped"
                )
                if item.known_skip_seen:
                    evidence += "; includes a configured known skip marker"
                findings.append(
                    Finding(
                        finding_id=f"SUI-{seq:03d}",
                        severity="Low",
                        title=f"{item.adapter_id} passed with honest skip(s)",
                        basis=(
                            "Low because a skip is recorded rather than converted into "
                            "a pass. It is not treated as full coverage."
                        ),
                        evidence=evidence,
                        repo=item.repo,
                        related=item.adapter_id,
                    )
                )
            continue
        seq += 1
        if item.status == "NOT_RUN":
            severity = "Medium"
            basis = (
                "Medium because a registered adapter was not executed; NOT_RUN "
                "must not be presented as a pass."
            )
        elif item.status in {"UNKNOWN", "PARSE_ERROR", "TIMEOUT"}:
            severity = "High"
            basis = (
                "High because a crash, timeout, parser error, or clone failure is "
                "fail-closed and cannot appear healthy."
            )
        elif item.status in {"FAILED", "DIRTY", "ZERO_TESTS"}:
            severity = "High"
            basis = (
                "High because a failing, empty, or source-mutating suite cannot "
                "be treated as a healthy regression signal."
            )
        else:
            severity = "High"
            basis = "High because any non-ok suite status is fail-closed."
        findings.append(
            Finding(
                finding_id=f"SUI-{seq:03d}",
                severity=severity,
                title=f"{item.adapter_id} status is {item.status}",
                basis=basis,
                evidence=item.error or f"status={item.status}",
                repo=item.repo,
                related=item.adapter_id,
            )
        )
    return findings
