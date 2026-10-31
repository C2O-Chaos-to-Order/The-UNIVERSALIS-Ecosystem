"""Stage P3. Requirement identifiers are ULC-<tablet>-<clause>."""

import unittest

import bootstrap  # noqa: F401
from support import CORPUS, SOURCE, T0, ingest, memory_store, register_basics

from universalis.errors import (
    DegradedPresentedAsComplete,
    FabricationRefused,
    FailedRouteIsNotEmpty,
    TruncationPresentedAsComplete,
)
from universalis.failures import (
    RouteRequest,
    RouteResult,
    fabricate_result,
    label_complete,
    present_as_empty,
    resolve,
)
from universalis.states import RouteOutcome


class StageP3FailuresTest(unittest.TestCase):
    def setUp(self):
        self.store = register_basics(memory_store())
        self.records = [
            ingest(self.store, assertion_text=f"account {index}", member_id=f"m{index}")
            for index in (1, 2, 3)
        ]

    def _request(self, **overrides) -> RouteRequest:
        fields = {"corpus_id": CORPUS, "recorded_at": T0}
        fields.update(overrides)
        return RouteRequest(**fields)

    def test_ulc_21_06_six_causes_produce_six_outcomes(self):
        results = {
            "empty": resolve(self.store, self._request(query_text="nothing-matches")),
            "missing": resolve(self.store, self._request(record_id="absent-record")),
            "failed_request": resolve(self.store, self._request(route_failed=True)),
            "truncated": resolve(self.store, self._request(budget=1)),
            "denied": resolve(
                self.store,
                self._request(authorized=False, path_visible=True, query_text="account"),
            ),
            "unavailable": resolve(self.store, self._request(source_id="missing-source")),
        }
        self.assertEqual(set(results), {item.value for item in RouteOutcome if item is not RouteOutcome.OK})
        for name, result in results.items():
            self.assertEqual(result.outcome, name)
        self.assertEqual(len({result.outcome for result in results.values()}), 6)

    def test_ulc_21_06_failed_route_is_never_empty(self):
        failed = resolve(self.store, self._request(route_failed=True, query_text="nothing-matches"))
        self.assertEqual(failed.outcome, "failed_request")
        self.assertNotEqual(failed.transport, "empty")
        with self.assertRaises(FailedRouteIsNotEmpty):
            present_as_empty(failed)
        for outcome in ("missing", "failed_request", "truncated", "denied", "unavailable"):
            with self.assertRaises(FailedRouteIsNotEmpty):
                RouteResult(
                    outcome=outcome,
                    transport="empty",
                    records=(),
                    omitted_count=1,
                    omitted_ids=("x",),
                    omission_note="named",
                    complete=False,
                    source_id=None,
                    detail="attempted alias to empty",
                )
        empty = resolve(self.store, self._request(query_text="nothing-matches"))
        self.assertIs(present_as_empty(empty), empty)

    def test_ulc_21_06_truncated_response_is_not_presented_as_complete(self):
        result = resolve(self.store, self._request(budget=1))
        self.assertEqual(result.outcome, "truncated")
        self.assertFalse(result.complete)
        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.omitted_count, 2)
        self.assertEqual(len(result.omitted_ids), 2)
        with self.assertRaises(TruncationPresentedAsComplete):
            RouteResult(
                outcome="truncated",
                transport="truncated",
                records=result.records,
                omitted_count=result.omitted_count,
                omitted_ids=result.omitted_ids,
                omission_note=result.omission_note,
                complete=True,
                source_id=None,
                detail="looks complete",
            )
        with self.assertRaises(DegradedPresentedAsComplete):
            label_complete(result)

    def test_ulc_16_07_unresolved_source_is_failure_not_a_fabricated_answer(self):
        before = len(self.store.records_in_corpus(CORPUS, current_only=False))
        result = resolve(
            self.store,
            self._request(source_id=SOURCE, source_version="1", resolve_hops=5),
        )
        self.assertEqual(result.outcome, "unavailable")
        self.assertEqual(result.records, ())
        self.assertIn("no answer was synthesised", result.omission_note)
        after = len(self.store.records_in_corpus(CORPUS, current_only=False))
        self.assertEqual(before, after)

    def test_ulc_16_07_fabrication_is_a_hard_error(self):
        with self.assertRaises(FabricationRefused):
            fabricate_result(self._request(source_id="missing-source"))

    def test_ulc_16_12_timeout_and_budget_name_omissions(self):
        timed_out = resolve(
            self.store,
            self._request(query_text="nothing-matches", timed_out=True),
        )
        self.assertEqual(timed_out.outcome, "failed_request")
        self.assertIn("deadline", timed_out.omission_note)
        self.assertFalse(timed_out.complete)
        self.assertNotEqual(timed_out.outcome, "empty")
        budget = resolve(self.store, self._request(budget=1))
        self.assertEqual(budget.outcome, "truncated")
        self.assertEqual(set(budget.omitted_ids), {self.records[1].record_id, self.records[2].record_id})
        self.assertIn("omitted", budget.omission_note)

    def test_ulc_16_12_degraded_result_cannot_be_labelled_complete(self):
        denied = resolve(self.store, self._request(authorized=False, path_visible=True))
        self.assertEqual(denied.outcome, "denied")
        self.assertFalse(denied.complete)
        self.assertIn("visibility", denied.detail)
        with self.assertRaises(DegradedPresentedAsComplete):
            label_complete(denied)


if __name__ == "__main__":
    unittest.main()
