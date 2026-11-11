"""ULC-01-05: a bound is not a guarantee on a domain iteration escapes.

These tests pin the behaviour the UNI-RP-001 research found missing. The
central case reproduces SIM-003: at step 1 the error equals the bound, the
point is inside the domain, the bound is satisfied, and the residual has
already exceeded the premise. A check that only compares error to bound passes
it. This one must refuse.

The exact artifacts are driven separately in ``test_sim003_artifacts.py``; this
module uses constructed steps so boundary and malformed cases can be stated
precisely.
"""

import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from universalis.errors import DomainNotForwardInvariant
from universalis.trajectory import (
    CALLER_FACT_LIMITATION,
    FORWARD_INVARIANCE_WAIVER,
    SCOPE_LIMITATION,
    StepFact,
    TrajectoryGuarantee,
    certify_trajectory,
    forward_invariance_report,
)

EPS = Fraction(1)


def step(n, error, bound, inside=True, premise=True, residual=None, epsilon=EPS):
    """A step stating its premise as a caller assertion.

    ``residual`` is documentation of the recorded residual and is paired with
    ``epsilon`` because the module refuses a residual on its own: a residual
    without its epsilon states no premise. The boolean is still the premise
    source here unless the caller leaves it out.
    """
    return StepFact(
        n=n,
        true_error=Fraction(error),
        claimed_bound=Fraction(bound),
        inside_domain=inside,
        premise_holds=premise,
        residual=None if residual is None else Fraction(residual),
        epsilon=None if residual is None else Fraction(epsilon),
    )


def computed_step(n, error, bound, residual, epsilon=EPS, inside=True):
    """A step whose premise is computed from residual and epsilon."""
    return StepFact(
        n=n,
        true_error=Fraction(error),
        claimed_bound=Fraction(bound),
        inside_domain=inside,
        residual=Fraction(residual),
        epsilon=Fraction(epsilon),
    )


class TheSimulationFindingTest(unittest.TestCase):
    """The exact shape of SIM-003."""

    def test_a_satisfied_bound_over_a_broken_premise_is_refused(self):
        # At n=1: error 1, bound 1, inside the domain, bound satisfied,
        # but the residual (4) has already exceeded eps (1).
        with self.assertRaises(DomainNotForwardInvariant) as caught:
            certify_trajectory([step(0, 0, 0), step(1, 1, 1, inside=True, premise=False, residual=4)])
        self.assertEqual(caught.exception.step, 1)
        self.assertIn("premise", caught.exception.reason)

    def test_the_bound_being_attained_does_not_rescue_the_guarantee(self):
        # error == bound at step 1 is exactly the seductive case: it looks ideal.
        with self.assertRaises(DomainNotForwardInvariant):
            certify_trajectory([step(1, 1, 1, premise=False)])

    def test_leaving_the_domain_is_refused_even_when_the_bound_still_holds(self):
        # This is the sharper half of the finding: a small error outside the
        # domain says nothing, because the bound was derived on the domain.
        with self.assertRaises(DomainNotForwardInvariant) as caught:
            certify_trajectory([step(1, 0, 5, inside=False, premise=True)])
        self.assertEqual(caught.exception.step, 1)
        self.assertIn("left the declared domain", caught.exception.reason)

    def test_the_real_sim_003_shape_is_refused_at_its_first_failure(self):
        trajectory = [
            step(0, 0, 0, inside=True, premise=True),
            step(1, 1, 1, inside=True, premise=False, residual=4),
            step(2, 7, 5, inside=False, premise=False, residual=64),
        ]
        with self.assertRaises(DomainNotForwardInvariant) as caught:
            certify_trajectory(trajectory)
        self.assertEqual(caught.exception.step, 1, "must report the first failure, not a later one")


