
"""Optional Hypothesis properties. Not part of the stdlib unittest suite."""

from __future__ import annotations

from datetime import datetime, timezone

from hypothesis import given, settings, strategies as st

from engineering_doctor.allowlist import ScopeError, validate_requested_repos
from engineering_doctor.constants import BANNER
from engineering_doctor.findings import Finding
from engineering_doctor.records import build_record, validate_record
from engineering_doctor.suites import parse_unittest_output


@given(
    discovered=st.integers(min_value=0, max_value=80),
    failed=st.integers(min_value=0, max_value=20),
    errors=st.integers(min_value=0, max_value=20),
    skipped=st.integers(min_value=0, max_value=20),
)
@settings(max_examples=40)
def test_unittest_summary_reconciles(discovered, failed, errors, skipped):
    if failed + errors + skipped > discovered:
        return
    passed = discovered - failed - errors - skipped
    if failed or errors:
        banner = f"FAILED (failures={failed}, errors={errors}, skipped={skipped})"
    elif skipped:
        banner = f"OK (skipped={skipped})"
    else:
        banner = "OK"
    text = f"Ran {discovered} tests in 0.010s\n\n{banner}\n"
    parsed = parse_unittest_output(text)
    assert parsed.discovered == discovered
    assert parsed.passed == passed
    assert parsed.failed == failed
    assert parsed.errors == errors
    assert parsed.skipped == skipped
    assert parsed.reconciled()


@given(st.sampled_from(["example-one", "example-two", "example-excluded", "totally-unknown"]))
@settings(max_examples=20)
def test_excluded_and_unknown_names_are_never_accepted(name):
    allowlist = ("example-one", "example-two")
    excluded = ("example-excluded",)
    if name in excluded or name not in allowlist:
        try:
            validate_requested_repos([name], allowlist=allowlist, excluded=excluded)
        except ScopeError:
            return
        raise AssertionError(f"{name} should have been refused")
    assert validate_requested_repos([name], allowlist=allowlist, excluded=excluded) == [name]


@given(st.sampled_from(["Critical", "High", "Medium", "Low"]))
@settings(max_examples=8)
def test_records_always_carry_banner_and_never_a_score(severity):
    started = datetime(2026, 11, 10, 20, 0, tzinfo=timezone.utc)
    record = build_record(
        run_id="prop",
        started_at=started,
        finished_at=started,
        python_version="3.14.10",
        inputs={"k": "v"},
        inventory=[],
        suites=[],
        findings=[
            Finding(
                finding_id="P-001",
                severity=severity,
                title="property",
                basis=f"{severity} because this is a generated property fixture.",
                evidence="n/a",
            )
        ],
        limitations=["property test"],
        repo_shas={},
    )
    assert record["banner"] == BANNER
    assert record["classification"] == "PUBLIC_CANDIDATE"
    assert "confidence" not in record
    assert "readiness_percent" not in record
    assert validate_record(record) == []
