"""Trajectory guarantees and forward invariance (ULC-01-05).

A bound of the form ``e_n <= eps * sum(L^k)`` is derived under premises: a
residual bounded by ``eps`` over a domain, and an ``L``-Lipschitz map on that
domain. The research package ``UNI-RP-001`` (Emerald tablet clause 01.E05)
found that such a bound can be *numerically satisfied while the premise that
justifies it has already failed*: at step 1 the error equalled the bound, the
point was still inside the domain, and the residual had already exceeded
``eps``. The bound first reported trouble one step later.

That makes a bound alone unsafe as an engineering guarantee. This module adds
the missing condition: a guarantee about a trajectory is only issued when the
declared domain is forward invariant along the observed trajectory and the
per-step premise holds at every step up to the one being certified.

Scope of this module:

- It checks a *given* trajectory. It does not prove a domain is forward
  invariant in general; it checks the steps it was given and says so.
- It issues no authorization and awards no credit. A guaranteed trajectory is
  a statement about a premise holding on the observed steps, nothing more.
- A refusal is not an error to be silenced. The refusal carries the step and
  the reason so the record can show what failed.

Reference: ULC-01-05, ``research-packages/UNI-RP-001`` in
Research-for-the-UNIVERSALIS-Ecosystem, simulation SIM-003.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Iterable, Sequence

from universalis.errors import DomainNotForwardInvariant


@dataclass(frozen=True)
class StepFact:
    """What was observed at one step of a trajectory.

    ``inside_domain`` and ``premise_holds`` are recorded by the caller from its
    own evaluation. This module does not infer them from the error size: the
    whole point of the finding is that a small error does not imply a holding
    premise.
    """

    n: int
    true_error: Fraction
    claimed_bound: Fraction
    inside_domain: bool
    premise_holds: bool
    residual: Fraction | None = None


@dataclass(frozen=True)
class TrajectoryGuarantee:
    """The result of a successful check.

    ``steps_checked`` is stated explicitly so a guarantee over three steps is
    not read as a guarantee over the whole trajectory.
    """

    steps_checked: int
    last_step: int
    #: True only if the error equalled a strictly positive bound at some step.
    #: A zero error against a zero bound is vacuous and does not count.
    bound_attained: bool
    premise_held_at_every_step: bool

    def __post_init__(self) -> None:
        if self.steps_checked <= 0:
            raise ValueError("a guarantee must cover at least one step")
        if not self.premise_held_at_every_step:
            # Belt and braces: a guarantee object must never be constructible
            # for a trajectory whose premise failed.
            raise DomainNotForwardInvariant(
                step=self.last_step,
                reason="premise did not hold at every step, so no guarantee is issued",
            )


def _as_fraction(value) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        raise TypeError("a boolean is not a quantity")
    return Fraction(value)


def certify_trajectory(
    steps: Iterable[StepFact],
    *,
    require_forward_invariance: bool = True,
) -> TrajectoryGuarantee:
    """Return a guarantee, or refuse.

    Refusal conditions, in order of what is most informative to report:

    1. The domain was escaped at some step (``inside_domain`` false) while
       forward invariance was required.
    2. The premise failed at some step (``premise_holds`` false).
    3. The true error exceeded the claimed bound at some step.

    Refusal on (1) or (2) happens even when the bound is numerically satisfied,
    which is the behaviour the research found missing.
    """
    ordered = sorted((s for s in steps), key=lambda s: s.n)
    if not ordered:
        raise ValueError("no trajectory steps supplied; nothing to certify")

    previous_n = None
    premise_held = True
    bound_attained = False

    for step in ordered:
        if previous_n is not None and step.n != previous_n + 1:
            raise ValueError(
                f"trajectory steps are not contiguous: {previous_n} then {step.n}"
            )
        previous_n = step.n

        error = _as_fraction(step.true_error)
        bound = _as_fraction(step.claimed_bound)

        if error > bound:
            raise DomainNotForwardInvariant(
                step=step.n,
                reason=(
                    f"true error {error} exceeds the claimed bound {bound}"
                ),
            )

        if require_forward_invariance and not step.inside_domain:
            raise DomainNotForwardInvariant(
                step=step.n,
                reason=(
                    "the state left the declared domain, so a bound derived on that "
                    "domain no longer applies even if the error still looks small"
                ),
            )

        if not step.premise_holds:
            premise_held = False
            raise DomainNotForwardInvariant(
                step=step.n,
                reason=(
                    "the per-step premise failed; a bound whose premise has failed is "
                    "vacuous even where the inequality still holds"
                ),
            )

        # Attainment is only evidence of sharpness where the bound is doing
        # real work. At step 0 with a zero error the equality is vacuous: 0 == 0
        # says nothing about how tight the bound is. Counting that would let a
        # trivially satisfied trajectory be reported as sharp.
        if error == bound and bound > 0:
            bound_attained = True

    return TrajectoryGuarantee(
        steps_checked=len(ordered),
        last_step=ordered[-1].n,
        bound_attained=bound_attained,
        premise_held_at_every_step=premise_held,
    )


def forward_invariance_report(
    path: Sequence[Sequence[Fraction]],
    in_domain: Callable[[Sequence[Fraction]], bool],
) -> dict:
    """Check whether an observed path stays inside a declared domain.

    This reports what it saw. It does not claim the domain is invariant for
    every starting point, which would need an argument this function cannot
    make: it only has one trajectory.
    """
    escaped_at = None
    for index, point in enumerate(path):
        if not in_domain(point):
            escaped_at = index
            break
    return {
        "points_checked": len(path),
        "escaped": escaped_at is not None,
        "first_step_outside_domain": escaped_at,
        "scope": (
            "Observed path only. Staying inside for this path does not show the "
            "domain is invariant for other starting points."
        ),
    }
