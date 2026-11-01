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

WHAT THIS MODULE DOES NOT DO (read this before relying on a guarantee)
======================================================================

``premise_holds`` and ``inside_domain`` are **CALLER-SUPPLIED ASSERTIONS**.
They are facts the caller hands in about its own evaluation. Nothing in this
module observes the modelled system, re-runs a simulation, or measures a
residual. The module therefore **cannot detect a caller who lies**.

As a partial mitigation, ``residual`` and ``epsilon`` may be supplied instead
of ``premise_holds``; the premise is then computed here as
``residual <= epsilon`` (see ``StepFact``) and the caller does not get to state
a boolean that contradicts its own numbers. This removes one class of mistake —
a wrong boolean — but not the class it exists upstream of: **the numbers
themselves are still caller-supplied**, so a caller who reports a residual it
did not measure is not detected by anything here.

Consequently a ``TrajectoryGuarantee`` is a statement **about the facts as
supplied**, not an independently established property of the underlying
system. It is not a proof, not a certificate, and not scientific validation.

Scope of this module:

- It checks a *given* trajectory. It does not prove a domain is forward
  invariant in general; it checks the steps it was given and says so.
- It issues no authorization and awards no credit. A guaranteed trajectory is
  a statement about a premise holding on the observed steps, nothing more.
- A refusal is not an error to be silenced. The refusal carries the step and
  the reason so the record can show what failed.

Reference: ULC-01-05, ``research-packages/UNI-RP-001`` in
Research-for-the-UNIVERSALIS-Ecosystem, simulation SIM-003. The artifacts
``results/SIM-003.json`` and ``results/trajectories/SIM-003_trajectory.json``
are driven against this module by ``test_sim003_artifacts.py``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Iterable, Sequence

from universalis.errors import DomainNotForwardInvariant

#: Types accepted as a quantity, in addition to ``Fraction`` itself. A ``bool``
#: is excluded deliberately although it is a subclass of ``int``: ``True`` is
#: not a magnitude. A string is excluded although ``Fraction("1/4")`` parses:
#: a caller holding a string must say what it means by parsing it first.
_QUANTITY_TYPES = (int, Fraction, float)


def _as_quantity(value, field: str) -> Fraction:
    """Return ``value`` as an exact ``Fraction``, or refuse it as not a quantity."""
    if isinstance(value, bool) or not isinstance(value, _QUANTITY_TYPES):
        raise TypeError(
            f"{field} must be a real number (int, Fraction, or float); "
            f"got {type(value).__name__}. A boolean and a string are not quantities."
        )
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{field} must be finite; got {value!r}")
    # Fraction(float) is the exact binary value of the float, not its decimal
    # reading. Exactness is preserved; callers wanting decimal semantics must
    # pass a Fraction or an int.
    return value if isinstance(value, Fraction) else Fraction(value)


def _as_magnitude(value, field: str) -> Fraction:
    """A magnitude or a bound: a quantity that is not negative.

    An error magnitude, a claimed bound, a residual, and an epsilon are all
    non-negative by construction. A negative one is not a small number that
    happens to be below zero; it means the caller has confused a signed
    difference with a magnitude, or a bound with a slack.
    """
    quantity = _as_quantity(value, field)
    if quantity < 0:
        raise ValueError(f"{field} must be non-negative; got {quantity}")
    return quantity


