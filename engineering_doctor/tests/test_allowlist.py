
import json
import tempfile
import unittest
from pathlib import Path

from engineering_doctor.allowlist import (
    ScopeError,
    is_allowlisted,
    is_excluded,
    load_name_file,
    validate_requested_repos,
)
from engineering_doctor.config import RuntimeConfig


class AllowlistTests(unittest.TestCase):
    def test_default_allowlist_is_empty(self) -> None:
        config = RuntimeConfig()
        self.assertEqual(config.allowlist, ())
        self.assertEqual(config.excluded, ())
        self.assertEqual(
            validate_requested_repos(None, allowlist=config.allowlist, excluded=config.excluded),
            [],
        )

    def test_operator_repos_accepted_when_allowlist_empty(self) -> None:
        self.assertEqual(
            validate_requested_repos(
                ["example-one", "example-two"],
                allowlist=(),
                excluded=(),
            ),
            ["example-one", "example-two"],
        )

    def test_excluded_name_is_refused(self) -> None:
        with self.assertRaises(ScopeError) as ctx:
            validate_requested_repos(
                ["example-excluded"],
                allowlist=("example-one",),
                excluded=("example-excluded",),
            )
        self.assertIn("explicitly excluded", str(ctx.exception))

    def test_unknown_name_refused_when_allowlist_configured(self) -> None:
        with self.assertRaises(ScopeError):
            validate_requested_repos(
                ["not-listed"],
                allowlist=("example-one",),
                excluded=(),
            )

    def test_allowlisted_name_is_accepted(self) -> None:
        chosen = ["example-one"]
        self.assertEqual(
            validate_requested_repos(
                chosen,
                allowlist=("example-one", "example-two"),
                excluded=(),
            ),
            chosen,
        )
        self.assertTrue(is_allowlisted("example-one", ("example-one",)))
        self.assertTrue(is_excluded("example-excluded", ("example-excluded",)))

    def test_empty_request_returns_configured_allowlist(self) -> None:
        names = ("example-one", "example-two")
        self.assertEqual(
            validate_requested_repos(None, allowlist=names, excluded=()),
            list(names),
        )

    def test_load_name_file_json_and_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "allow.json"
            json_path.write_text(json.dumps(["example-one", "example-two"]), encoding="utf-8")
            text_path = Path(tmp) / "allow.txt"
            text_path.write_text("# comment\nexample-one\nexample-two\n", encoding="utf-8")
            self.assertEqual(load_name_file(json_path), ["example-one", "example-two"])
            self.assertEqual(load_name_file(text_path), ["example-one", "example-two"])
