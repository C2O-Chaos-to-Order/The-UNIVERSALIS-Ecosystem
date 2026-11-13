import json
import tempfile
import unittest
from pathlib import Path

from construction_engine.engine import BuildError, build, load_spec, validate_spec, verify


class ConstructionEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.spec_path = Path(__file__).parents[1] / "examples" / "hello-tool.json"

    def tearDown(self):
        self.temp.cleanup()

    def test_build_and_verify(self):
        output = self.root / "out"
        record = build(self.spec_path, output)
        self.assertEqual(record["status"], "BUILT_NOT_PROMOTED")
        result = verify(output)
        self.assertTrue(result["ok"])
        self.assertEqual(result["checked"], 2)

    def test_tamper_is_detected(self):
        output = self.root / "out"
        build(self.spec_path, output)
        (output / "hello_tool" / "README.md").write_text("tampered", encoding="utf-8")
        self.assertFalse(verify(output)["ok"])

    def test_path_traversal_rejected(self):
        spec = {
            "spec_version": "c2o-build-spec/v0.1",
            "tool_id": "bad-tool",
            "name": "Bad",
            "version": "0",
            "target_ecosystem": "universalis",
            "files": [{"path": "../escape.txt", "content": "no"}],
        }
        with self.assertRaises(BuildError):
            validate_spec(spec)

    def test_wrong_target_rejected(self):
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        spec["target_ecosystem"] = "everywhere"
        with self.assertRaises(BuildError):
            validate_spec(spec)

    def test_spec_loads(self):
        self.assertEqual(load_spec(self.spec_path)["tool_id"], "hello-tool")


if __name__ == "__main__":
    unittest.main()
