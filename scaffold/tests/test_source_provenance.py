"""Source roles, independence, and the witness-siglum rule."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

from support import build_empty, build_executed, run_validator
from package_files import rebuild_locks, write_json

SCHEMA = json.loads((ROOT / "schemas" / "source_register_entry.schema.json").read_text(encoding="utf-8"))


def _source(**overrides) -> dict:
    entry = {
        "id": "SRC-001",
        "kind": "catalogue record",
        "source_role": "catalogue_transcription",
        "independence_from": [],
        "review_scope": "Fixture entry. Nothing was reviewed.",
        "release_classification": "PUBLICLY_CLEARED",
    }
    entry.update(overrides)
    return entry


class SourceSchemaTests(unittest.TestCase):
    def test_source_role_enum_has_the_eight_roles(self):
        self.assertEqual(
            SCHEMA["properties"]["source_role"]["enum"],
            [
                "catalogue_transcription",
                "manuscript_image_transcription",
                "critical_edition",
                "edition_page_image",
                "secondary_study",
                "dataset",
                "software",
                "other",
            ],
        )

    def test_independence_from_is_a_required_array_of_ids(self):
        self.assertIn("independence_from", SCHEMA["required"])
        self.assertEqual(SCHEMA["properties"]["independence_from"]["type"], "array")
        self.assertEqual(
            SCHEMA["properties"]["independence_from"]["items"]["type"], "string"
        )

    def test_siglum_description_states_the_documentary_requirement(self):
        description = SCHEMA["properties"]["witness_siglum"]["description"].lower()
        self.assertIn("edition itself assigns", description)
        self.assertIn("locator", description)
        self.assertIn("no siglum is assigned by this repository", description)


class SourceValidationTests(unittest.TestCase):
    def _run(self, sources: list[dict]) -> tuple[int, dict, str]:
        with tempfile.TemporaryDirectory() as tmp:
            package = build_empty(Path(tmp) / "programme")
            write_json(package / "sources" / "source_register.json", sources)
            rebuild_locks(package)
            return run_validator(package)

    def test_a_siglum_without_a_locator_is_refused(self):
        code, payload, stderr = self._run(
            [_source(source_role="critical_edition", witness_siglum="A")]
        )
        self.assertNotEqual(code, 0)
        reasons = "\n".join(
            reason
            for check in payload["checks"]
            if check["check"] == "traceability"
            for reason in check["reasons"]
        )
        self.assertIn("records a witness_siglum without a locator", reasons)

    def test_a_locator_without_a_siglum_is_refused(self):
        code, payload, stderr = self._run(
            [_source(witness_siglum_locator="p. 00 (fixture locator)")]
        )
        self.assertNotEqual(code, 0)
        reasons = "\n".join(
            reason
            for check in payload["checks"]
            if check["check"] == "traceability"
            for reason in check["reasons"]
        )
        self.assertIn("records a witness_siglum_locator without a witness_siglum", reasons)

    def test_a_siglum_on_a_non_edition_role_is_refused(self):
        code, payload, stderr = self._run(
            [
                _source(
                    source_role="catalogue_transcription",
                    witness_siglum="A",
                    witness_siglum_locator="p. 00 (fixture locator)",
                )
            ]
        )
        self.assertNotEqual(code, 0)
        reasons = "\n".join(
            reason
            for check in payload["checks"]
            if check["check"] == "traceability"
            for reason in check["reasons"]
        )
        self.assertIn("only the citing edition may assign a siglum", reasons)

    def test_an_edition_assigned_siglum_with_a_locator_is_accepted(self):
        code, payload, stderr = self._run(
            [
                _source(
                    source_role="critical_edition",
                    witness_siglum="A",
                    witness_siglum_locator="p. 00 (fixture locator)",
                )
            ]
        )
        self.assertEqual(code, 0, stderr + json.dumps(payload, indent=2))

    def test_independence_from_must_resolve(self):
        code, payload, stderr = self._run(
            [_source(independence_from=["SRC-999"])]
        )
        self.assertNotEqual(code, 0)
        reasons = "\n".join(
            reason
            for check in payload["checks"]
            if check["check"] == "traceability"
            for reason in check["reasons"]
        )
        self.assertIn("independence_from names SRC-999", reasons)

    def test_a_source_may_not_be_independent_of_itself(self):
        code, payload, stderr = self._run([_source(independence_from=["SRC-001"])])
        self.assertNotEqual(code, 0)
        reasons = "\n".join(
            reason
            for check in payload["checks"]
            if check["check"] == "traceability"
            for reason in check["reasons"]
        )
        self.assertIn("lists itself in independence_from", reasons)

    def test_a_transcription_declaring_its_edition_is_accepted(self):
        code, payload, stderr = self._run(
            [
                _source(id="SRC-001", source_role="critical_edition"),
                _source(
                    id="SRC-002",
                    kind="transcription",
                    source_role="manuscript_image_transcription",
                    independence_from=["SRC-001"],
                    review_scope="Fixture transcription that consulted the edition.",
                ),
            ]
        )
        self.assertEqual(code, 0, stderr + json.dumps(payload, indent=2))


class ProvenanceDocTests(unittest.TestCase):
    doc = (ROOT / "SOURCE_PROVENANCE.md").read_text(encoding="utf-8")

    def test_documents_the_three_roles_and_their_separation(self):
        self.assertIn("catalogue_transcription", self.doc)
        self.assertIn("manuscript_image_transcription", self.doc)
        self.assertIn("critical_edition", self.doc)
        self.assertIn("never cited as though they were each other", self.doc)

    def test_does_not_assign_a_siglum(self):
        self.assertIn("No siglum is assigned by this repository", self.doc)
        self.assertIn("Do not invent one", self.doc)

    def test_records_the_instantiation_with_both_counts_and_scopes(self):
        self.assertIn("Add MS 7527", self.doc)
        self.assertIn("Qatar Digital Library", self.doc)
        self.assertIn("QDL_Add_MS_7527_Complete_Codex.pdf", self.doc)
        self.assertIn("384", self.doc)
        self.assertIn("320", self.doc)
        self.assertIn("ff. 2v–170r", self.doc)
        self.assertIn("Three treatises on natural philosophy and medicine", self.doc)
        self.assertIn("different scopes", self.doc)
        # The two counts must not be presented as one number.
        self.assertNotIn("384-item", self.doc)
        self.assertNotIn("704", self.doc)

    def test_names_weisser_1979_as_a_separate_edition(self):
        self.assertIn("Weisser", self.doc)
        self.assertIn("1979", self.doc)


if __name__ == "__main__":
    unittest.main()