@dataclass(frozen=True)
class StepFact:
    """What was observed at one step of a trajectory.

    The caller supplies the observations. Two ways of stating the premise are
    supported, and they are **not** of equal assurance:

    ``residual`` and ``epsilon`` supplied (HIGHER assurance)
        The premise is computed here as ``residual <= epsilon``. The caller
        cannot state a boolean that disagrees with its own numbers; if it
        supplies both and they disagree, construction is refused.

    ``premise_holds`` supplied (LOWER assurance)
        The premise is asserted by the caller and taken at face value. This
        path exists for callers that do not have a residual, and it is the path
        whose correctness this module cannot check at all.

    A caller may supply both, but only if they agree. There is no silent
    preference for one over the other.

    ``inside_domain`` is **always** a caller-supplied assertion. This module has
    no access to the domain membership test and does not attempt to infer it
    from the error size: the whole point of the finding is that a small error
    does not imply a point stayed inside the domain.

    Values refused at construction, with ``TypeError`` for a wrong type and
    ``ValueError`` for a wrong value:

    - ``n`` must be a non-negative ``int`` and not a ``bool``.
    - ``inside_domain`` and ``premise_holds`` must be real ``bool`` values.
      ``1``, ``0``, ``"yes"``, and ``"false"`` are refused; a truthy string is
      not a fact about the world.
    - ``true_error``, ``claimed_bound``, ``residual``, and ``epsilon`` must be
      ``int``, ``Fraction``, or finite ``float``, and must not be negative. NaN
      and infinity are refused rather than failing later inside ``Fraction``.
    - ``residual`` and ``epsilon`` are supplied together or not at all. One
      without the other is an incomplete premise, not a premise.

    Deliberate choice at zero: ``epsilon == 0`` is **accepted**. With
    non-negative residuals it makes the premise ``residual == 0`` — strict, and
    satisfiable, but not vacuous. It is not an error to demand an exact zero
    residual. ``epsilon < 0`` is **refused**, because ``residual <= eps`` would
    then be unsatisfiable for every non-negative residual; that is a malformed
    epsilon, not a trajectory whose premise failed, and reporting it as a
    premise failure would misattribute a defect in the input to the model.
    """

    n: int
    true_error: Fraction
    claimed_bound: Fraction
    inside_domain: bool
    premise_holds: bool | None = None
    residual: Fraction | None = None
    epsilon: Fraction | None = None
    #: The boolean exactly as supplied, before any computation. ``None`` when
    #: the caller supplied only residual and epsilon. Kept so that
    #: ``premise_basis`` reports what actually happened rather than inferring it
    #: from the normalised field.
    asserted_premise_holds: bool | None = None

    def __post_init__(self) -> None:
        if isinstance(self.n, bool) or not isinstance(self.n, int):
            raise TypeError(
                f"n must be an int step index; got {type(self.n).__name__}. "
                "A float such as 1.0 is not a step index."
            )
        if self.n < 0:
            raise ValueError(f"n must be non-negative; got {self.n}")

        if not isinstance(self.inside_domain, bool):
            raise TypeError(
                "inside_domain must be a bool; got "
                f"{type(self.inside_domain).__name__}. A truthy value is not an assertion."
            )
        if self.premise_holds is not None and not isinstance(self.premise_holds, bool):
            raise TypeError(
                "premise_holds must be a bool when supplied; got "
                f"{type(self.premise_holds).__name__}. Supply residual and epsilon "
                "to have the premise computed instead of asserting it."
            )

        error = _as_magnitude(self.true_error, "true_error")
        bound = _as_magnitude(self.claimed_bound, "claimed_bound")
        residual = (
            None if self.residual is None else _as_magnitude(self.residual, "residual")
        )
        epsilon = (
            None if self.epsilon is None else _as_magnitude(self.epsilon, "epsilon")
        )

        if (residual is None) != (epsilon is None):
            raise ValueError(
                "residual and epsilon must be supplied together: a residual "
                "without its epsilon states no premise, and an epsilon without a "
                "residual cannot be evaluated"
            )

        computed = None if residual is None else residual <= epsilon

        if computed is None and self.premise_holds is None:
            raise ValueError(
                "a step must state its premise: supply premise_holds, or supply "
                "residual and epsilon so it can be computed"
            )

        if computed is not None and self.premise_holds is not None:
            if computed != self.premise_holds:
                raise ValueError(
                    "the supplied premise_holds contradicts the supplied residual "
                    f"and epsilon: residual {residual} <= epsilon {epsilon} is "
                    f"{computed}, but premise_holds is {self.premise_holds}. "
                    "This module will not choose one of the two for you."
                )

        # Normalise to exact Fractions so later comparisons are exact even when
        # the caller passed floats.
        object.__setattr__(self, "asserted_premise_holds", self.premise_holds)
        object.__setattr__(self, "true_error", error)
        object.__setattr__(self, "claimed_bound", bound)
        object.__setattr__(self, "residual", residual)
        object.__setattr__(self, "epsilon", epsilon)
        object.__setattr__(self, "premise_holds", computed if computed is not None else self.premise_holds)

    @property
    def premise_basis(self) -> str:
        """How ``premise_holds`` came to be. Not a statement of its truth.

        ``computed_and_asserted`` means the caller supplied both the boolean and
        the numbers and they agreed. It is reported separately rather than
        folded into the computed case, because the caller did assert a premise
        and a reader is entitled to know that.
        """
        if self.residual is not None:
            if self.asserted_premise_holds is not None:
                return "computed_and_asserted"
            return "computed_from_residual_and_epsilon"
        return "caller_asserted"