class PremiseIsCallerSuppliedTest(unittest.TestCase):
    """Finding 1: the authority the module has is bounded and stated."""

    def test_the_limitation_travels_on_every_guarantee(self):
        # Not only in a docstring: a reader of the object must be told.
        guarantee = certify_trajectory([step(0, 0, 0)])
        self.assertIn(CALLER_FACT_LIMITATION, guarantee.limitations)
        self.assertIn(SCOPE_LIMITATION, guarantee.limitations)
        self.assertIn("cannot detect", CALLER_FACT_LIMITATION)

    def test_a_caller_assertion_is_marked_as_asserted(self):
        s = step(0, 0, 0, premise=True)
        self.assertEqual(s.premise_basis, "caller_asserted")
        guarantee = certify_trajectory([s])
        self.assertEqual(guarantee.premise_basis, "caller_asserted")

    def test_a_computed_premise_is_marked_as_computed(self):
        s = computed_step(0, 0, 0, residual=1)
        self.assertEqual(s.premise_basis, "computed_from_residual_and_epsilon")
        guarantee = certify_trajectory([s])
        self.assertEqual(guarantee.premise_basis, "computed_from_residual_and_epsilon")

    def test_supplying_both_and_agreeing_is_reported_as_both(self):
        # Found while self-reviewing: with both supplied and agreeing, the
        # earlier code reported "computed" and hid that the caller had also
        # asserted a premise. A reader is entitled to know which it was.
        s = StepFact(
            n=0, true_error=Fraction(0), claimed_bound=Fraction(0),
            inside_domain=True, premise_holds=True,
            residual=Fraction(0), epsilon=Fraction(1),
        )
        self.assertEqual(s.premise_basis, "computed_and_asserted")
        self.assertTrue(s.premise_holds)
        self.assertIs(s.asserted_premise_holds, True)

    def test_the_asserted_boolean_is_retained_before_normalisation(self):
        s = StepFact(
            n=0, true_error=Fraction(0), claimed_bound=Fraction(0),
            inside_domain=True, residual=Fraction(0), epsilon=Fraction(1),
        )
        self.assertIsNone(s.asserted_premise_holds)
        self.assertEqual(s.premise_basis, "computed_from_residual_and_epsilon")

    def test_a_mixed_trajectory_is_marked_mixed(self):
        guarantee = certify_trajectory([
            computed_step(0, 0, 0, residual=1),
            step(1, 1, 2, premise=True),
        ])
        self.assertEqual(guarantee.premise_basis, "mixed")

    def test_the_module_does_not_invent_inside_domain(self):
        # A small error outside the domain is still refused, which shows the
        # module reads the supplied flag rather than inferring from the error.
        with self.assertRaises(DomainNotForwardInvariant):
            certify_trajectory([step(0, 0, 0, inside=False)])
        # Conversely a large-but-in-bound error with inside_domain true passes,
        # so the module is not deriving inside_domain from the error either.
        self.assertEqual(certify_trajectory([step(0, 5, 6)]).steps_checked, 1)


class ComputedPremiseTest(unittest.TestCase):
    """Finding 2: premise validity derived from real quantities."""

    def test_a_residual_within_epsilon_computes_a_holding_premise(self):
        self.assertTrue(computed_step(0, 0, 0, residual=1).premise_holds)

    def test_a_residual_above_epsilon_computes_a_failed_premise(self):
        self.assertFalse(computed_step(0, 0, 0, residual=2).premise_holds)

    def test_the_computed_path_refuses_the_finding_without_a_boolean(self):
        # The caller never states premise_holds; the module reaches the finding.
        with self.assertRaises(DomainNotForwardInvariant) as caught:
            certify_trajectory([
                computed_step(0, 0, 0, residual=1),
                computed_step(1, 1, 1, residual=4),
            ])
        self.assertEqual(caught.exception.step, 1)
        self.assertIn("premise", caught.exception.reason)

    def test_boundary_residual_exactly_equal_to_epsilon_holds(self):
        # residual <= epsilon is inclusive: equality holds.
        self.assertTrue(computed_step(0, 0, 0, residual=1, epsilon=1).premise_holds)
        self.assertTrue(computed_step(0, 0, 0, residual=0, epsilon=0).premise_holds)

    def test_boundary_residual_one_unit_above_epsilon_fails(self):
        self.assertFalse(computed_step(0, 0, 0, residual=2, epsilon=1).premise_holds)

    def test_a_disagreement_between_boolean_and_numbers_is_refused(self):
        # Both supplied and contradictory: neither is silently preferred.
        with self.assertRaises(ValueError) as caught:
            StepFact(
                n=1, true_error=Fraction(1), claimed_bound=Fraction(1),
                inside_domain=True, premise_holds=True, residual=Fraction(4),
                epsilon=Fraction(1),
            )
        self.assertIn("contradicts", str(caught.exception))

    def test_a_disagreement_in_the_other_direction_is_also_refused(self):
        with self.assertRaises(ValueError):
            StepFact(
                n=1, true_error=Fraction(1), claimed_bound=Fraction(1),
                inside_domain=True, premise_holds=False, residual=Fraction(0),
                epsilon=Fraction(1),
            )

    def test_agreement_between_boolean_and_numbers_is_accepted(self):
        s = StepFact(
            n=1, true_error=Fraction(1), claimed_bound=Fraction(1),
            inside_domain=True, premise_holds=False, residual=Fraction(4),
            epsilon=Fraction(1),
        )
        self.assertFalse(s.premise_holds)

    def test_a_residual_without_epsilon_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            StepFact(n=0, true_error=Fraction(0), claimed_bound=Fraction(0),
                     inside_domain=True, residual=Fraction(1))
        self.assertIn("together", str(caught.exception))

    def test_an_epsilon_without_residual_is_refused(self):
        with self.assertRaises(ValueError):
            StepFact(n=0, true_error=Fraction(0), claimed_bound=Fraction(0),
                     inside_domain=True, epsilon=Fraction(1))

    def test_a_step_stating_no_premise_at_all_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            StepFact(n=0, true_error=Fraction(0), claimed_bound=Fraction(0),
                     inside_domain=True)
        self.assertIn("must state its premise", str(caught.exception))


