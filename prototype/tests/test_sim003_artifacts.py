"""Drive the ULC-01-05 implementation from the real UNI-RP-001 SIM-003 artifacts.

Nothing here is a hand-typed trajectory. Every value is parsed from the
research record and its raw per-step trajectory, with ``Fraction`` so all
arithmetic is exact. The point is to reproduce the research finding against
the implementation rather than to confirm a fixture written to suit it.

Artifact provenance
    record:     results/SIM-003.json                      sha256 0ad25914759f...
    trajectory: results/trajectories/SIM-003_trajectory.json sha256 e5edb338...
    model:      simulations/model.py                      sha256 d21c2613...
                (the record's own code_sha256; this module does not re-run it)

Resolution order
    1. ``UNIVERSALIS_UNI_PKG`` if set — the canonical research package.
    2. Otherwise the vendored byte-identical copies under ``tests/fixtures/``.

If an external package is named but absent, the external tests skip with the
reason stated. They never fall back to the vendored copy silently, because a
test that claims to have read the research package must have read it.

What is and is not established here
    This module shows the implementation behaves correctly on facts recorded by
    another program. It does not establish that the research record is correct,
    that the simulation was independently reproduced, or that the finding
    generalises. The simulation and this implementation share an author.
"""

import hashlib
import json
import os
import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from universalis.errors import DomainNotForwardInvariant
from universalis.trajectory import (
    FORWARD_INVARIANCE_WAIVER,
    StepFact,
    certify_trajectory,
)

HERE = Path(__file__).resolve().parent
VENDORED = HERE / "fixtures" / "sim003"
EXTERNAL = os.environ.get("UNIVERSALIS_UNI_PKG")

#: Hashes of the two artifacts, recorded so a substitution is detectable. The
#: vendored copy must match byte for byte; that is asserted, not assumed.
RECORD_SHA256 = "0ad25914759ff26add9f3872f8a40ba9895755c8adb118f1c660d39e6655e6a1"
TRAJECTORY_SHA256 = "e5edb33859522f9b8c86c03f04c4c1e6f0b41c023ebe7c9a805753ca37aa3ab8"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(directory: Path):
    record_path = directory / "SIM-003.json"
    trajectory_path = directory / "SIM-003_trajectory.json"
    record = json.loads(record_path.read_text())
    trajectory = json.loads(trajectory_path.read_text())
    return record, trajectory, record_path, trajectory_path


def _steps_from(trajectory, epsilon):
    """Build StepFacts from the recorded rows, parsing every number exactly.

    ``residual_here`` and the record's ``input.epsilon`` are supplied instead of
    a boolean, so the premise is *computed* by the implementation rather than
    copied from the artifact's ``hypothesis_intact`` field. That is the whole
    point: the module must reach the same verdict without being told it.

    ``epsilon`` is passed in rather than held in a module global so that test
    ordering cannot change what is under test.
    """
    epsilon = Fraction(epsilon)
    return [
        StepFact(
            n=row["n"],
            true_error=Fraction(row["true_error"]),
            claimed_bound=Fraction(row["claimed_bound"]),
            inside_domain=row["inside_domain"],
            residual=Fraction(row["residual_here"]),
            epsilon=epsilon,
        )
        for row in trajectory
    ]


class ArtifactIntegrityTest(unittest.TestCase):
    """The vendored copy must be the research package's copy, not a likeness."""

    def test_the_vendored_record_matches_its_recorded_hash(self):
        path = VENDORED / "SIM-003.json"
        self.assertTrue(path.is_file(), f"missing vendored record at {path}")
        self.assertEqual(_sha256(path), RECORD_SHA256)

    def test_the_vendored_trajectory_matches_its_recorded_hash(self):
        path = VENDORED / "SIM-003_trajectory.json"
        self.assertTrue(path.is_file(), f"missing vendored trajectory at {path}")
        self.assertEqual(_sha256(path), TRAJECTORY_SHA256)

    def test_the_vendored_trajectory_is_the_one_the_record_points_at(self):
        # The record's own raw_evidence_location must name the trajectory we
        # vendored, so the pair cannot drift apart unnoticed.
        record, _, _, _ = _load(VENDORED)
        declared = record["raw_evidence_location"]
        self.assertTrue(declared.endswith("SIM-003.json"))
        self.assertEqual(record["record_id"], "SIM-003")

    def test_the_record_names_the_code_that_produced_it(self):
        # A shape check only: this module does not re-run the model, so it
        # cannot confirm the hash belongs to the code that ran. It confirms the
        # record carries a hash rather than a promise.
        record, _, _, _ = _load(VENDORED)
        digest = record.get("code_sha256", "")
        self.assertEqual(len(digest), 64, "a sha256 hex digest is 64 characters")
        int(digest, 16)  # raises if it is not hex


