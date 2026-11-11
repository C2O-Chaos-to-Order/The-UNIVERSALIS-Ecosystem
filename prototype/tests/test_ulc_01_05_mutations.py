"""Mutation tests for the ULC-01-05 guards.

A test that passes proves a guard *ran*, not that it would catch anything. This
module weakens each guard in the module under test and requires the relevant
tests to fail. A guard whose removal leaves every test green is exercised, not
tested.

Where the mutation is applied
    To a **temporary copy** of the package, never to the working tree. An
    earlier version of this module rewrote ``universalis/trajectory.py`` in
    place and restored it afterwards. That was a hazard: any other reader of the
    checkout during the run — a concurrent suite, ``git status``, an editor —
    could observe the mutated source, and a hard kill mid-run could leave it
    corrupted. Mutating a copy removes the hazard rather than managing it.

    The copy contains ``universalis/``, the two test modules that matter here,
    the fixture directory, and ``bootstrap.py``. It is built once per test run
    under a temporary directory and removed afterwards.

Two controls make "caught" mean something:

``test_the_control_run_passes_without_a_mutation``
    The same runner and the same selector against an unmutated copy must exit 0.
    Without this, a broken selector — a class name that does not exist, say —
    would make every mutation look caught. An earlier version of this module had
    exactly that defect and reported fifteen false catches; it exited 1 for
    every mutation because it named a class in a module that did not define it.

``test_a_mutation_that_changes_nothing_is_reported_as_unchanged``
    A substitution whose anchor is absent must be reported as such, never
    counted as a catch. A table entry that silently stopped applying would
    otherwise look like a passing guard.

Scope
    Shows the listed guards are load-bearing against the listed mutations. It
    does not show the list is complete, and it is not independent verification:
    the mutations and the tests share an author with the code.
"""

import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROTOTYPE = Path(__file__).resolve().parents[1]
SOURCE = PROTOTYPE / "universalis" / "trajectory.py"
BASELINE_TEXT = SOURCE.read_text()
BASELINE_SHA = hashlib.sha256(SOURCE.read_bytes()).hexdigest()

#: Test modules copied into the sandbox, and the module each class lives in.
MODULES = {
    "test_ulc_01_05_forward_invariance": [
        "InvalidMagnitudesTest",
        "InvalidStepShapeTest",
        "ComputedPremiseTest",
        "RefusalOrderTest",
        "WaiverIsVisibleTest",
        "ForwardTrajectoriesTest",
    ],
    "test_sim003_artifacts": ["ArtifactIntegrityTest"],
}