class InvalidMagnitudesTest(unittest.TestCase):
    """Finding 3: negative, non-finite, and non-quantity inputs."""

    def test_a_negative_true_error_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            StepFact(n=0, true_error=Fraction(-5), claimed_bound=Fraction(10),
                     inside_domain=True, premise_holds=True)
        self.assertIn("non-negative", str(caught.exception))

    def test_a_negative_claimed_bound_is_refused(self):
        # Before this change a negative bound was accepted and then produced a
        # misleading "error exceeds bound" refusal. It is now refused as input.
        with self.assertRaises(ValueError) as caught:
            StepFact(n=0, true_error=Fraction(0), claimed_bound=Fraction(-5),
                     inside_domain=True, premise_holds=True)
        self.assertIn("claimed_bound", str(caught.exception))

    def test_a_negative_residual_is_refused(self):
        with self.assertRaises(ValueError):
            StepFact(n=0, true_error=Fraction(0), claimed_bound=Fraction(0),
                     inside_domain=True, residual=Fraction(-1), epsilon=Fraction(1))

    def test_a_negative_epsilon_is_refused(self):
        # Deliberate: residual <= eps would be unsatisfiable for a non-negative
        # residual, so a negative epsilon is a malformed input, not a premise
        # failure, and must not be reported as one.
        with self.assertRaises(ValueError) as caught:
            StepFact(n=0, true_error=Fraction(0), claimed_bound=Fraction(0),
                     inside_domain=True, residual=Fraction(0), epsilon=Fraction(-1))
        self.assertIn("epsilon", str(caught.exception))

    def test_a_zero_epsilon_is_accepted(self):
        s = StepFact(n=0, true_error=Fraction(0), claimed_bound=Fraction(0),
                     inside_domain=True, residual=Fraction(0), epsilon=Fraction(0))
        self.assertTrue(s.premise_holds)

    def test_a_nan_true_error_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            StepFact(n=0, true_error=float("nan"), claimed_bound=Fraction(1),
                     inside_domain=True, premise_holds=True)
        self.assertIn("finite", str(caught.exception))

    def test_an_infinite_claimed_bound_is_refused(self):
        # A bound of infinity would silently accept every error.
        for value in (float("inf"), float("-inf")):
            with self.assertRaises(ValueError):
                StepFact(n=0, true_error=Fraction(0), claimed_bound=value,
                         inside_domain=True, premise_holds=True)

    def test_a_boolean_is_not_a_quantity(self):
        for field in ("true_error", "claimed_bound"):
            kwargs = dict(n=0, true_error=Fraction(0), claimed_bound=Fraction(1),
                          inside_domain=True, premise_holds=True)
            kwargs[field] = True
            with self.assertRaises(TypeError) as caught:
                StepFact(**kwargs)
            self.assertIn(field, str(caught.exception))

    def test_a_boolean_residual_or_epsilon_is_refused(self):
        with self.assertRaises(TypeError):
            StepFact(n=0, true_error=Fraction(0), claimed_bound=Fraction(0),
                     inside_domain=True, residual=True, epsilon=Fraction(1))
        with self.assertRaises(TypeError):
            StepFact(n=0, true_error=Fraction(0), claimed_bound=Fraction(0),
                     inside_domain=True, residual=Fraction(0), epsilon=False)

    def test_a_zero_error_against_a_zero_bound_is_accepted(self):
        # Vacuous for sharpness, which bound_attained handles, but not an error.
        guarantee = certify_trajectory([step(0, 0, 0)])
        self.assertFalse(
            guarantee.bound_attained,
            "0 == 0 must not be reported as the bound being sharp",
        )

    def test_a_negative_zero_float_is_not_treated_as_negative(self):
        # -0.0 == 0, so it is a legal zero and must not be refused.
        self.assertEqual(certify_trajectory([
            StepFact(n=0, true_error=-0.0, claimed_bound=Fraction(0),
                     inside_domain=True, premise_holds=True)
        ]).steps_checked, 1)


