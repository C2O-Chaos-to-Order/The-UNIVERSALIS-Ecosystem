"""Finding records with a stated severity basis."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .constants import SEVERITIES


@dataclass(frozen=True)
class Finding:
    finding_id: str
    severity: str
    title: str
    basis: str
    evidence: str
    repo: str | None = None
    related: str | None = None

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"unsupported severity: {self.severity!r}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def severity_counts(findings: list[Finding]) -> dict[str, int]:
    counts = {name: 0 for name in SEVERITIES}
    for finding in findings:
        counts[finding.severity] += 1
    return counts
