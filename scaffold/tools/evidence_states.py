"""Ordered evidence states for a research programme package.

The ladder separates a plan, an execution record, a reproduction, and a human
decision. Tooling may set only the states that record what a program did.
``reviewed``, ``accepted`` and ``authorized`` stay unset unless an explicit
owner or reviewer decision record cites them. ``authorization_status`` is not
an evidence state. It is a separate column, default ``NOT_AUTHORIZED``, and
nothing in this module copies it from ``evidence_status`` or from the ladder.
This module does not award programme credit and does not decide that a claim
is true.
"""

from __future__ import annotations

STATES = (
    "planned",
    "executed",
    "failed",
    "incomplete",
    "reproduced",
    "reviewed",
    "accepted",
    "authorized",
)

# States a program may record from its own run. ``failed`` and ``incomplete``
# are execution outcomes beside ``executed``, not steps toward acceptance.
TOOL_SETTABLE = frozenset(
    {"planned", "executed", "failed", "incomplete", "reproduced"}
)

DECISION_REQUIRED = frozenset({"reviewed", "accepted", "authorized"})

PROGRAMME_CREDITS = (
    "NONE",
    "CANDIDATE_PENDING_OWNER_REVIEW",
    "AWARDED",
)

TOOL_CREDITS = frozenset({"NONE", "CANDIDATE_PENDING_OWNER_REVIEW"})

# Separate from the evidence ladder. The default is the only value tooling
# may record. ``AUTHORIZED`` requires an authorization record that says so.
DEFAULT_AUTHORIZATION_STATUS = "NOT_AUTHORIZED"
AUTHORIZATION_GRANTED = "AUTHORIZED"

# Legal edges. The spine is planned → executed → reproduced → reviewed →
# accepted → authorized. ``failed`` and ``incomplete`` are recorded from
# ``planned`` (or, for a resumed case, ``incomplete`` → ``executed``). They
# do not advance to review. A later state never rewrites an earlier run;
# start a new record instead of demoting ``executed`` to ``failed``.
TRANSITIONS = {
    "planned": frozenset({"executed", "failed", "incomplete"}),
    "executed": frozenset({"reproduced"}),
    "failed": frozenset({"planned"}),
    "incomplete": frozenset({"planned", "executed"}),
    "reproduced": frozenset({"reviewed"}),
    "reviewed": frozenset({"accepted"}),
    "accepted": frozenset({"authorized"}),
    "authorized": frozenset(),
}

_DECISION_RANK = {"reviewed": 0, "accepted": 1, "authorized": 2}


class EvidenceStateError(ValueError):
    """An evidence state or programme credit was refused."""


def ladder_index(state: str) -> int:
    """Return the canonical position of ``state`` in :data:`STATES`."""
    try:
        return STATES.index(state)
    except ValueError as exc:
        raise EvidenceStateError(f"unknown evidence state {state!r}") from exc


def tooling_set(state: str) -> str:
    """Return ``state`` when tooling is allowed to set it.

    ``reviewed``, ``accepted`` and ``authorized`` are refused here even if a
    decision record is supplied. Those states are entered through
    :func:`transition`, which checks the decision.
    """
    if state not in TOOL_SETTABLE:
        raise EvidenceStateError(
            f"tooling cannot set evidence state {state!r}; "
            "reviewed, accepted and authorized require an explicit "
            "owner or reviewer decision record"
        )
    return state


def _decision_rank(state: str) -> int:
    if state not in _DECISION_RANK:
        raise EvidenceStateError(
            f"decision state must be reviewed, accepted or authorized, not {state!r}"
        )
    return _DECISION_RANK[state]


def decision_supports(record: dict, state: str, target_id: str) -> bool:
    """Return whether ``record`` cites ``target_id`` for ``state`` or a higher decision state.

    A decision of ``authorized`` covers ``accepted`` and ``reviewed`` for the
    cited targets. A decision of ``accepted`` covers ``reviewed``. The cover
    is not programme credit and it is not a check that the cited person exists.
    """
    if not isinstance(record, dict):
        return False
    if record.get("authority") not in {"owner", "reviewer"}:
        return False
    decided_by = record.get("decided_by")
    citation = record.get("citation")
    if not isinstance(decided_by, str) or not decided_by.strip():
        return False
    if not isinstance(citation, str) or not citation.strip():
        return False
    targets = record.get("target_ids")
    if not isinstance(targets, list) or target_id not in targets:
        return False
    claimed = record.get("state")
    if not isinstance(claimed, str) or claimed not in _DECISION_RANK:
        return False
    try:
        needed = _decision_rank(state)
    except EvidenceStateError:
        return False
    return _decision_rank(claimed) >= needed