class InvalidStepShapeTest(unittest.TestCase):
    """Finding 4: step indices and boolean fields."""

    def test_a_negative_step_index_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            StepFact(n=-1, true_error=Fraction(0), claimed_bound=Fraction(0),
                     inside_domain=True, premise_holds=True)
        self.assertIn("non-negative", str(caught.exception))

    def test_a_boolean_step_index_is_refused(self):
        with self.assertRaises(TypeError):
            StepFact(n=True, true_error=Fraction(0), claimed_bound=Fraction(0),
                     inside_domain=True, premise_holds=True)

    def test_a_float_step_index_is_refused(self):
        with self.assertRaises(TypeError) as caught:
            StepFact(n=1.0, true_error=Fraction(0), claimed_bound=Fraction(0),
                     inside_domain=True, premise_holds=True)
        self.assertIn("1.0", str(caught.exception))

    def test_a_string_step_index_is_refused(self):
        with self.assertRaises(TypeError):
            StepFact(n="1", true_error=Fraction(0), claimed_bound=Fraction(0),
                     inside_domain=True, premise_holds=True)

    def test_a_truthy_string_inside_domain_is_refused(self):
        with self.assertRaises(TypeError) as caught:
            StepFact(n=0, true_error=Fraction(0), claimed_bound=Fraction(0),
                     inside_domain="yes", premise_holds=True)
        self.assertIn("inside_domain", str(caught.exception))

    def test_an_integer_premise_holds_is_refused(self):
        # 1 is truthy but is not an assertion.
        for value in (1, 0):
            with self.assertRaises(TypeError):
                StepFact(n=0, true_error=Fraction(0), claimed_bound=Fraction(0),
                         inside_domain=True, premise_holds=value)

    def test_a_string_premise_holds_is_refused(self):
        with self.assertRaises(TypeError):
            StepFact(n=0, true_error=Fraction(0), claimed_bound=Fraction(0),
                     inside_domain=True, premise_holds="false")

    def test_a_non_numeric_true_error_is_refused(self):
        for value in ("abc", None, [1], {"x": 1}):
            with self.assertRaises(TypeError):
                StepFact(n=0, true_error=value, claimed_bound=Fraction(0),
                         inside_domain=True, premise_holds=True)

    def test_a_non_stepfact_is_refused_rather_than_duck_typed(self):
        for bad in ({"n": 0}, None, 7):
            with self.assertRaises(TypeError) as caught:
                certify_trajectory([bad])
            self.assertIn("StepFact", str(caught.exception))


