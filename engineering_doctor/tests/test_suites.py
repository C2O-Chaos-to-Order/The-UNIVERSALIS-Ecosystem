
import tempfile
import unittest
from pathlib import Path

from engineering_doctor.suites import parse_unittest_output, run_suite_adapter


OK_OUTPUT = """\
test_one (test_mod.T.test_one) ... ok
test_two (test_mod.T.test_two) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.001s

OK
"""

SKIP_OUTPUT = """\
test_one (test_mod.T.test_one) ... ok
test_optional_external_resource (test_mod.T) ... skipped 'resource unset'

----------------------------------------------------------------------
Ran 147 tests in 0.200s

OK (skipped=1)
"""

FAIL_OUTPUT = """\
test_one (test_mod.T.test_one) ... FAIL

======================================================================
FAIL: test_one
----------------------------------------------------------------------
Ran 4 tests in 0.010s

FAILED (failures=1, errors=1, skipped=1)
"""


class ParseUnittestTests(unittest.TestCase):
    def test_ok_two_passed(self) -> None:
        parsed = parse_unittest_output(OK_OUTPUT)
        self.assertEqual(parsed.discovered, 2)
        self.assertEqual(parsed.passed, 2)
        self.assertEqual(parsed.skipped, 0)
        self.assertTrue(parsed.healthy_banner)
        self.assertTrue(parsed.reconciled())

    def test_ok_with_skip_reconciles(self) -> None:
        parsed = parse_unittest_output(SKIP_OUTPUT)
        self.assertEqual(parsed.discovered, 147)
        self.assertEqual(parsed.passed, 146)
        self.assertEqual(parsed.skipped, 1)
        self.assertTrue(parsed.reconciled())

    def test_failed_banner_reconciles(self) -> None:
        parsed = parse_unittest_output(FAIL_OUTPUT)
        self.assertEqual(parsed.discovered, 4)
        self.assertEqual(parsed.passed, 1)
        self.assertEqual(parsed.failed, 1)
        self.assertEqual(parsed.errors, 1)
        self.assertEqual(parsed.skipped, 1)
        self.assertFalse(parsed.healthy_banner)

    def test_corrupted_output_is_not_a_pass(self) -> None:
        with self.assertRaises(ValueError):
            parse_unittest_output("this is not unittest output")

    def test_ran_without_banner_is_not_a_pass(self) -> None:
        with self.assertRaises(ValueError):
            parse_unittest_output("Ran 4 tests in 0.1s\n\nno banner here\n")

    def test_zero_tests_parses_but_is_empty(self) -> None:
        parsed = parse_unittest_output("Ran 0 tests in 0.000s\n\nOK\n")
        self.assertEqual(parsed.discovered, 0)
        self.assertEqual(parsed.passed, 0)


class SuiteRunnerTests(unittest.TestCase):
    def _init_repo(self, root: Path, body: str) -> str:
        import subprocess

        tests = root / "prototype" / "tests"
        tests.mkdir(parents=True)
        (root / ".gitignore").write_text("__pycache__/\n*.pyc\n", encoding="utf-8")
        (tests / "test_sample.py").write_text(body, encoding="utf-8")
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "doctor@example.test"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Doctor Tests"], check=True)
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(root), "commit", "-m", "fixture"], check=True, capture_output=True)
        sha = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return sha

    def test_positive_suite_and_timeout_and_zero_tests(self) -> None:
        passing = (
            "import unittest\n"
            "class T(unittest.TestCase):\n"
            "    def test_ok(self):\n"
            "        self.assertTrue(True)\n"
        )
        empty_note = "# no tests here\n"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            src = tmp_path / "src"
            src.mkdir()
            sha = self._init_repo(src, passing)

            def cloner(repo: str, requested_sha: str, dest: Path) -> str:
                import shutil

                shutil.copytree(src, dest)
                return sha

            adapter = {
                "id": "tiny-ok",
                "repo": "example-public",
                "pinned_sha": sha,
                "workdir": ".",
                "argv_suffix": ("-m", "unittest", "discover", "-s", "prototype/tests", "-v"),
            }
            result = run_suite_adapter(adapter, scratch_root=tmp_path / "scratch", cloner=cloner)
            self.assertEqual(result.status, "ok")
            self.assertEqual(result.discovered, 1)
            self.assertEqual(result.passed, 1)
            self.assertEqual(result.porcelain_after, "")

            timeout_adapter = dict(adapter)
            timeout_adapter["id"] = "tiny-timeout"
            timeout_adapter["argv_suffix"] = ("-c", "import time; time.sleep(5)")
            timed = run_suite_adapter(
                timeout_adapter,
                scratch_root=tmp_path / "scratch-timeout",
                cloner=cloner,
                timeout_sec=1,
            )
            self.assertEqual(timed.status, "TIMEOUT")
            self.assertTrue(timed.timeout)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            src = tmp_path / "src"
            src.mkdir()
            sha = self._init_repo(src, empty_note)

            def cloner(repo: str, requested_sha: str, dest: Path) -> str:
                import shutil

                shutil.copytree(src, dest)
                return sha

            adapter = {
                "id": "tiny-zero",
                "repo": "example-public",
                "pinned_sha": sha,
                "workdir": ".",
                "argv_suffix": ("-m", "unittest", "discover", "-s", "prototype/tests", "-v"),
            }
            zero = run_suite_adapter(adapter, scratch_root=tmp_path / "scratch", cloner=cloner)
            self.assertIn(zero.status, {"ZERO_TESTS", "PARSE_ERROR"})
            self.assertNotEqual(zero.status, "ok")