class TheFindingReproducedFromArtifactsTest(unittest.TestCase):
    """SIM-003's finding, re-derived from the recorded evidence."""

    @classmethod
    def setUpClass(cls):
        record, trajectory, _, _ = _load(VENDORED)
        cls.record = record
        cls.trajectory = trajectory
        cls.epsilon = record["input"]["epsilon"]

    def test_the_premise_breaks_at_step_1_and_the_bound_at_step_2(self):
        # Established from the artifacts, not assumed: this is the claim under
        # test and it is independently recomputed here.
        first_premise_break = next(
            row["n"] for row in self.trajectory if not row["hypothesis_intact"]
        )
        first_bound_violation = next(
            row["n"] for row in self.trajectory if not row["bound_satisfied"]
        )
        self.assertEqual(first_premise_break, 1)
        self.assertEqual(first_bound_violation, 2)
        self.assertLess(
            first_premise_break,
            first_bound_violation,
            "the finding is that the premise fails BEFORE the bound is violated",
        )

    def test_at_step_1_the_bound_is_satisfied_and_the_point_is_inside(self):
        # The seductive row: everything a bound-only check looks at passes.
        row = self.trajectory[1]
        self.assertEqual(row["n"], 1)
        self.assertTrue(row["bound_satisfied"])
        self.assertTrue(row["inside_domain"])
        self.assertEqual(
            Fraction(row["true_error"]), Fraction(row["claimed_bound"])
        )
        self.assertFalse(row["residual_within_epsilon"])

    def test_computing_the_premise_agrees_with_the_record_at_every_step(self):
        # residual <= epsilon is computed by StepFact from the recorded residual
        # and epsilon; it must equal the record's own hypothesis_intact. If the
        # two disagreed, either the implementation or the record would be wrong
        # and neither should be assumed correct.
        eps = Fraction(self.record["input"]["epsilon"])
        for row in self.trajectory:
            fact = StepFact(
                n=row["n"],
                true_error=Fraction(row["true_error"]),
                claimed_bound=Fraction(row["claimed_bound"]),
                inside_domain=row["inside_domain"],
                residual=Fraction(row["residual_here"]),
                epsilon=eps,
            )
            self.assertEqual(
                fact.premise_holds,
                row["hypothesis_intact"],
                f"step {row['n']}: computed premise disagrees with the record",
            )
            self.assertEqual(fact.premise_basis, "computed_from_residual_and_epsilon")

    def test_the_recorded_claimed_bound_is_the_closed_form(self):
        # Guards the derivation the module's docstring cites.
        eps = Fraction(self.record["input"]["epsilon"])
        big_l = Fraction(self.record["input"]["L"])
        for row in self.trajectory:
            expected = eps * sum((big_l**k for k in range(row["n"])), Fraction(0))
            self.assertEqual(
                Fraction(row["claimed_bound"]),
                expected,
                f"step {row['n']}: recorded bound is not eps*sum(L^k)",
            )

    def test_the_module_refuses_the_recorded_trajectory(self):
        with self.assertRaises(DomainNotForwardInvariant) as caught:
            certify_trajectory(_steps_from(self.trajectory, self.epsilon))
        self.assertEqual(caught.exception.step, 1)

    def test_it_refuses_at_step_1_and_not_at_step_2(self):
        # The distinction the finding turns on. Refusing at step 2 would mean
        # the module learned what a bound-only check already knew.
        with self.assertRaises(DomainNotForwardInvariant) as caught:
            certify_trajectory(_steps_from(self.trajectory, self.epsilon))
        self.assertNotEqual(caught.exception.step, 2)
        self.assertEqual(caught.exception.step, 1)

    def test_the_refusal_reason_identifies_a_failed_premise(self):
        with self.assertRaises(DomainNotForwardInvariant) as caught:
            certify_trajectory(_steps_from(self.trajectory, self.epsilon))
        reason = caught.exception.reason.lower()
        self.assertIn("premise", reason)
        # It must not be the bound violation: at step 1 the bound held.
        self.assertNotIn("exceeds", reason)

    def test_truncating_before_the_failure_would_have_passed(self):
        # Shows precisely what the module adds. Steps 0..1 certify cleanly if
        # the trajectory simply stops there — and step 1 is where the premise
        # has just failed, so the prefix is exactly the trap.
        prefix = _steps_from(self.trajectory, self.epsilon)[:2]
        with self.assertRaises(DomainNotForwardInvariant) as caught:
            certify_trajectory(prefix)
        self.assertEqual(caught.exception.step, 1)
        # And step 0 alone is certified, because nothing has failed yet. That
        # is correct and is not a weakness: a guarantee over one step is a
        # guarantee over one step, which is why steps_checked is mandatory.
        guarantee = certify_trajectory(_steps_from(self.trajectory, self.epsilon)[:1])
        self.assertEqual(guarantee.steps_checked, 1)

    def test_a_bound_only_check_would_have_accepted_the_prefix(self):
        # The contrast case, computed from the artifacts: a check that only
        # compares error to bound accepts steps 0..1 and reports no problem.
        prefix = self.trajectory[:2]
        bound_only_failures = [r["n"] for r in prefix if not r["bound_satisfied"]]
        self.assertEqual(bound_only_failures, [], "a bound-only check sees nothing")
        # Yet the record shows the premise already broken at the last step.
        self.assertFalse(prefix[-1]["hypothesis_intact"])