class RefusalOrderTest(unittest.TestCase):
    """Finding 5: the documented order and the executed order must agree."""

    def test_all_three_violated_reports_the_domain_first(self):
        # Domain escape voids the scope in which any bound was derived, so it
        # is the widest invalidation and is reported first.
        with self.assertRaises(DomainNotForwardInvariant) as caught:
            certify_trajectory([
                StepFact(n=1, true_error=Fraction(99), claimed_bound=Fraction(1),
                         inside_domain=False, premise_holds=False),
            ])
        self.assertIn("left the declared domain", caught.exception.reason)

    def test_premise_and_bound_both_violated_reports_the_premise_first(self):
        # The case the module exists for: the premise is the more informative
        # of the two, because a bound violation alone suggests an optimistic
        # bound, when in fact the bound may never have applied.
        with self.assertRaises(DomainNotForwardInvariant) as caught:
            certify_trajectory([
                StepFact(n=1, true_error=Fraction(99), claimed_bound=Fraction(1),
                         inside_domain=True, premise_holds=False),
            ])
        self.assertIn("premise", caught.exception.reason)
        self.assertNotIn("exceeds", caught.exception.reason)

    def test_a_bound_violation_alone_is_reported_as_such(self):
        with self.assertRaises(DomainNotForwardInvariant) as caught:
            certify_trajectory([step(1, 99, 1)])
        self.assertIn("exceeds", caught.exception.reason)

    def test_order_holds_when_waived_too(self):
        # With invariance waived the domain check is not made, so the premise
        # becomes the first refusal rather than being skipped along with it.
        with self.assertRaises(DomainNotForwardInvariant) as caught:
            certify_trajectory(
                [StepFact(n=1, true_error=Fraction(99), claimed_bound=Fraction(1),
                          inside_domain=False, premise_holds=False)],
                require_forward_invariance=False,
            )
        self.assertIn("premise", caught.exception.reason)

    def test_the_earliest_failing_step_is_reported(self):
        # A later, more severe failure must not displace an earlier one.
        with self.assertRaises(DomainNotForwardInvariant) as caught:
            certify_trajectory([
                step(0, 0, 0),
                step(1, 1, 1, premise=False),
                step(2, 999, 1, inside=False),
            ])
        self.assertEqual(caught.exception.step, 1)


class WaiverIsVisibleTest(unittest.TestCase):
    """Finding 6: a waived guarantee must say so on the object."""

    def test_the_enforced_path_says_it_was_enforced(self):
        guarantee = certify_trajectory([step(0, 0, 0)])
        self.assertTrue(guarantee.forward_invariance_enforced)
        self.assertEqual(guarantee.waivers, ())
        self.assertNotIn(FORWARD_INVARIANCE_WAIVER, guarantee.limitations)

    def test_the_waived_path_says_it_was_not_enforced(self):
        guarantee = certify_trajectory(
            [step(1, 0, 5, inside=False)], require_forward_invariance=False
        )
        self.assertFalse(guarantee.forward_invariance_enforced)
        self.assertEqual(guarantee.waivers, (FORWARD_INVARIANCE_WAIVER,))
        self.assertIn(FORWARD_INVARIANCE_WAIVER, guarantee.limitations)

    def test_a_waived_result_is_distinguishable_without_reading_the_docstring(self):
        import dataclasses

        waived = certify_trajectory(
            [step(1, 0, 5, inside=False)], require_forward_invariance=False
        )
        enforced = certify_trajectory([step(1, 0, 5, inside=True)])
        self.assertNotEqual(waived, enforced)
        # Name the fields that differ, so the difference is demonstrated rather
        # than left to dataclass equality. My first version of this test
        # asserted the difference had to appear in the numeric fields, which
        # was wrong: the numbers are legitimately identical and the waiver is
        # carried by forward_invariance_enforced and waivers.
        differing = {
            f.name
            for f in dataclasses.fields(waived)
            if getattr(waived, f.name) != getattr(enforced, f.name)
        }
        self.assertIn("forward_invariance_enforced", differing)
        self.assertIn("waivers", differing)
        self.assertNotIn(
            "steps_checked", differing, "the numeric coverage is the same on both"
        )

    def test_a_waived_guarantee_cannot_omit_its_waiver(self):
        with self.assertRaises(ValueError) as caught:
            TrajectoryGuarantee(
                steps_checked=1, last_step=1, bound_attained=False,
                premise_held_at_every_step=True,
                forward_invariance_enforced=False, waivers=(),
                limitations=(SCOPE_LIMITATION,), premise_basis="caller_asserted",
            )
        self.assertIn("waiver", str(caught.exception))

    def test_a_waived_guarantee_cannot_omit_the_text_from_limitations(self):
        with self.assertRaises(ValueError):
            TrajectoryGuarantee(
                steps_checked=1, last_step=1, bound_attained=False,
                premise_held_at_every_step=True,
                forward_invariance_enforced=False,
                waivers=(FORWARD_INVARIANCE_WAIVER,),
                limitations=(SCOPE_LIMITATION,), premise_basis="caller_asserted",
            )

    def test_an_enforced_guarantee_cannot_claim_a_waiver(self):
        with self.assertRaises(ValueError):
            TrajectoryGuarantee(
                steps_checked=1, last_step=1, bound_attained=False,
                premise_held_at_every_step=True,
                forward_invariance_enforced=True,
                waivers=(FORWARD_INVARIANCE_WAIVER,),
                limitations=(FORWARD_INVARIANCE_WAIVER,),
                premise_basis="caller_asserted",
            )

    def test_waiving_does_not_excuse_a_failed_premise(self):
        with self.assertRaises(DomainNotForwardInvariant):
            certify_trajectory(
                [step(1, 1, 1, premise=False)],
                require_forward_invariance=False,
            )


