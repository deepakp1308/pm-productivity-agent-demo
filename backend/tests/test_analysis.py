"""Tests for backend.analysis.engine — ~10 tests."""

import pytest
from backend.analysis.engine import compute_pm_summary, compute_dashboard, detect_anomalies


class TestComputePmSummary:
    def test_returns_correct_structure(self, seeded_db):
        """compute_pm_summary should return all required keys."""
        s = compute_pm_summary("stephen-yu")
        required_keys = [
            "pm_id", "pm_name", "total_activities", "meetings", "messages",
            "emails", "tickets", "alignment_pct", "top_priority",
            "meeting_hours", "fragmentation_score", "source_breakdown",
            "type_breakdown", "priority_breakdown",
        ]
        for key in required_keys:
            assert key in s, f"Missing key: {key}"

    def test_alignment_pct_range(self, seeded_db):
        """alignment_pct must be between 0 and 100."""
        for pm_id in ["stephen-yu", "nicole-jayne", "vivian-wang"]:
            s = compute_pm_summary(pm_id)
            assert 0 <= s["alignment_pct"] <= 100, (
                f"{pm_id} alignment_pct={s['alignment_pct']} out of range"
            )

    def test_meeting_hours_matches_calendar(self, seeded_db):
        """meeting_hours should equal the sum of calendar activity durations / 60."""
        from backend.storage import db
        acts = db.get_activities(pm_id="stephen-yu", source="calendar", limit=5000)
        # The engine uses duration_minutes if present, else estimates 30 for calendar
        total_min = sum(a.get("duration_minutes") or 30 for a in acts)
        s = compute_pm_summary("stephen-yu")
        # Allow small float rounding tolerance
        assert abs(s["meeting_hours"] - total_min / 60.0) < 0.5

    def test_source_breakdown_sums_to_total(self, seeded_db):
        """Sum of source_breakdown values should equal total_activities."""
        s = compute_pm_summary("stephen-yu")
        breakdown_sum = sum(s["source_breakdown"].values())
        assert breakdown_sum == s["total_activities"]

    def test_fragmentation_score_non_negative(self, seeded_db):
        """fragmentation_score must be >= 0."""
        s = compute_pm_summary("nicole-jayne")
        assert s["fragmentation_score"] >= 0

    def test_empty_pm_returns_defaults(self, seeded_db):
        """A non-existent PM should return graceful defaults."""
        s = compute_pm_summary("nonexistent-pm")
        assert s["total_activities"] == 0
        assert s["alignment_pct"] == 0


class TestComputeDashboard:
    def test_dashboard_has_required_fields(self, seeded_db):
        """Dashboard result should have team_balance_score, pm_summaries, top_insight."""
        d = compute_dashboard()
        assert "team_balance_score" in d
        assert "pm_summaries" in d
        assert "top_insight" in d
        assert len(d["pm_summaries"]) == 3

    def test_dashboard_total_activities_positive(self, seeded_db):
        """Dashboard total_activities should be > 0 after seeding."""
        d = compute_dashboard()
        assert d["total_activities"] > 0


class TestDetectAnomalies:
    def test_returns_list(self, seeded_db):
        """detect_anomalies should return a list (possibly empty)."""
        anomalies = detect_anomalies()
        assert isinstance(anomalies, list)

    def test_anomaly_structure(self, seeded_db):
        """Each anomaly should have required fields."""
        anomalies = detect_anomalies()
        for a in anomalies:
            assert "pm_id" in a
            assert "type" in a
            assert "severity" in a
            assert "message" in a