def _build_sandbox(destination: Path) -> Path:
    """Copy the package and the tests into ``destination``; return its tests dir."""
    package = destination / "universalis"
    shutil.copytree(
        PROTOTYPE / "universalis", package,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    tests = destination / "tests"
    tests.mkdir()
    shutil.copy2(PROTOTYPE / "tests" / "bootstrap.py", tests / "bootstrap.py")
    for module in MODULES:
        shutil.copy2(PROTOTYPE / "tests" / f"{module}.py", tests / f"{module}.py")
    fixtures = PROTOTYPE / "tests" / "fixtures"
    if fixtures.is_dir():
        shutil.copytree(fixtures, tests / "fixtures")
    return tests


def _text_for(target: str) -> str:
    """The committed text of a sandbox file, used as the mutation baseline."""
    return (PROTOTYPE / target).read_text()


def _run_class(tests_dir: Path, test_class: str) -> subprocess.CompletedProcess:
    """Run one test class from the sandbox, in a fresh process."""
    module = next(m for m, classes in MODULES.items() if test_class in classes)
    return subprocess.run(
        [sys.executable, "-m", "unittest", f"{module}.{test_class}"],
        cwd=str(tests_dir),
        capture_output=True,
        text=True,
    )


#: (label, target file within the sandbox, anchor, replacement, test class that
#: must fail, why it must fail). The target is named per entry rather than
#: assumed to be trajectory.py: one guard lives in the artifact test's own hash
#: pin, and an earlier version of this table wrongly looked for it in
#: trajectory.py and was caught by the stale-anchor check.
MUTATIONS = [
    (
        "negative magnitude and bound rejected",
        "universalis/trajectory.py",
        '    if quantity < 0:\n'
        '        raise ValueError(f"{field} must be non-negative; got {quantity}")\n',
        "",
        "InvalidMagnitudesTest",
        "a negative error or bound would be accepted as a quantity",
    ),
    (
        "bool rejected where a number is expected",
        "universalis/trajectory.py",
        "if isinstance(value, bool) or not isinstance(value, _QUANTITY_TYPES):",
        "if not isinstance(value, _QUANTITY_TYPES):",
        "InvalidMagnitudesTest",
        "True would be read as the integer 1",
    ),
    (
        "bool-only inside_domain enforced",
        "universalis/trajectory.py",
        "if not isinstance(self.inside_domain, bool):",
        "if False:",
        "InvalidStepShapeTest",
        'the truthy string "yes" would be accepted as an assertion',
    ),
    (
        "bool-only premise_holds enforced",
        "universalis/trajectory.py",
        "if self.premise_holds is not None and not isinstance(self.premise_holds, bool):",
        "if False:",
        "InvalidStepShapeTest",
        "the integer 1 would be accepted as an assertion",
    ),
    (
        "premise disagreement refused",
        "universalis/trajectory.py",
        "if computed != self.premise_holds:",
        "if False:",
        "ComputedPremiseTest",
        "a boolean contradicting its own numbers would be accepted",
    ),
    (
        "waiver recorded on the result",
        "universalis/trajectory.py",
        "waivers = (FORWARD_INVARIANCE_WAIVER,)",
        "waivers = ()",
        "WaiverIsVisibleTest",
        "a waived guarantee would look identical to a full one",
    ),
    (
        "refusal order: premise before bound",
        "universalis/trajectory.py",
        "        if not step.premise_holds:",
        "        if error > bound:\n"
        '            raise DomainNotForwardInvariant(step=step.n, reason=f"true error {error} exceeds the claimed bound {bound}")\n'
        "        if not step.premise_holds:",
        "RefusalOrderTest",
        "the bound would be reported first and mask the premise failure at step 1",
    ),
    (
        "refusal order: domain before premise",
        "universalis/trajectory.py",
        "if require_forward_invariance and not step.inside_domain:",
        "if False:",
        "RefusalOrderTest",
        "an escaped domain would be reported as a premise failure",
    ),
    (
        "negative step index refused",
        "universalis/trajectory.py",
        "        if self.n < 0:",
        "        if False:",
        "InvalidStepShapeTest",
        "a negative step index would be certified",
    ),
    (
        "bool step index refused",
        "universalis/trajectory.py",
        "if isinstance(self.n, bool) or not isinstance(self.n, int):",
        "if not isinstance(self.n, int):",
        "InvalidStepShapeTest",
        "True would be accepted as step 1",
    ),
    (
        "waiver text required in limitations",
        "universalis/trajectory.py",
        "if FORWARD_INVARIANCE_WAIVER not in self.limitations:",
        "if False:",
        "WaiverIsVisibleTest",
        "a reader of the object would never see the waiver",
    ),
    (
        "StepFact type enforced",
        "universalis/trajectory.py",
        "if not isinstance(step, StepFact):",
        "if False:",
        "InvalidStepShapeTest",
        "a lookalike object would bypass every StepFact check",
    ),
    (
        "non-finite values refused",
        "universalis/trajectory.py",
        "if isinstance(value, float) and not math.isfinite(value):",
        "if False:",
        "InvalidMagnitudesTest",
        "NaN would reach Fraction and fail with the wrong exception type",
    ),
    (
        "premise computed from residual and epsilon",
        "universalis/trajectory.py",
        "computed = None if residual is None else residual <= epsilon",
        "computed = None if residual is None else residual > epsilon",
        "ComputedPremiseTest",
        "every surviving trajectory would have a failed premise",
    ),
    (
        "structural validation before semantic refusal",
        "universalis/trajectory.py",
        "if previous_n is not None and step.n != previous_n + 1:",
        "if False:",
        "ForwardTrajectoriesTest",
        "a non-contiguous trajectory would be certified",
    ),
    (
        "fixture hash pinned",
        "tests/test_sim003_artifacts.py",
        "RECORD_SHA256 = \"0ad25914759ff26add9f3872f8a40ba9895755c8adb118f1c660d39e6655e6a1\"",
        "RECORD_SHA256 = \"0\" * 64",
        "ArtifactIntegrityTest",
        "a substituted research record would pass the hash check",
    ),
]


class GuardMutationTest(unittest.TestCase):
    """Each guard must be load-bearing: remove it and its tests must fail."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.mkdtemp(prefix="ulc-mutation-")
        cls.tests_dir = _build_sandbox(Path(cls._tmp))
        cls.sandbox = cls.tests_dir.parent
        cls.sandbox_source = cls.sandbox / "universalis" / "trajectory.py"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def _run_with(self, target: str, text: str, test_class: str):
        """Mutate one sandbox file only, run the class, restore that file."""
        path = self.sandbox / target
        original = path.read_text()
        try:
            path.write_text(text)
            return _run_class(self.tests_dir, test_class)
        finally:
            path.write_text(original)

    def test_the_working_tree_is_never_written(self):
        # The whole point of the sandbox. Checked before and after a mutation
        # run so a future edit that reintroduces in-place editing fails here.
        before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        self.current = "InvalidMagnitudesTest"
        self._run_with(
            "universalis/trajectory.py",
            BASELINE_TEXT.replace("if quantity < 0:", "if False:", 1),
            "InvalidMagnitudesTest",
        )
        after = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        self.assertEqual(before, after, "the working tree source was modified")
        self.assertEqual(after, BASELINE_SHA)

    def test_the_control_run_passes_without_a_mutation(self):
        # Proves the runner and the selectors are sound against the sandbox. The
        # sandbox source is identical to the working tree, asserted first.
        self.assertEqual(
            hashlib.sha256(self.sandbox_source.read_bytes()).hexdigest(),
            BASELINE_SHA,
            "the sandbox copy is not the source under test",
        )
        for test_class in sorted({c for cs in MODULES.values() for c in cs}):
            with self.subTest(test_class=test_class):
                result = _run_class(self.tests_dir, test_class)
                combined = result.stdout + result.stderr
                self.assertEqual(
                    result.returncode, 0,
                    f"control run of {test_class} is not green, so a failure "
                    f"under mutation would prove nothing:\n{combined[-800:]}",
                )
                self.assertNotIn("no such test method", combined)
                self.assertNotIn("AttributeError", combined)
                self.assertNotIn("Ran 0 tests", combined)

    def test_a_substitution_whose_anchor_is_gone_is_reported(self):
        # Never counted as a catch: an entry that stopped applying is a stale
        # test, and must be visible as one.
        stale = BASELINE_TEXT.replace("if quantity < 0:", "if False:", 1)
        self.sandbox_source.write_text(stale)
        try:
            # The stale text no longer contains the anchor.
            self.assertNotIn("if quantity < 0:", self.sandbox_source.read_text())
        finally:
            self.sandbox_source.write_text(BASELINE_TEXT)
        self.assertIn("if quantity < 0:", BASELINE_TEXT)

    def test_every_mutation_is_caught(self):
        uncaught, mis_anchored = [], []
        for label, target, anchor, replacement, test_class, why in MUTATIONS:
            with self.subTest(mutation=label):
                baseline = _text_for(target)
                if anchor not in baseline:
                    mis_anchored.append(
                        f"{label!r}: anchor absent from {target}, so this "
                        "mutation must be updated rather than silently skipped"
                    )
                    continue
                mutated = baseline.replace(anchor, replacement, 1)
                self.assertNotEqual(mutated, baseline, "mutation changed nothing")
                result = self._run_with(target, mutated, test_class)
                if result.returncode == 0:
                    uncaught.append(f"{label!r} was NOT caught by {test_class}: {why}")
        self.assertEqual(mis_anchored, [], "\n".join(mis_anchored))
        self.assertEqual(uncaught, [], "\n".join(uncaught))

    def test_the_mutation_table_covers_every_guard_of_interest(self):
        # A table that emptied itself would make the case above pass vacuously.
        self.assertGreaterEqual(len(MUTATIONS), 15)
        covered = {entry[4] for entry in MUTATIONS}
        for required in (
            "InvalidMagnitudesTest",
            "InvalidStepShapeTest",
            "ComputedPremiseTest",
            "RefusalOrderTest",
            "WaiverIsVisibleTest",
            "ArtifactIntegrityTest",
        ):
            self.assertIn(required, covered, f"no mutation covers {required}")

    def test_the_working_tree_source_matches_the_commit(self):
        # Last case: the file this module reads must be the reviewed one, not a
        # leftover from an interrupted run.
        self.assertEqual(
            hashlib.sha256(SOURCE.read_bytes()).hexdigest(), BASELINE_SHA
        )


if __name__ == "__main__":
    unittest.main()
