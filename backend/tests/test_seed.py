"""Tests for backend.seed.seed_data — ~7 tests (uses seeded_db fixture)."""

import pytest
from backend.storage import db


class TestSeedAll:
    def test_seed_returns_correct_keys(self, seeded_db):
        """seed_all result should have expected keys."""
        expected_keys = {"team_members", "priorities", "activities", "classifications", "week_iso"}
        assert expected_keys.issubset(set(seeded_db.keys()))

    def test_total_activities_above_400(self, seeded_db):
        """Total seeded activities should be > 400 (~476 expected)."""
        count = db.get_activity_count()
        assert count > 400, f"Only {count} activities seeded"

    def test_each_pm_has_over_100_activities(self, seeded_db):
        """Each PM should have > 100 activities."""
        for pm_id in ["stephen-yu", "nicole-jayne", "vivian-wang"]:
            count = db.get_activity_count(pm_id=pm_id)
            assert count > 100, f"{pm_id} has only {count} activities"

    def test_each_pm_has_all_4_sources(self, seeded_db):
        """Each PM should have activities from calendar, slack, email, jira."""
        for pm_id in ["stephen-yu", "nicole-jayne", "vivian-wang"]:
            acts = db.get_activities(pm_id=pm_id, limit=5000)
            sources = {a["source"] for a in acts}
            for src in ["calendar", "slack", "email", "jira"]:
                assert src in sources, f"{pm_id} missing source: {src}"

    def test_nine_recommendations_exist(self, seeded_db):
        """9 recommendations should be seeded (3 per PM)."""
        week = seeded_db["week_iso"]
        assert week is not None
        recs = db.get_recommendations(week_iso=week)
        assert len(recs) == 9

    def test_recommendation_kinds(self, seeded_db):
        """Each recommendation should have kind in (Accelerate, Cut, Redirect)."""
        week = seeded_db["week_iso"]
        recs = db.get_recommendations(week_iso=week)
        valid_kinds = {"Accelerate", "Cut", "Redirect"}
        for r in recs:
            assert r["kind"] in valid_kinds, f"Invalid kind: {r['kind']}"

    def test_activities_within_date_range(self, seeded_db):
        """Activities should be within the last 4 weeks + today."""
        from datetime import datetime, timedelta
        acts = db.get_activities(limit=5000)
        now = datetime.now()
        four_weeks_ago = now - timedelta(weeks=5)  # small buffer
        for a in acts:
            try:
                dt = datetime.fromisoformat(a["occurred_at"])
                assert dt >= four_weeks_ago, (
                    f"Activity dated {a['occurred_at']} is older than 5 weeks"
                )
                assert dt <= now + timedelta(days=1), (
                    f"Activity dated {a['occurred_at']} is in the future"
                )
            except (ValueError, TypeError):
                pass  # skip unparseable dates
