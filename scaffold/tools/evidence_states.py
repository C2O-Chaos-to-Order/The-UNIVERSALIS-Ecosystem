"""Ordered evidence states and the separate execution-outcome axis.

Two vocabularies live here and must never be mixed:

``STATES`` -- the governing Plan's evidence ladder, in Plan order:
``proposed``, ``documented``, ``implemented``, ``tested``, ``verified``,
``independently_reproduced``, ``validated``, ``authorized``. A state records
how far the *evidence* for a claim has been established.

``EXECUTION_OUTCOMES`` -- what a run actually did: ``not_executed``,
``executed``, ``failed``, ``incomplete``. This is not an evidence state and
must never be read as one. A run that failed can legitimately sit at
``evidence_status: documented``: what is documented is that the run failed.

Tooling may set only the states that record what a program did on its own
authority: ``proposed``, ``documented``, ``implemented``, ``tested``.
``verified``, ``independently_reproduced``, ``validated`` and ``authorized``
stay unset unless an explicit owner or reviewer decision record cites them.

``authorization_status`` is a third, separate column. Its default is
``NOT_AUTHORIZED``. Nothing in this module copies it from ``evidence_status``
or from the ladder, and ``evidence_status: authorized`` neither sets nor
implies ``authorization_status: AUTHORIZED``. This module does not award
programme credit and does not decide that a claim is true.
"""

from __future__ import annotations

from typing import Iterable

# The governing Plan's evidence ladder, in Plan order (Plan section 7).
STATES = (
    "proposed",
    "documented",
    "implemented",
    "tested",
    "verified",
    "independently_reproduced",
    "validated",
    "authorized",
)

# States a program may record from its own run. These do not require a human
# decision. They are still evidence claims, not execution claims.
TOOL_SETTABLE = frozenset({"proposed", "documented", "implemented", "tested"})

# States entered only through an explicit owner or reviewer decision record.
DECISION_REQUIRED = frozenset(
    {"verified", "independently_reproduced", "validated", "authorized"}
)

# What the run actually did. A separate axis from ``STATES``.
# ``failed`` and ``incomplete`` are execution outcomes. They are not evidence
# states, and a failed run is documented at whatever evidence state its record
# has actually reached.
EXECUTION_OUTCOMES = ("not_executed", "executed", "failed", "incomplete")
DEFAULT_EXECUTION_OUTCOME = "not_executed"

# Guard the separation at import time so the two vocabularies cannot drift
# into a shared slug without this module failing loudly.
_OVERLAP = set(STATES) & set(EXECUTION_OUTCOMES)
if _OVERLAP:  # pragma: no cover - defensive invariant
    raise RuntimeError(
        "evidence states and execution outcomes must not share a value: "
        + ", ".join(sorted(_OVERLAP))
    )

PROGRAMME_CREDITS = (
    "NONE",
    "CANDIDATE_PENDING_OWNER_REVIEW",
    "AWARDED",
)

TOOL_CREDITS = frozenset({"NONE", "CANDIDATE_PENDING_OWNER_REVIEW"})

# Separate from both ladders. The default is the only value tooling may
# record. ``AUTHORIZED`` requires an authorization record that says so.
DEFAULT_AUTHORIZATION_STATUS = "NOT_AUTHORIZED"
AUTHORIZATION_GRANTED = "AUTHORIZED"

# Forward edges only, one step at a time. A later state never rewrites an
# earlier one: there is no demotion edge, so a record that reached ``tested``
# cannot be moved back to ``implemented``, and a failed run is recorded as an
# execution outcome on the run, not by demoting the evidence state.
TRANSITIONS = {
    "proposed": frozenset({"documented"}),
    "documented": frozenset({"implemented"}),
    "implemented": frozenset({"tested"}),
    "tested": frozenset({"verified"}),
    "verified": frozenset({"independently_reproduced"}),
    "independently_reproduced": frozenset({"validated"}),
    "validated": frozenset({"authorized"}),
    "authorized": frozenset(),
}

# Rank among the decision-required states. A higher decision covers a lower
# one for the targets it cites. A decision never covers an execution outcome.
_DECISION_RANK = {
    "verified": 0,
    "independently_reproduced": 1,
    "validated": 2,
    "authorized": 3,
}


class EvidenceStateError(ValueError):
    """An evidence state or programme credit was refused."""


def ladder_index(state: str) -> int:
    """Return the canonical position of ``state`` in :data:`STATES`."""
    try:
        return STATES.index(state)
    except ValueError as exc:
        raise EvidenceStateError(f"unknown evidence state {state!r}") from exc


def next_state(state: str) -> str | None:
    """Return the single forward edge from ``state``, or ``None`` at the top."""
    ladder_index(state)
    edges = TRANSITIONS[state]
    return next(iter(edges)) if edges else None