#: Fixed scope statements carried on every guarantee this module issues. They
#: are part of the result rather than only of the documentation, so a reader of
#: the object sees them.
SCOPE_LIMITATION = (
    "Checks only the steps supplied. It does not prove the declared domain is "
    "forward invariant for other starting points, other iterations, or a longer "
    "run of the same trajectory."
)
CALLER_FACT_LIMITATION = (
    "The per-step facts are caller-supplied: inside_domain always, and the "
    "premise either asserted by the caller or computed from a caller-supplied "
    "residual and epsilon. The module cannot detect an incorrect or dishonest "
    "caller, so this guarantee is a statement about the facts as supplied, not "
    "an independently established property of the modelled system."
)
NO_AUTHORITY_LIMITATION = (
    "This guarantee carries no authorization, awards no credit, and is not "
    "scientific validation or independent verification."
)

FORWARD_INVARIANCE_WAIVER = (
    "FORWARD INVARIANCE WAS NOT ENFORCED: the check was called with "
    "require_forward_invariance=False, so a step outside the declared domain "
    "would not have been refused. A bound derived on that domain is void on the "
    "steps that escaped it, and this result cannot be read as covering them."
)


@dataclass(frozen=True)
class TrajectoryGuarantee:
    """The result of a successful check.

    Every field is mandatory. That is deliberate: a guarantee is only useful if
    it states how far it reaches (``steps_checked``), on what basis
    (``premise_basis``), and what it waived (``forward_invariance_enforced``,
    ``waivers``, ``limitations``). A waived guarantee therefore cannot be
    mistaken for a full one by a program that inspects the object.

    ``steps_checked`` is stated explicitly so a guarantee over three steps is
    not read as a guarantee over the whole trajectory.
    """

    steps_checked: int
    last_step: int
    #: True only if the error equalled a strictly positive bound at some step.
    #: A zero error against a zero bound is vacuous and does not count.
    bound_attained: bool
    premise_held_at_every_step: bool
    #: False when the caller waived the forward-invariance condition. A waived
    #: guarantee must name its waiver in ``waivers`` and in ``limitations``.
    forward_invariance_enforced: bool
    #: Names each condition that was not enforced. Empty for a full guarantee.
    waivers: tuple[str, ...]
    #: Human-readable limits on what this guarantee covers, including the
    #: waiver text when one applies.
    limitations: tuple[str, ...]
    #: Records the assurance basis of the premise across the steps:
    #: ``"computed_from_residual_and_epsilon"``, ``"caller_asserted"``,
    #: ``"computed_and_asserted"``, or ``"mixed"`` across steps.
    premise_basis: str

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
        if self.forward_invariance_enforced:
            if self.waivers:
                raise ValueError(
                    "a guarantee with forward invariance enforced cannot name a waiver"
                )
        else:
            if FORWARD_INVARIANCE_WAIVER not in self.waivers:
                raise ValueError(
                    "a guarantee that waived forward invariance must name that "
                    "waiver in waivers; otherwise the result does not say what it "
                    "did not check"
                )
            if FORWARD_INVARIANCE_WAIVER not in self.limitations:
                raise ValueError(
                    "a guarantee that waived forward invariance must carry the "
                    "waiver text in limitations; otherwise a reader of the object "
                    "cannot see it"
                )


