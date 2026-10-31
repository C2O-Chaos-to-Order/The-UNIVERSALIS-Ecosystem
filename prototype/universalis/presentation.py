"""Status and claim rendering.

A status is a text label plus a machine-readable value. Colour may be stored
beside those two and is never enough to construct or render a status.
"""

from __future__ import annotations

from dataclasses import dataclass

from universalis.errors import (
    ColourAloneRefused,
    IncompleteClaimRendering,
    StateCollapseRefused,
    StatusAnnouncementRequired,
    StatusIncomplete,
    VocabularyBoundaryError,
)
from universalis.states import TransportOutcome, require_evidence_state


@dataclass(frozen=True)
class Status:
    machine_value: str
    text_label: str

    def __post_init__(self) -> None:
        if not isinstance(self.machine_value, str) or not self.machine_value.strip():
            raise StatusIncomplete(
                "ULC-21-03: a status needs a machine-readable value"
            )
        if not isinstance(self.text_label, str) or not self.text_label.strip():
            raise StatusIncomplete(
                "ULC-21-03: a status needs a textual label"
            )


@dataclass(frozen=True)
class RenderedStatus:
    text_label: str
    machine_value: str
    text: str
    colour_supplement: str | None = None

    def __post_init__(self) -> None:
        if not self.text_label or not self.machine_value or not self.text:
            raise ColourAloneRefused(
                "ULC-21-03: a rendering needs a text label and a machine-readable value"
            )
        if self.text_label not in self.text or self.machine_value not in self.text:
            raise ColourAloneRefused(
                "ULC-21-09: the rendered text must carry the label and the machine value"
            )


@dataclass(frozen=True)
class StatusChange:
    previous: Status
    current: Status
    announcement_text: str

    def __post_init__(self) -> None:
        if not isinstance(self.previous, Status) or not isinstance(self.current, Status):
            raise StatusAnnouncementRequired(
                "ULC-21-09: a status change names the previous and current status"
            )
        if not isinstance(self.announcement_text, str) or not self.announcement_text.strip():
            raise StatusAnnouncementRequired(
                "ULC-21-09: a status change is announced in text"
            )


@dataclass(frozen=True)
class RenderedClaim:
    claim_id: str
    evidence_state: str
    reason: str
    source_trace: str
    text: str
    presented_as_resolution: bool

    def __post_init__(self) -> None:
        if self.presented_as_resolution:
            raise IncompleteClaimRendering(
                "ULC-21-01: readability is not resolution"
            )
        if self.evidence_state not in self.text:
            raise IncompleteClaimRendering(
                "ULC-21-01: the rendering must include the evidence state"
            )
        if self.reason not in self.text or self.source_trace not in self.text:
            raise IncompleteClaimRendering(
                "ULC-21-01: the rendering must include the reason and the source"
            )


def status_from_colour(colour: str) -> Status:
    raise ColourAloneRefused(
        "ULC-21-03: colour, shape, or icon cannot replace a text label and a machine value"
        + (f" (received colour {colour!r})" if colour else "")
    )


def render_status(status: Status | None = None, *, colour: str | None = None) -> RenderedStatus:
    if not isinstance(status, Status):
        raise ColourAloneRefused(
            "ULC-21-03: a status rendering requires a text label and a machine-readable "
            "value; a colour by itself cannot be rendered"
        )
    text = f"{status.text_label} [{status.machine_value}]"
    return RenderedStatus(
        text_label=status.text_label,
        machine_value=status.machine_value,
        text=text,
        colour_supplement=colour,
    )


def announce_status_change(
    previous: Status, current: Status, announcement_text: str
) -> StatusChange:
    return StatusChange(
        previous=previous,
        current=current,
        announcement_text=announcement_text,
    )


def render_status_change(change: StatusChange) -> str:
    return (
        f"{change.announcement_text} "
        f"{change.previous.text_label} [{change.previous.machine_value}] -> "
        f"{change.current.text_label} [{change.current.machine_value}]"
    )


@dataclass(frozen=True)
class PresentationProjection:
    """A display-only collapse. It is not a canonical record and cannot be saved as one."""

    kind: str
    states: tuple
    writable: bool

    def __post_init__(self) -> None:
        if self.kind != "presentation_projection" or self.writable:
            raise StateCollapseRefused(
                "ULC-21-08: a presentation projection is labelled as a projection "
                "and is not writable as a canonical record"
            )


def project_for_display(states: list[str]) -> PresentationProjection:
    return PresentationProjection(
        kind="presentation_projection",
        states=tuple(states),
        writable=False,
    )


def save_projection_as_record(projection: PresentationProjection) -> None:
    raise StateCollapseRefused(
        "ULC-21-08: a presentation projection cannot be written back as the canonical record"
    )


def render_claim(
    *,
    claim_id: str,
    evidence_state: object,
    reason: str,
    source_trace: str,
    readable: bool = False,
) -> RenderedClaim:
    if isinstance(evidence_state, TransportOutcome):
        raise VocabularyBoundaryError(
            "a transport outcome cannot be rendered as a claim's evidence state"
        )
    state = require_evidence_state(evidence_state)
    if not reason or not str(reason).strip():
        raise IncompleteClaimRendering(
            "ULC-21-01: a claim rendering needs an explanatory reason"
        )
    if not source_trace or not str(source_trace).strip():
        raise IncompleteClaimRendering(
            "ULC-21-01: a claim rendering needs a traceable source"
        )
    text = f"state={state}; reason={reason}; source={source_trace}"
    return RenderedClaim(
        claim_id=claim_id,
        evidence_state=state,
        reason=reason,
        source_trace=source_trace,
        text=text,
        presented_as_resolution=False,
    )
