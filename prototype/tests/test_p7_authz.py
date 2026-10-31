"""Stage P7. The corrected plan assigns the authorization requirements here.

This file exercises an in-memory stub. The stub proves nothing about a real
identity provider. ULC-00-12 is only partial here: a stub permit is not readiness.
"""

import unittest

import bootstrap  # noqa: F401
from support import T0, memory_store

from universalis.authz import (
    STUB_NOTICE,
    InMemoryAuthorizationStub,
    readiness_from_stub,
)
from universalis.errors import (
    AnalogyCannotPopulateSource,
    AuthorizationNotImplied,
    ReadinessRefused,
    SourceNotScopedOrigin,
    ToolingStatusForbidden,
)
from universalis.states import Readiness, assert_readiness, tooling_set_evidence_status


class StageP7AuthorizationTest(unittest.TestCase):
    def test_ulc_16_11_each_authorization_dimension_is_checked(self):
        stub = InMemoryAuthorizationStub()
        granted = {
            "principal": "ada",
            "purpose": "research",
            "project": "corpus-1",
            "credential": "stub-token",
            "action": "read",
        }
        stub.grant(**granted)
        for missing in granted:
            fields = dict(granted)
            fields[missing] = None
            decision = stub.authorize(**fields)
            self.assertFalse(decision.permitted)
            self.assertIn(missing, decision.failed_dimensions)
            self.assertIn(STUB_NOTICE, decision.notice)
        permitted = stub.authorize(**granted)
        self.assertTrue(permitted.permitted)
        self.assertTrue(permitted.stub)
        self.assertIn("proves nothing", permitted.notice)
        wrong_credential = dict(granted)
        wrong_credential["credential"] = "other-token"
        self.assertFalse(stub.authorize(**wrong_credential).permitted)

    def test_ulc_16_11_visible_path_is_not_permission(self):
        stub = InMemoryAuthorizationStub()
        stub.show_path("/corpus/1")
        decision = stub.authorize(
            principal="ada",
            purpose="research",
            project="corpus-1",
            credential="stub-token",
            action="read",
            path="/corpus/1",
        )
        self.assertTrue(decision.path_visible)
        self.assertFalse(decision.permitted)
        self.assertIn("visible", decision.reason)
        self.assertIn(STUB_NOTICE, repr(stub))

    def test_ulc_26_03_one_action_does_not_authorize_an_adjacent_action(self):
        stub = InMemoryAuthorizationStub()
        stub.grant(
            principal="ada",
            purpose="research",
            project="corpus-1",
            credential="stub-token",
            action="read",
        )
        read = stub.authorize(
            principal="ada",
            purpose="research",
            project="corpus-1",
            credential="stub-token",
            action="read",
        )
        write = stub.authorize(
            principal="ada",
            purpose="research",
            project="corpus-1",
            credential="stub-token",
            action="write",
        )
        self.assertTrue(read.permitted)
        self.assertFalse(write.permitted)

    def test_ulc_26_05_declining_a_suggestion_reduces_nothing_else(self):
        stub = InMemoryAuthorizationStub()
        stub.grant(
            principal="ada",
            purpose="research",
            project="corpus-1",
            credential="stub-token",
            action="read",
        )
        before_standing = {
            "access": dict(stub.standing["access"]),
            "data": dict(stub.standing["data"]),
            "standing": stub.standing["standing"],
            "debt": stub.standing["debt"],
        }
        before_grants = set(stub._grants)
        declined = stub.decline_suggestion(principal="ada", suggestion_id="optional-summary")
        self.assertEqual(declined["debt"], 0)
        self.assertTrue(declined["standing_unchanged"])
        self.assertEqual(stub.standing["debt"], 0)
        self.assertEqual(stub.standing["access"], before_standing["access"])
        self.assertEqual(stub.standing["data"], before_standing["data"])
        self.assertEqual(stub.standing["standing"], before_standing["standing"])
        self.assertEqual(stub._grants, before_grants)
        self.assertEqual(len(stub.declines()), 1)

    def test_ulc_00_11_a_passing_test_does_not_supply_authorization(self):
        stub = InMemoryAuthorizationStub()
        with self.assertRaises(AuthorizationNotImplied):
            stub.authorize_from_passing_test(test_passed=True, principal="ada")

    def test_ulc_00_11_a_mapping_does_not_supply_authorization(self):
        stub = InMemoryAuthorizationStub()
        with self.assertRaises(AuthorizationNotImplied):
            stub.authorize_from_mapping({"ada": "read"})

    def test_ulc_00_11_an_equation_does_not_supply_authorization(self):
        stub = InMemoryAuthorizationStub()
        with self.assertRaises(AuthorizationNotImplied):
            stub.authorize_from_equation("a=b")

    def test_ulc_16_05_analogy_cannot_populate_a_source(self):
        store = memory_store()
        for kind in ("analogy", "metaphor"):
            with self.assertRaises(AnalogyCannotPopulateSource):
                store.register_source(
                    source_id="s",
                    version="1",
                    identity="a figure of speech",
                    digest="digest",
                    retrieval_time=T0,
                    review_scope="none",
                    provenance="figurative",
                    kind=kind,
                )
        with self.assertRaises(AnalogyCannotPopulateSource):
            store.register_source(
                source_id="s",
                version="1",
                identity="origin",
                digest="digest",
                retrieval_time=T0,
                review_scope="full",
                provenance="pinned",
                figurative=True,
            )
        self.assertIsNone(store.get_source("s"))

    def test_ulc_16_05_source_must_be_a_scoped_origin(self):
        store = memory_store()
        with self.assertRaises(SourceNotScopedOrigin):
            store.register_source(
                source_id="s",
                version="1",
                identity="origin",
                digest="",
                retrieval_time=T0,
                review_scope="full",
                provenance="",
            )
        self.assertIsNone(store.get_source("s"))

    def test_ulc_00_12_stub_permission_is_not_readiness(self):
        stub = InMemoryAuthorizationStub()
        stub.grant(
            principal="ada",
            purpose="research",
            project="corpus-1",
            credential="stub-token",
            action="read",
        )
        decision = stub.authorize(
            principal="ada",
            purpose="research",
            project="corpus-1",
            credential="stub-token",
            action="read",
        )
        readiness = readiness_from_stub(decision)
        self.assertIs(readiness, Readiness.UNEXECUTED)
        with self.assertRaises(ReadinessRefused):
            assert_readiness(readiness, evaluated=True, passing=True)
        self.assertEqual(tooling_set_evidence_status("executed"), "executed")
        for forbidden in ("reviewed", "accepted", "authorized"):
            with self.assertRaises(ToolingStatusForbidden):
                tooling_set_evidence_status(forbidden)


if __name__ == "__main__":
    unittest.main()
