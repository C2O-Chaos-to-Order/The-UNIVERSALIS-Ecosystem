"""ULC-01-05: a bound is not a guarantee on a domain iteration escapes.

These tests pin the behaviour the UNI-RP-001 research found missing. The
central case reproduces SIM-003 exactly: at step 1 the error equals the bound,
the point is inside the domain, the bound is satisfied, and the residual has
already exceeded the premise. A check that only compares error to bound passes
it. This one must refuse.
"""

import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from universalis.errors import DomainNotForwardInvariant
from universalis.trajectory import (
    StepFact,
    certify_trajectory,
    forward_invariance_report,
)


def step(n, error, bound, inside=True, premise=True, residual=None):
    return StepFact(
        n=n,
        true_error=Fraction(error),
        claimed_bound=Fraction(bound),
        inside_domain=inside,
        premise_holds=premise,
        residual=None if residual is None else Fraction(residual),
    )


class TheSimulationFindingTest(unittest.TestCase):
    """The exact shape of SIM-003, taken from the executed evidence."""

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

    def test_the_real_sim_003_trajectory_is_refused_at_its_first_failure(self):
        # Values transcribed from results/trajectories/SIM-003_trajectory.json.
        trajectory = [
            step(0, 0, 0, inside=True, premise=True),
            step(1, 1, 1, inside=True, premise=False, residual=4),
            step(2, 7, 5, inside=False, premise=False, residual=64),
        ]
        with self.assertRaises(DomainNotForwardInvariant) as caught:
            certify_trajectory(trajectory)
        self.assertEqual(caught.exception.step, 1, "must report the first failure, not a later one")


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

    def test_error_above_bound_is_refused(self):
        with self.assertRaises(DomainNotForwardInvariant) as caught:
            certify_trajectory([step(0, 0, 0), step(1, 3, 2)])
        self.assertIn("exceeds", caught.exception.reason)

    def test_non_contiguous_steps_are_refused(self):
        with self.assertRaises(ValueError):
            certify_trajectory([step(0, 0, 0), step(2, 1, 2)])

    def test_an_empty_trajectory_is_refused(self):
        with self.assertRaises(ValueError):
            certify_trajectory([])

    def test_a_boolean_is_not_a_quantity(self):
        with self.assertRaises(TypeError):
            certify_trajectory([
                StepFact(n=0, true_error=True, claimed_bound=Fraction(1),
                         inside_domain=True, premise_holds=True)
            ])

    def test_steps_are_sorted_so_order_of_supply_does_not_matter(self):
        reversed_order = [step(1, "1/4", "1/2"), step(0, 0, 0)]
        guarantee = certify_trajectory(reversed_order)
        self.assertEqual(guarantee.last_step, 1)

    def test_a_guarantee_cannot_be_constructed_without_a_holding_premise(self):
        from universalis.trajectory import TrajectoryGuarantee
        with self.assertRaises(DomainNotForwardInvariant):
            TrajectoryGuarantee(
                steps_checked=1, last_step=0, bound_attained=False,
                premise_held_at_every_step=False,
            )

    def test_forward_invariance_can_be_waived_explicitly(self):
        # The check is opt-out only by explicit argument, so silence is never
        # read as consent to skip it.
        guarantee = certify_trajectory(
            [step(1, 0, 5, inside=False, premise=True)],
            require_forward_invariance=False,
        )
        self.assertEqual(guarantee.steps_checked, 1)


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
