
import tempfile
import unittest
from pathlib import Path

from engineering_doctor.cli import main
from engineering_doctor.config import RuntimeConfig
from engineering_doctor.constants import BANNER
from engineering_doctor.github_client import GitHubClient
from engineering_doctor.run import RunRequest, execute


class RunTests(unittest.TestCase):
    def test_excluded_request_is_refused_and_recorded(self) -> None:
        config = RuntimeConfig(
            allowlist=("example-one",),
            excluded=("example-excluded",),
            suite_adapters=(),
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = execute(
                RunRequest(
                    output_dir=Path(tmp),
                    repos=["example-excluded"],
                    skip_suites=True,
                    skip_inventory=True,
                    config=config,
                )
            )
            self.assertTrue(result["scope_refused"])
            titles = [item.title for item in result["findings"]]
            self.assertTrue(any("outside scope" in title for title in titles))
            brief = result["brief"]
            self.assertIn(BANNER, brief)
            self.assertIn("LIMITED", brief)
            self.assertIn("PUBLIC_CANDIDATE", brief)
            self.assertNotIn("93%", brief)
            self.assertNotIn("confidence:", brief.lower())
            self.assertNotRegex(brief, r"Confidence:\s*\d")

    def test_cli_excluded_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code = main(
                [
                    "run",
                    "--output-dir",
                    tmp,
                    "--exclude",
                    "example-excluded",
                    "--repo",
                    "example-excluded",
                    "--skip-suites",
                    "--skip-inventory",
                ]
            )
            self.assertEqual(code, 2)

    def test_mocked_inventory_run_writes_outputs_outside_repo_by_default(self) -> None:
        def fetch(url: str, headers: dict[str, str]):
            return 500, {}, b'{"message":"nope"}'

        config = RuntimeConfig(suite_adapters=())
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out"
            result = execute(
                RunRequest(
                    output_dir=output,
                    repos=["example-public"],
                    skip_suites=True,
                    client=GitHubClient(fetch=fetch),
                    config=config,
                )
            )
            self.assertTrue(Path(result["paths"]["brief"]).is_file())
            self.assertTrue(Path(result["paths"]["record"]).is_file())
            statuses = [item["query_status"] for item in result["record"]["inventory"]]
            self.assertEqual(statuses, ["UNKNOWN"])
            self.assertNotIn("example-public", result["record"]["repo_shas"])
            self.assertIn("example-public", result["record"]["unresolved_repo_shas"])
            self.assertNotIn(None, result["record"]["repo_shas"].values())
            self.assertNotIn("working-tree", result["record"]["repo_shas"].values())
            self.assertIn(BANNER, result["record"]["banner"])
            self.assertEqual(result["record"]["classification"], "PUBLIC_CANDIDATE")
