"""Wave 1 remediation K01, N10, N11 (ULC-01-05 trajectory inputs).

Audit items (2026-11-07):

- K01 (High, known): ``forward_invariance_report`` accepted a string or a list
  of non-points as a trajectory and returned a clean "not escaped" report.
- N10: after an early escape, ``points_checked`` reported every supplied point,
  including points the domain predicate never saw.
- N11: ``certify_trajectory(require_forward_invariance="false")`` was accepted
  and the string was copied into ``forward_invariance_enforced``.

These regressions pin the corrected contract. A report remains a statement
about one observed path only; it is never a proof of invariance.
"""

import unittest
from fractions import Fraction

import bootstrap  # noqa: F401

from universalis.trajectory import StepFact, certify_trajectory, forward_invariance_report


def _box(point):
    return -10 <= point[0] <= 10


def _ok_step(n=0):
    return StepFact(n=n, true_error=Fraction(0), claimed_bound=Fraction(0),
                    inside_domain=True, premise_holds=True)


class W1K01NonTrajectoryRefusedTest(unittest.TestCase):

    def test_string_path_is_refused(self):
        with self.assertRaises(TypeError):
            forward_invariance_report("abc", lambda p: True)

    def test_list_of_non_points_is_refused(self):
        for bad in ([None, 42, "x"], ["12", "34"], [1, 2, 3], [b"ab"]):
            with self.subTest(path=bad):
                with self.assertRaises(TypeError):
                    forward_invariance_report(bad, lambda p: True)

    def test_point_coordinates_must_be_quantities(self):
        for bad in ([[True, Fraction(0)]], [["1", "2"]], [[None]], [[Fraction(1), object()]]):
            with self.subTest(path=bad):
                with self.assertRaises(TypeError):
                    forward_invariance_report(bad, lambda p: True)

    def test_non_finite_coordinates_are_refused(self):
        for bad in ([[float("nan")]], [[float("inf"), 0]]):
            with self.subTest(path=bad):
                with self.assertRaises(ValueError):
                    forward_invariance_report(bad, lambda p: True)

    def test_empty_path_or_empty_point_is_refused(self):
        with self.assertRaises(ValueError):
            forward_invariance_report([], lambda p: True)
        with self.assertRaises(ValueError):
            forward_invariance_report([[]], lambda p: True)

    def test_inconsistent_dimensions_are_refused(self):
        with self.assertRaises(ValueError):
            forward_invariance_report([[Fraction(1), Fraction(0)], [Fraction(1)]], _box)

    def test_predicate_must_be_callable_and_return_a_real_bool(self):
        path = [[Fraction(1)]]
        with self.assertRaises(TypeError):
            forward_invariance_report(path, "not callable")
        for bad_return in (1, 0, "false", None, Fraction(1)):
            with self.subTest(returned=bad_return):
                with self.assertRaises(TypeError):
                    forward_invariance_report(path, lambda p, r=bad_return: r)

    def test_valid_paths_still_report(self):
        report = forward_invariance_report([[Fraction(2), 0], [4, 0.5]], _box)
        self.assertFalse(report["escaped"])
        self.assertEqual(report["points_checked"], 2)
        self.assertIn("Observed path only", report["scope"])


class W1N10PointsCheckedTest(unittest.TestCase):

    def test_points_checked_counts_only_evaluated_points(self):
        calls = []

        def predicate(point):
            calls.append(point)
            return False

        report = forward_invariance_report([[Fraction(11)], [Fraction(1)], [Fraction(2)]], predicate)
        self.assertEqual(len(calls), 1)
        self.assertEqual(report["points_checked"], 1)
        self.assertEqual(report["points_supplied"], 3)
        self.assertTrue(report["escaped"])
        self.assertEqual(report["first_step_outside_domain"], 0)

    def test_contained_path_checks_every_point(self):
        report = forward_invariance_report([[Fraction(1)], [Fraction(2)], [Fraction(3)]], _box)
        self.assertEqual(report["points_checked"], 3)
        self.assertEqual(report["points_supplied"], 3)


class W1N11BooleanOptionTest(unittest.TestCase):

    def test_non_bool_require_forward_invariance_is_refused(self):
        for bad in ("false", "true", 0, 1, None):
            with self.subTest(option=bad):
                with self.assertRaises(TypeError):
                    certify_trajectory([_ok_step()], require_forward_invariance=bad)

    def test_real_booleans_still_work_and_waiver_stays_visible(self):
        enforced = certify_trajectory([_ok_step()], require_forward_invariance=True)
        self.assertIs(enforced.forward_invariance_enforced, True)
        waived = certify_trajectory([_ok_step()], require_forward_invariance=False)
        self.assertIs(waived.forward_invariance_enforced, False)
        self.assertTrue(waived.waivers)


class W1K01MutationTest(unittest.TestCase):
    """Removing the path validation must turn the K01 regression red."""

    def test_disabling_path_validation_revives_the_false_green(self):
        import universalis.trajectory as trajectory

        original = trajectory._validated_path
        trajectory._validated_path = lambda path: list(path)  # mutant
        try:
            outcome = unittest.TestResult()
            unittest.defaultTestLoader.loadTestsFromName(
                "test_string_path_is_refused", W1K01NonTrajectoryRefusedTest
            ).run(outcome)
        finally:
            trajectory._validated_path = original
        self.assertEqual((outcome.testsRun, len(outcome.errors)), (1, 0), outcome.errors)
        self.assertEqual(len(outcome.failures), 1, "mutant survived")
        self.assertIn("AssertionError", outcome.failures[0][1])


if __name__ == "__main__":
    unittest.main()
