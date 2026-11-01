"""Mutation tests for the ULC-01-05 guards.

A test that passes proves a guard *ran*, not that it would catch anything. This
module weakens each guard in the real source, runs the named test class against
the weakened code, and requires that run to fail. A guard whose removal leaves
every test green is not tested, it is only exercised.

Two controls make "caught" mean something:

``test_the_control_run_passes_without_a_mutation``
    The same runner, same selector, unmutated source must exit 0. Without this
    a broken selector — a class name that does not exist, say — would make every
    case look caught. An earlier version of this module had exactly that defect
    and reported fifteen false catches; it exited 1 for every mutation because
    it named a class in a module that did not define it.

``test_a_mutation_that_changes_nothing_is_not_counted_as_caught``
    A textual substitution that leaves behaviour intact must NOT be reported as
    caught, which proves the runner distinguishes a real failure from noise.

How the source is mutated
    The original bytes and their sha256 are kept in memory and written to a
    backup file. After every case the file is re-hashed against the baseline and
    a mismatch fails the test rather than passing quietly. An ``atexit`` hook
    restores the source if this process dies mid-mutation.

    These tests rewrite a source file, so this module is not safe to run
    concurrently with itself or with a suite that imports the module under
    mutation. ``unittest`` runs serially by default and this repository has no
    parallel runner.

Scope
    Shows the listed guards are load-bearing against the listed mutations. It
    does not show the list is complete, and it is not independent verification:
    mutations and tests share an author with the code.
"""

import atexit
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROTOTYPE = Path(__file__).resolve().parents[1]
SOURCE = PROTOTYPE / "universalis" / "trajectory.py"
BASELINE = SOURCE.read_bytes()
BASELINE_TEXT = BASELINE.decode()
BASELINE_SHA = hashlib.sha256(BASELINE).hexdigest()

_BACKUP = {"dir": None, "path": None}

#: module (without .py) that defines each test class used below.
MODULE_FOR_CLASS = {
    "InvalidMagnitudesTest": "test_ulc_01_05_forward_invariance",
    "InvalidStepShapeTest": "test_ulc_01_05_forward_invariance",
    "ComputedPremiseTest": "test_ulc_01_05_forward_invariance",
    "RefusalOrderTest": "test_ulc_01_05_forward_invariance",
    "WaiverIsVisibleTest": "test_ulc_01_05_forward_invariance",
    "ForwardTrajectoriesTest": "test_ulc_01_05_forward_invariance",
}


def _ensure_backup():
    if _BACKUP["path"] is None:
        directory = tempfile.mkdtemp(prefix="ulc-mutation-")
        path = Path(directory) / "trajectory.py"
        path.write_bytes(BASELINE)
        _BACKUP["dir"], _BACKUP["path"] = directory, path

        def _restore_at_exit():
            source = _BACKUP["path"]
            if source is not None and source.exists():
                SOURCE.write_bytes(source.read_bytes())
            if _BACKUP["dir"]:
                shutil.rmtree(_BACKUP["dir"], ignore_errors=True)

        atexit.register(_restore_at_exit)
    return _BACKUP["path"]


#: (label, anchor, replacement, test class that must fail, why it must fail)
MUTATIONS = [
    (
        "negative magnitude and bound rejected",
        '    if quantity < 0:\n'
        '        raise ValueError(f"{field} must be non-negative; got {quantity}")\n',
        "",
        "InvalidMagnitudesTest",
        "a negative error or bound would be accepted as a quantity",
    ),
    (
        "bool rejected where a number is expected",
        "if isinstance(value, bool) or not isinstance(value, _QUANTITY_TYPES):",
        "if not isinstance(value, _QUANTITY_TYPES):",
        "InvalidMagnitudesTest",
        "True would be read as the integer 1",
    ),
    (
        "bool-only inside_domain enforced",
        "if not isinstance(self.inside_domain, bool):",
        "if False:",
        "InvalidStepShapeTest",
        'the truthy string "yes" would be accepted as an assertion',
    ),
    (
        "bool-only premise_holds enforced",
        "if self.premise_holds is not None and not isinstance(self.premise_holds, bool):",
        "if False:",
        "InvalidStepShapeTest",
        "the integer 1 would be accepted as an assertion",
    ),
    (
        "premise disagreement refused",
        "if computed != self.premise_holds:",
        "if False:",
        "ComputedPremiseTest",
        "a boolean contradicting its own numbers would be accepted",
    ),
    (
        "waiver recorded on the result",
        "waivers = (FORWARD_INVARIANCE_WAIVER,)",
        "waivers = ()",
        "WaiverIsVisibleTest",
        "a waived guarantee would look identical to a full one",
    ),
    (
        "refusal order: premise before bound",
        "        if not step.premise_holds:",
        "        if error > bound:\n"
        '            raise DomainNotForwardInvariant(step=step.n, reason=f"true error {error} exceeds the claimed bound {bound}")\n'
        "        if not step.premise_holds:",
        "RefusalOrderTest",
        "the bound would be reported first and mask the premise failure at step 1",
    ),
    (
        "refusal order: domain before premise",
        "if require_forward_invariance and not step.inside_domain:",
        "if False:",
        "RefusalOrderTest",
        "an escaped domain would be reported as a premise failure",
    ),
    (
        "negative step index refused",
        "        if self.n < 0:",
        "        if False:",
        "InvalidStepShapeTest",
        "a negative step index would be certified",
    ),
    (
        "bool step index refused",
        "if isinstance(self.n, bool) or not isinstance(self.n, int):",
        "if not isinstance(self.n, int):",
        "InvalidStepShapeTest",
        "True would be accepted as step 1",
    ),
    (
        "waiver text required in limitations",
        "if FORWARD_INVARIANCE_WAIVER not in self.limitations:",
        "if False:",
        "WaiverIsVisibleTest",
        "a reader of the object would never see the waiver",
    ),
    (
        "StepFact type enforced",
        "if not isinstance(step, StepFact):",
        "if False:",
        "InvalidStepShapeTest",
        "a lookalike object would bypass every StepFact check",
    ),
    (
        "non-finite values refused",
        "if isinstance(value, float) and not math.isfinite(value):",
        "if False:",
        "InvalidMagnitudesTest",
        "NaN would reach Fraction and fail with the wrong exception type",
    ),
    (
        "premise computed from residual and epsilon",
        "computed = None if residual is None else residual <= epsilon",
        "computed = None if residual is None else residual > epsilon",
        "ComputedPremiseTest",
        "every surviving trajectory would have a failed premise",
    ),
    (
        "structural validation before semantic refusal",
        "if previous_n is not None and step.n != previous_n + 1:",
        "if False:",
        "ForwardTrajectoriesTest",
        "a non-contiguous trajectory would be certified",
    ),
]