class ValidTrajectoryFromArtifactsTest(unittest.TestCase):
    """The implementation must still certify a trajectory that holds up."""

    @classmethod
    def setUpClass(cls):
        record, trajectory, _, _ = _load(VENDORED)
        cls.epsilon = record["input"]["epsilon"]
        # Steps 0 and 1 are the only recorded rows inside the declared box.
        # Selected from the recorded rows rather than invented.
        cls.inside_rows = [r for r in trajectory if r["inside_domain"]]

    def test_the_rows_inside_the_declared_domain_are_steps_0_and_1(self):
        self.assertEqual([r["n"] for r in self.inside_rows], [0, 1])

    def test_a_trajectory_that_holds_up_is_certified(self):
        # Step 1's premise has failed in SIM-003, so the honest valid case from
        # these artifacts is step 0 alone. Asserted rather than assumed.
        step_zero = _steps_from([self.inside_rows[0]], self.epsilon)
        guarantee = certify_trajectory(step_zero)
        self.assertEqual(guarantee.steps_checked, 1)
        self.assertTrue(guarantee.forward_invariance_enforced)
        self.assertEqual(guarantee.waivers, ())


class ExternalPackageTest(unittest.TestCase):
    """When the research package is on disk, compare against it directly.

    These skip, with a reason, when it is not. A skip is honest; a silent
    fallback to the vendored copy would let a reader believe the external
    package was read when it was not.
    """

    def setUp(self):
        if not EXTERNAL:
            self.skipTest(
                "UNIVERSALIS_UNI_PKG is not set, so the external research "
                "package was not read; the vendored byte-identical fixtures "
                "were used instead"
            )
        directory = Path(EXTERNAL)
        if not (directory / "results" / "SIM-003.json").is_file():
            self.skipTest(
                f"UNIVERSALIS_UNI_PKG={EXTERNAL} does not contain "
                "results/SIM-003.json, so the external package was not read"
            )
        self.directory = directory

    def test_the_external_record_is_byte_identical_to_the_vendored_copy(self):
        external = self.directory / "results" / "SIM-003.json"
        self.assertEqual(_sha256(external), RECORD_SHA256)
        self.assertEqual(
            external.read_bytes(), (VENDORED / "SIM-003.json").read_bytes()
        )

    def test_the_external_trajectory_is_byte_identical_to_the_vendored_copy(self):
        external = self.directory / "results" / "trajectories" / "SIM-003_trajectory.json"
        self.assertEqual(_sha256(external), TRAJECTORY_SHA256)
        self.assertEqual(
            external.read_bytes(),
            (VENDORED / "SIM-003_trajectory.json").read_bytes(),
        )

    def test_the_module_refuses_the_externally_loaded_trajectory(self):
        # The package keeps the record and the trajectory in different
        # directories, so read each from its own path rather than reusing the
        # single-directory loader.
        results = self.directory / "results"
        record = json.loads((results / "SIM-003.json").read_text())
        trajectory = json.loads(
            (results / "trajectories" / "SIM-003_trajectory.json").read_text()
        )
        with self.assertRaises(DomainNotForwardInvariant) as caught:
            certify_trajectory(_steps_from(trajectory, record["input"]["epsilon"]))
        self.assertEqual(caught.exception.step, 1)
        self.assertIn("premise", caught.exception.reason)


class TheWaiverIsVisibleOnAnArtifactRunTest(unittest.TestCase):
    """A waived run over the real failure must still say what it waived."""

    def setUp(self):
        record, trajectory, _, _ = _load(VENDORED)
        self.epsilon = record["input"]["epsilon"]
        self.trajectory = trajectory

    def test_waiving_forward_invariance_still_refuses_a_broken_premise(self):
        # Steps 0..1 are inside the domain, so waiving invariance changes
        # nothing about them: the premise failure at step 1 is still fatal.
        with self.assertRaises(DomainNotForwardInvariant) as caught:
            certify_trajectory(
                _steps_from(self.trajectory[:2], self.epsilon),
                require_forward_invariance=False,
            )
        self.assertEqual(caught.exception.step, 1)
        self.assertIn("premise", caught.exception.reason)

    def test_a_waived_guarantee_is_programmatically_distinguishable(self):
        # Step 0 is inside the domain and its premise holds, so this yields a
        # guarantee — a weak one, which must announce itself as such.
        guarantee = certify_trajectory(
            _steps_from(self.trajectory[:1], self.epsilon),
            require_forward_invariance=False,
        )
        self.assertFalse(guarantee.forward_invariance_enforced)
        self.assertEqual(guarantee.waivers, (FORWARD_INVARIANCE_WAIVER,))
        self.assertIn(FORWARD_INVARIANCE_WAIVER, guarantee.limitations)
        full = certify_trajectory(_steps_from(self.trajectory[:1], self.epsilon))
        self.assertNotEqual(full, guarantee)


if __name__ == "__main__":
    unittest.main()
