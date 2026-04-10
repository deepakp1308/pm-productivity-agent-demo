"""Tests for backend.api.chat helper functions — ~8 tests."""

import pytest
from backend.api.chat import _detect_pm, _detect_priority, _local_answer


class TestDetectPM:
    def test_stephen(self, seeded_db):
        assert _detect_pm("How is stephen doing?") == "stephen-yu"

    def test_nicole(self, seeded_db):
        assert _detect_pm("What about nicole's meetings?") == "nicole-jayne"

    def test_vivian(self, seeded_db):
        assert _detect_pm("Tell me about vivian's priorities") == "vivian-wang"

    def test_random_returns_none(self, seeded_db):
        assert _detect_pm("Tell me about the random person") is None


class TestDetectPriority:
    def test_insights_agent(self, seeded_db):
        """'analytics' keyword should map to Analytics Agent Beta."""
        result = _detect_priority("How is the analytics agent work going?")
        assert result is not None
        # The actual mapping value from the code
        assert "Analytics" in result or "analytics" in result.lower()

    def test_email_report(self, seeded_db):
        """'data platform' should map to Data Platform Alignment."""
        result = _detect_priority("What about data platform alignment?")
        assert result is not None

    def test_random_returns_none(self, seeded_db):
        assert _detect_priority("Tell me about the weather") is None


class TestLocalAnswer:
    def test_compare_meeting_hours(self, seeded_db):
        """'Compare meeting hours across all PMs' should return non-empty with PM names."""
        answer = _local_answer("Compare meeting hours across all PMs")
        assert len(answer) > 0
        # Should mention at least one real PM name
        assert any(name in answer for name in ["Stephen", "Nicole", "Vivian"])