def _run_class(test_class):
    """Run one test class in a fresh process, from the module that defines it."""
    module = MODULE_FOR_CLASS[test_class]
    return subprocess.run(
        [sys.executable, "-m", "unittest", f"{module}.{test_class}"],
        cwd=str(PROTOTYPE / "tests"),
        capture_output=True,
        text=True,
    )


class GuardMutationTest(unittest.TestCase):
    """Each guard must be load-bearing: remove it and its tests must fail."""

    def _run_with_text(self, text):
        backup = _ensure_backup()
        try:
            SOURCE.write_text(text)
            result = _run_class(self.current_class)
        finally:
            SOURCE.write_bytes(backup.read_bytes())
        self.assertEqual(
            hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            BASELINE_SHA,
            "source was not restored",
        )
        return result

    def test_the_control_run_passes_without_a_mutation(self):
        # Proves the runner and the selectors are sound. Without this, a
        # selector naming a class that does not exist would fail on every
        # mutation and be counted as a catch for the wrong reason.
        for test_class in sorted(MODULE_FOR_CLASS):
            with self.subTest(test_class=test_class):
                result = subprocess.run(
                    [sys.executable, "-m", "unittest",
                     f"{MODULE_FOR_CLASS[test_class]}.{test_class}"],
                    cwd=str(PROTOTYPE / "tests"), capture_output=True, text=True,
                )
                combined = result.stdout + result.stderr
                self.assertEqual(
                    result.returncode, 0,
                    f"control run of {test_class} is not green, so a failure "
                    f"under mutation would prove nothing:\n{combined[-800:]}",
                )
                self.assertNotIn("no such test method", combined)
                self.assertNotIn("AttributeError", combined)
                self.assertNotIn("Ran 0 tests", combined)

    def test_a_mutation_that_changes_nothing_is_not_counted_as_caught(self):
        # A cosmetic substitution keeps behaviour identical; the runner must
        # report green, so a red result can only mean the guard mattered.
        self.current_class = "InvalidMagnitudesTest"
        cosmetic = BASELINE_TEXT.replace(
            "#: Types accepted as a quantity", "#: Types ACCEPTED as a quantity", 1
        )
        self.assertNotEqual(cosmetic, BASELINE_TEXT, "cosmetic edit did not apply")
        result = self._run_with_text(cosmetic)
        self.assertEqual(
            result.returncode, 0,
            "a cosmetic edit was reported as a catch, so this runner cannot "
            f"distinguish a real failure from noise:\n{(result.stdout + result.stderr)[-800:]}",
        )

    def test_every_mutation_is_caught(self):
        uncaught, mis_anchored = [], []
        for label, anchor, replacement, test_class, why in MUTATIONS:
            with self.subTest(mutation=label):
                if anchor not in BASELINE_TEXT:
                    mis_anchored.append(
                        f"{label!r}: anchor no longer present in trajectory.py, so "
                        "this mutation must be updated rather than silently skipped"
                    )
                    continue
                self.current_class = test_class
                mutated = BASELINE_TEXT.replace(anchor, replacement, 1)
                self.assertNotEqual(mutated, BASELINE_TEXT, "mutation changed nothing")
                result = self._run_with_text(mutated)
                if result.returncode == 0:
                    uncaught.append(f"{label!r} was NOT caught by {test_class}: {why}")
        self.assertEqual(mis_anchored, [], "\n".join(mis_anchored))
        self.assertEqual(uncaught, [], "\n".join(uncaught))

    def test_the_mutation_table_covers_every_guard_of_interest(self):
        # A table that emptied itself would make the case above pass vacuously.
        self.assertGreaterEqual(len(MUTATIONS), 12)
        covered = {entry[3] for entry in MUTATIONS}
        for required in (
            "InvalidMagnitudesTest",
            "InvalidStepShapeTest",
            "ComputedPremiseTest",
            "RefusalOrderTest",
            "WaiverIsVisibleTest",
        ):
            self.assertIn(required, covered, f"no mutation covers {required}")

    def test_the_source_is_unmutated_at_the_end(self):
        self.assertEqual(
            hashlib.sha256(SOURCE.read_bytes()).hexdigest(), BASELINE_SHA
        )


if __name__ == "__main__":
    unittest.main()