def certify_trajectory(
    steps: Iterable[StepFact],
    *,
    require_forward_invariance: bool = True,
) -> TrajectoryGuarantee:
    """Return a guarantee, or refuse.

    Every step is a ``StepFact``, so every step has already been validated at
    construction. ``certify_trajectory`` additionally refuses a value that is
    not a ``StepFact`` rather than duck-typing it, so a lookalike object cannot
    bypass those checks.

    **Refusal order.** Within the first step at which anything fails, the
    conditions are tested in this order:

    1. The state is outside the declared domain (``inside_domain`` false), when
       forward invariance is required.
    2. The premise failed (``premise_holds`` false).
    3. The true error exceeded the claimed bound.

    The rationale for that order is that it runs from the widest invalidation to
    the narrowest. A point outside the domain voids the scope in which *any*
    bound was derived, so it explains the other two rather than being explained
    by them. A failed premise voids the justification of the bound while the
    inequality may still hold — the case this module exists for. A violated
    bound is the least informative of the three: it is the only one visible
    without this module, and a reader told only "error exceeds bound" would
    conclude the bound is merely optimistic, when in fact it may never have
    applied.

    Refusal on (1) or (2) happens even when the bound is numerically satisfied,
    which is the behaviour the research found missing.

    The earliest failing step is always the one reported: a later failure does
    not displace an earlier one.
    """
    supplied = list(steps)
    if not supplied:
        raise ValueError("no trajectory steps supplied; nothing to certify")

    # Type-check before sorting: sorting reads ``.n``, so a non-StepFact would
    # raise AttributeError here and report the wrong cause. Found by probing
    # this ordering directly rather than assuming it.
    for step in supplied:
        if not isinstance(step, StepFact):
            raise TypeError(
                "certify_trajectory accepts StepFact instances only; got "
                f"{type(step).__name__}. A lookalike object would bypass the "
                "validation StepFact performs."
            )

    ordered = sorted(supplied, key=lambda s: s.n)

    # Structural checks run over the whole trajectory before any semantic
    # refusal is raised. Otherwise a malformed later step would be hidden behind
    # a semantic failure at an earlier step, and whether the malformed input was
    # reported would depend on the order of the data.
    previous_n = None
    for step in ordered:
        if previous_n is not None and step.n != previous_n + 1:
            raise ValueError(
                f"trajectory steps are not contiguous: {previous_n} then {step.n}"
            )
        previous_n = step.n

    bound_attained = False
    bases = set()

    for step in ordered:
        bases.add(step.premise_basis)
        error, bound = step.true_error, step.claimed_bound

        if require_forward_invariance and not step.inside_domain:
            raise DomainNotForwardInvariant(
                step=step.n,
                reason=(
                    "the state left the declared domain, so a bound derived on that "
                    "domain no longer applies even if the error still looks small"
                ),
            )

        if not step.premise_holds:
            raise DomainNotForwardInvariant(
                step=step.n,
                reason=(
                    "the per-step premise failed; a bound whose premise has failed is "
                    "vacuous even where the inequality still holds"
                ),
            )

        if error > bound:
            raise DomainNotForwardInvariant(
                step=step.n,
                reason=(
                    f"true error {error} exceeds the claimed bound {bound}"
                ),
            )

        # Attainment is only evidence of sharpness where the bound is doing
        # real work. At step 0 with a zero error the equality is vacuous: 0 == 0
        # says nothing about how tight the bound is. Counting that would let a
        # trivially satisfied trajectory be reported as sharp.
        if error == bound and bound > 0:
            bound_attained = True

    if len(bases) == 1:
        premise_basis = bases.pop()
    else:
        premise_basis = "mixed"

    limitations = [SCOPE_LIMITATION, CALLER_FACT_LIMITATION, NO_AUTHORITY_LIMITATION]
    if require_forward_invariance:
        waivers: tuple[str, ...] = ()
    else:
        waivers = (FORWARD_INVARIANCE_WAIVER,)
        limitations.append(FORWARD_INVARIANCE_WAIVER)

    return TrajectoryGuarantee(
        steps_checked=len(ordered),
        last_step=ordered[-1].n,
        bound_attained=bound_attained,
        premise_held_at_every_step=True,
        forward_invariance_enforced=require_forward_invariance,
        waivers=waivers,
        limitations=tuple(limitations),
        premise_basis=premise_basis,
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
