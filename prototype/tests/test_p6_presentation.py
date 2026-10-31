"""Stage P6. The corrected plan assigns ULC-21-01, ULC-21-03, and ULC-21-09 here."""

import unittest

import bootstrap  # noqa: F401

from universalis.errors import (
    ColourAloneRefused,
    IncompleteClaimRendering,
    StatusAnnouncementRequired,
    StatusIncomplete,
    VocabularyBoundaryError,
)
from universalis.presentation import (
    Status,
    announce_status_change,
    render_claim,
    render_status,
    render_status_change,
    status_from_colour,
)
from universalis.states import EvidenceState, TransportOutcome


class StageP6PresentationTest(unittest.TestCase):
    def test_ulc_21_03_status_requires_text_and_machine_value(self):
        status = Status("supported", "Supported")
        rendered = render_status(status)
        self.assertIn("Supported", rendered.text)
        self.assertIn("supported", rendered.text)
        self.assertEqual(rendered.machine_value, "supported")
        self.assertEqual(rendered.text_label, "Supported")
        with self.assertRaises(StatusIncomplete):
            Status("", "Supported")
        with self.assertRaises(StatusIncomplete):
            Status("supported", " ")

    def test_ulc_21_03_colour_alone_cannot_construct_a_status(self):
        with self.assertRaises(ColourAloneRefused):
            status_from_colour("red")
        with self.assertRaises(ColourAloneRefused):
            render_status(colour="red")

    def test_ulc_21_09_status_change_is_announced_in_text(self):
        previous = Status("disputed", "Disputed")
        current = Status("pending_review", "Pending review")
        change = announce_status_change(
            previous,
            current,
            "The status changed from disputed to pending review.",
        )
        rendered = render_status_change(change)
        self.assertIn("The status changed from disputed to pending review.", rendered)
        self.assertIn("disputed", rendered)
        self.assertIn("pending_review", rendered)
        with self.assertRaises(StatusAnnouncementRequired):
            announce_status_change(previous, current, " ")

    def test_ulc_21_09_rendering_does_not_depend_on_colour(self):
        status = Status("missing", "Missing")
        red = render_status(status, colour="red")
        blue = render_status(status, colour="blue")
        none = render_status(status)
        self.assertEqual(red.text, blue.text)
        self.assertEqual(red.text, none.text)
        self.assertEqual(red.machine_value, "missing")
        self.assertNotEqual(red.colour_supplement, blue.colour_supplement)

    def test_ulc_21_01_claim_rendering_includes_state_reason_and_source(self):
        rendered = render_claim(
            claim_id="c1",
            evidence_state=EvidenceState.DISPUTED,
            reason="two witnesses disagree",
            source_trace="record:abc witness:w1",
        )
        self.assertIn("disputed", rendered.text)
        self.assertIn("two witnesses disagree", rendered.text)
        self.assertIn("record:abc witness:w1", rendered.text)
        self.assertFalse(rendered.presented_as_resolution)
        with self.assertRaises(IncompleteClaimRendering):
            render_claim(
                claim_id="c1",
                evidence_state=EvidenceState.DISPUTED,
                reason="",
                source_trace="record:abc",
            )
        with self.assertRaises(VocabularyBoundaryError):
            render_claim(
                claim_id="c1",
                evidence_state=TransportOutcome.FAILED_REQUEST,
                reason="a failure",
                source_trace="route",
            )

    def test_ulc_21_01_readability_is_not_resolution(self):
        rendered = render_claim(
            claim_id="c1",
            evidence_state="disputed",
            reason="still disputed",
            source_trace="record:abc",
            readable=True,
        )
        self.assertEqual(rendered.evidence_state, "disputed")
        self.assertFalse(rendered.presented_as_resolution)
        self.assertIn("disputed", rendered.text)


if __name__ == "__main__":
    unittest.main()
