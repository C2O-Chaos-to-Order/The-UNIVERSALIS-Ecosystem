"""Wave 1 remediation N03: an unregistered corpus is never a complete empty result.

Audit finding N03 (2026-11-07): ``resolve`` on a corpus id that was never
registered returned ``outcome='empty', complete=True`` -- a false green that
reports "nothing exists" for a scope nobody declared. These regressions pin the
corrected behaviour: an unknown corpus is refused as ``unavailable`` and
incomplete, while a registered corpus that genuinely matches nothing may still
be an honest ``empty``.
"""

import unittest

import bootstrap  # noqa: F401
from support import CORPUS, T0, ingest, memory_store, register_basics

from universalis.errors import DegradedPresentedAsComplete, FailedRouteIsNotEmpty
from universalis.failures import RouteRequest, label_complete, present_as_empty, resolve


class W1N03UnknownCorpusTest(unittest.TestCase):
    def setUp(self):
        self.store = register_basics(memory_store())

    def tearDown(self):
        self.store.close()

    def test_unknown_corpus_is_not_complete_empty(self):
        result = resolve(self.store, RouteRequest(corpus_id="no-such-corpus", recorded_at=T0))
        self.assertNotEqual(result.outcome, "empty")
        self.assertFalse(result.complete)
        self.assertNotEqual(result.transport, "empty")

    def test_unknown_corpus_is_unavailable_and_names_the_omission(self):
        result = resolve(self.store, RouteRequest(corpus_id="no-such-corpus", recorded_at=T0))
        self.assertEqual(result.outcome, "unavailable")
        self.assertIn("no-such-corpus", result.omission_note)
        self.assertEqual(result.records, ())
        with self.assertRaises(FailedRouteIsNotEmpty):
            present_as_empty(result)
        with self.assertRaises(DegradedPresentedAsComplete):
            label_complete(result)

    def test_unknown_corpus_with_query_or_member_is_still_unavailable(self):
        for extra in ({"query_text": "anything"}, {"member_id": "m1"}, {"record_id": "r1"}):
            with self.subTest(extra=extra):
                result = resolve(
                    self.store, RouteRequest(corpus_id="no-such-corpus", recorded_at=T0, **extra)
                )
                self.assertEqual(result.outcome, "unavailable")
                self.assertFalse(result.complete)

    def test_denial_still_precedes_corpus_resolution(self):
        # An unauthorized caller must not learn whether a corpus id exists.
        result = resolve(
            self.store,
            RouteRequest(corpus_id="no-such-corpus", authorized=False, recorded_at=T0),
        )
        self.assertEqual(result.outcome, "denied")

    def test_registered_corpus_that_matches_nothing_is_still_honest_empty(self):
        ingest(self.store, assertion_text="account one", member_id="m1")
        result = resolve(
            self.store, RouteRequest(corpus_id=CORPUS, query_text="nothing-matches", recorded_at=T0)
        )
        self.assertEqual(result.outcome, "empty")
        self.assertTrue(result.complete)

    def test_registered_corpus_with_no_records_is_honest_empty(self):
        result = resolve(self.store, RouteRequest(corpus_id=CORPUS, recorded_at=T0))
        self.assertEqual(result.outcome, "empty")
        self.assertTrue(result.complete)


class W1N03MutationTest(unittest.TestCase):
    """Mutation check: removing the corpus guard must turn the regression red."""

    def test_disabling_corpus_guard_revives_the_false_green(self):
        import universalis.failures as failures

        original = failures._corpus_registered
        failures._corpus_registered = lambda store, corpus_id: True  # mutant
        try:
            outcome = unittest.TestResult()
            unittest.defaultTestLoader.loadTestsFromName(
                "test_unknown_corpus_is_not_complete_empty", W1N03UnknownCorpusTest
            ).run(outcome)
        finally:
            failures._corpus_registered = original
        self.assertEqual(outcome.testsRun, 1)
        self.assertEqual(len(outcome.errors), 0, outcome.errors)
        self.assertEqual(len(outcome.failures), 1, "mutant survived: guard removal not detected")
        self.assertIn("AssertionError", outcome.failures[0][1])


if __name__ == "__main__":
    unittest.main()