class ForwardTrajectoriesTest(unittest.TestCase):

    def test_an_honest_trajectory_is_certified(self):
        # SIM-002: error equals the bound at every step, premise holds throughout.
        trajectory = [
            step(0, 0, 0),
            step(1, "1/4", "1/4"),
            step(2, "3/8", "3/8"),
            step(3, "7/16", "7/16"),
        ]
        guarantee = certify_trajectory(trajectory)
        self.assertEqual(guarantee.steps_checked, 4)
        self.assertTrue(guarantee.bound_attained)
        self.assertTrue(guarantee.premise_held_at_every_step)

    def test_a_guarantee_states_how_many_steps_it_covers(self):
        guarantee = certify_trajectory([step(0, 0, 0), step(1, "1/4", "1/2")])
        self.assertEqual(guarantee.steps_checked, 2)
        self.assertFalse(guarantee.bound_attained, "a strict inequality is not attainment")

    def test_non_contiguous_steps_are_refused(self):
        with self.assertRaises(ValueError):
            certify_trajectory([step(0, 0, 0), step(2, 1, 2)])

    def test_a_malformed_step_is_reported_even_when_an_earlier_step_fails(self):
        # Found while fixing this work order: structural validation used to run
        # inside the semantic loop, so a bad step at n=2 was hidden behind a
        # semantic refusal at n=1 and whether it was reported depended on order.
        with self.assertRaises(ValueError) as caught:
            certify_trajectory([
                step(0, 0, 0),
                step(1, 1, 1, premise=False),
                step(3, 0, 0),
            ])
        self.assertIn("contiguous", str(caught.exception))

    def test_an_empty_trajectory_is_refused(self):
        with self.assertRaises(ValueError):
            certify_trajectory([])

    def test_steps_are_sorted_so_order_of_supply_does_not_matter(self):
        reversed_order = [step(1, "1/4", "1/2"), step(0, 0, 0)]
        guarantee = certify_trajectory(reversed_order)
        self.assertEqual(guarantee.last_step, 1)

    def test_a_guarantee_cannot_be_constructed_without_a_holding_premise(self):
        with self.assertRaises(DomainNotForwardInvariant):
            TrajectoryGuarantee(
                steps_checked=1, last_step=0, bound_attained=False,
                premise_held_at_every_step=False,
                forward_invariance_enforced=True, waivers=(),
                limitations=(SCOPE_LIMITATION,), premise_basis="caller_asserted",
            )


class ForwardInvarianceReportTest(unittest.TestCase):

    def test_a_path_that_escapes_is_reported_with_its_step(self):
        path = [[Fraction(2), Fraction(0)], [Fraction(4), Fraction(0)], [Fraction(16), Fraction(0)]]
        report = forward_invariance_report(path, lambda p: -10 <= p[0] <= 10)
        self.assertTrue(report["escaped"])
        self.assertEqual(report["first_step_outside_domain"], 2)

    def test_a_contained_path_does_not_claim_general_invariance(self):
        path = [[Fraction(2), Fraction(0)], [Fraction(4), Fraction(0)]]
        report = forward_invariance_report(path, lambda p: -10 <= p[0] <= 10)
        self.assertFalse(report["escaped"])
        self.assertIn("Observed path only", report["scope"])


if __name__ == "__main__":
    unittest.main()