def require_state_authority(state: str, decision_records, target_id: str) -> str:
    """Allow a tool-settable state, or a decision state cited for ``target_id``.

    ``decision_records`` is an iterable of decision objects. The function
    returns ``state`` when it is allowed and raises :class:`EvidenceStateError`
    otherwise.
    """
    if state not in STATES:
        raise EvidenceStateError(f"unknown evidence state {state!r}")
    if state in TOOL_SETTABLE:
        return state
    records = list(decision_records or [])
    if any(decision_supports(record, state, target_id) for record in records):
        return state
    raise EvidenceStateError(
        f"evidence state {state!r} requires an explicit owner or reviewer decision record"
    )


def credit_supported(record: dict, target_id: str) -> bool:
    """Return whether ``record`` explicitly awards programme credit for ``target_id``.

    The decision must be ``accepted`` or ``authorized`` and must set
    ``programme_credit`` to ``AWARDED``. Accepting an evidence state does not
    by itself award credit.
    """
    if not isinstance(record, dict):
        return False
    if record.get("programme_credit") != "AWARDED":
        return False
    return decision_supports(record, "accepted", target_id)


def assert_programme_credit(credit: str, decision_records=None, target_id: str | None = None) -> str:
    """Refuse programme credit that tooling would be awarding on its own authority."""
    if credit not in PROGRAMME_CREDITS:
        raise EvidenceStateError(
            f"unknown programme credit {credit!r}; expected one of {', '.join(PROGRAMME_CREDITS)}"
        )
    if credit in TOOL_CREDITS:
        return credit
    records = list(decision_records or [])
    if target_id and any(credit_supported(record, target_id) for record in records):
        return credit
    raise EvidenceStateError(
        "refusing to award programme credit without an explicit owner or reviewer decision record"
    )


def _cited_actor(record: dict, target_id: str) -> bool:
    if record.get("authority") not in {"owner", "reviewer"}:
        return False
    decided_by = record.get("decided_by")
    citation = record.get("citation")
    if not isinstance(decided_by, str) or not decided_by.strip():
        return False
    if not isinstance(citation, str) or not citation.strip():
        return False
    targets = record.get("target_ids")
    return isinstance(targets, list) and target_id in targets


def authorization_record_supports(record: dict, target_id: str) -> bool:
    """Return whether ``record`` explicitly authorizes ``target_id``.

    Only ``authorization_status`` is read. ``evidence_status``, the evidence
    ladder, and ``state`` are ignored, so an evidence decision cannot authorize.
    """
    if not isinstance(record, dict):
        return False
    if record.get("authorization_status") != AUTHORIZATION_GRANTED:
        return False
    return _cited_actor(record, target_id)


def assert_authorization_status(
    authorization_status: str,
    decision_records=None,
    target_id: str | None = None,
) -> str:
    """Allow the default, or ``AUTHORIZED`` when an authorization record cites it.

    The evidence ladder is not an input. Callers must pass the
    ``authorization_status`` column alone.
    """
    if authorization_status == DEFAULT_AUTHORIZATION_STATUS:
        return authorization_status
    records = list(decision_records or [])
    if (
        authorization_status == AUTHORIZATION_GRANTED
        and target_id
        and any(authorization_record_supports(record, target_id) for record in records)
    ):
        return authorization_status
    raise EvidenceStateError(
        f"authorization_status {authorization_status!r} is not the default "
        f"{DEFAULT_AUTHORIZATION_STATUS} and no authorization record exists"
    )


def transition(current: str, new: str, decision_record: dict | None = None, target_id: str | None = None) -> str:
    """Move from ``current`` to ``new`` or raise :class:`EvidenceStateError`.

    The error names an illegal edge directly. When the edge is legal and the
    destination requires a human decision, a missing or non-citing decision
    record is also refused. Tool-settable destinations do not require a
    decision record.
    """
    if current not in STATES:
        raise EvidenceStateError(f"unknown evidence state {current!r}")
    if new not in STATES:
        raise EvidenceStateError(f"unknown evidence state {new!r}")
    if new not in TRANSITIONS[current]:
        raise EvidenceStateError(f"illegal evidence-state transition: {current} -> {new}")
    if new in DECISION_REQUIRED:
        if target_id is None or not decision_supports(decision_record or {}, new, target_id):
            raise EvidenceStateError(
                f"refusing to set evidence state {new!r} without an explicit "
                "owner or reviewer decision record"
            )
    return new