def is_forward_step(current: str, new: str) -> bool:
    """Return whether ``current -> new`` is a legal one-step advance."""
    if current not in STATES or new not in STATES:
        return False
    return new in TRANSITIONS[current]


def tooling_set(state: str) -> str:
    """Return ``state`` when tooling is allowed to set it.

    ``verified``, ``independently_reproduced``, ``validated`` and
    ``authorized`` are refused here even if a decision record is supplied.
    Those states are entered through :func:`transition`, which checks the
    decision. Execution outcomes are refused: they are not evidence states.
    """
    if state in EXECUTION_OUTCOMES:
        raise EvidenceStateError(
            f"{state!r} is an execution outcome, not an evidence state; "
            f"execution outcomes are {', '.join(EXECUTION_OUTCOMES)} and are "
            "recorded on the execution_outcome field"
        )
    if state not in TOOL_SETTABLE:
        raise EvidenceStateError(
            f"tooling cannot set evidence state {state!r}; "
            + ", ".join(STATES[index] for index in range(len(STATES)) if STATES[index] in DECISION_REQUIRED)
            + " require an explicit owner or reviewer decision record"
        )
    return state


def cross_axis_problems(record: object, label: str) -> list[str]:
    """Report a value carried on the wrong axis.

    ``execution_outcome`` must not hold an evidence state, and
    ``evidence_status`` must not hold an execution outcome. Both directions
    are refused so a run outcome can never be read as an evidence claim.
    """
    if not isinstance(record, dict):
        return []
    problems: list[str] = []
    outcome = record.get("execution_outcome")
    if isinstance(outcome, str) and outcome in STATES:
        problems.append(
            f"EXECUTION_OUTCOME_CONFUSED: {label} execution_outcome {outcome!r} "
            "is an evidence state; execution outcomes are "
            f"{', '.join(EXECUTION_OUTCOMES)} on a separate axis"
        )
    evidence = record.get("evidence_status")
    if isinstance(evidence, str) and evidence in EXECUTION_OUTCOMES:
        problems.append(
            f"EXECUTION_OUTCOME_CONFUSED: {label} evidence_status {evidence!r} "
            "is an execution outcome; evidence states are "
            f"{', '.join(STATES)} and a run outcome must not replace one"
        )
    return problems


def _decision_rank(state: str) -> int:
    if state not in _DECISION_RANK:
        raise EvidenceStateError(
            "decision state must be one of "
            + ", ".join(state_name for state_name in STATES if state_name in _DECISION_RANK)
            + f", not {state!r}"
        )
    return _DECISION_RANK[state]


def decision_supports(record: dict, state: str, target_id: str) -> bool:
    """Return whether ``record`` cites ``target_id`` for ``state`` or a higher decision state.

    A decision of ``authorized`` covers ``validated``,
    ``independently_reproduced`` and ``verified`` for the cited targets. A
    decision of ``validated`` covers ``independently_reproduced`` and
    ``verified``, and so on. The cover is not programme credit and it is not a
    check that the cited person exists. It is also not an authorization: the
    decision must set ``authorization_status`` for that.
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
    otherwise. Authorization is not an input here and is never inferred.
    """
    if state in EXECUTION_OUTCOMES:
        raise EvidenceStateError(
            f"{state!r} is an execution outcome, not an evidence state; "
            "record it on execution_outcome"
        )
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

    The decision must be ``validated`` or ``authorized`` and must set
    ``programme_credit`` to ``AWARDED``. Reaching an evidence state does not by
    itself award credit.
    """
    if not isinstance(record, dict):
        return False
    if record.get("programme_credit") != "AWARDED":
        return False
    return decision_supports(record, "validated", target_id)


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
    ladder, and ``state`` are ignored, so an evidence decision -- including an
    evidence decision whose own state is ``authorized`` -- cannot authorize.
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
    ``authorization_status`` column alone. ``evidence_status: authorized`` is
    not evidence of authorization and raises nothing here: this function never
    sees it.
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


def transition(
    current: str,
    new: str,
    decision_record: dict | None = None,
    target_id: str | None = None,
) -> str:
    """Move from ``current`` to ``new`` or raise :class:`EvidenceStateError`.

    Only the single forward edge is legal. The error names an illegal edge
    directly. When the edge is legal and the destination requires a human
    decision, a missing or non-citing decision record is also refused.
    Tool-settable destinations do not require a decision record.
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


def assert_outcome_known(outcome: object) -> str:
    """Return ``outcome`` when it is one of :data:`EXECUTION_OUTCOMES`."""
    if outcome not in EXECUTION_OUTCOMES:
        raise EvidenceStateError(
            f"unknown execution outcome {outcome!r}; expected one of "
            f"{', '.join(EXECUTION_OUTCOMES)}"
        )
    return outcome  # type: ignore[return-value]


def iter_states() -> Iterable[str]:
    """Iterate the evidence ladder in Plan order."""
    return iter(STATES)
