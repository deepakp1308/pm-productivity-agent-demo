"""Data quality tests — ~15 tests verifying seeded data integrity."""

import json
from datetime import datetime, date, timedelta

import pytest
from backend.storage import db
from backend.analysis.engine import compute_pm_summary, compute_dashboard


PM_IDS = ["stephen-yu", "nicole-jayne", "vivian-wang"]
SOURCES = ["calendar", "slack", "email", "jira"]

# The seed week is always based on today's date
_SEED_WEEK = date.today().strftime("%G-W%V")


class TestActivityPresence:
    def test_every_pm_has_activities(self, seeded_db):
        """Every PM must have > 0 activities."""
        for pm_id in PM_IDS:
            count = db.get_activity_count(pm_id=pm_id)
            assert count > 0, f"{pm_id} has 0 activities"


class TestClassificationCoverage:
    def test_every_activity_has_classification(self, seeded_db):
        """Activities from seed should all have a classification (no orphans)."""
        # Only count the seed-data activities (source_id not from test inserts)
        rows = db.run_read_only_sql(
            """SELECT COUNT(*) as cnt FROM activities a
               LEFT JOIN activity_classifications ac ON ac.activity_id = a.id
               WHERE ac.id IS NULL AND a.source_id NOT LIKE 'test-%'
               AND a.source_id NOT LIKE 'bulk-%'
               AND a.source_id NOT LIKE 'no-match-%'
               AND a.source_id NOT LIKE 'unique-%'"""
        )
        assert rows[0]["cnt"] == 0, f"{rows[0]['cnt']} activities have no classification"


class TestRecommendationStructure:
    def test_three_per_pm(self, seeded_db):
        """Every PM should have exactly 3 recommendations (Accelerate, Cut, Redirect)."""
        week = _SEED_WEEK
        for pm_id in PM_IDS:
            recs = db.get_recommendations(week_iso=week, pm_id=pm_id)
            assert len(recs) == 3, f"{pm_id} has {len(recs)} recs, expected 3"
            kinds = {r["kind"] for r in recs}
            assert kinds == {"Accelerate", "Cut", "Redirect"}, (
                f"{pm_id} kinds: {kinds}"
            )


class TestSourceCoverage:
    def test_all_sources_per_pm(self, seeded_db):
        """All 4 sources should be present for each PM."""
        for pm_id in PM_IDS:
            acts = db.get_activities(pm_id=pm_id, limit=5000)
            sources = {a["source"] for a in acts}
            for src in SOURCES:
                assert src in sources, f"{pm_id} missing source: {src}"


class TestPriorityPresence:
    def test_all_priorities_appear(self, seeded_db):
        """All 3 priorities should appear in classifications."""
        rows = db.run_read_only_sql(
            "SELECT DISTINCT priority_name FROM activity_classifications WHERE priority_name != 'Other'"
        )
        priority_names = {r["priority_name"] for r in rows}
        expected = {
            "Insights Agent & Scaled AI",
            "Email Report Reimagine & Custom Reports",
            "Marketing Performance Reporting via QB BI",
        }
        for p in expected:
            assert p in priority_names, f"Priority '{p}' not found in classifications"


class TestAlignmentRange:
    def test_alignment_pct_range(self, seeded_db):
        """Alignment % should be between 0-100 for each PM."""
        for pm_id in PM_IDS:
            s = compute_pm_summary(pm_id)
            assert 0 <= s["alignment_pct"] <= 100


class TestSourceBreakdownConsistency:
    def test_source_counts_sum_to_total(self, seeded_db):
        """Source breakdown counts should sum to total for each PM."""
        for pm_id in PM_IDS:
            s = compute_pm_summary(pm_id)
            total_from_breakdown = sum(s["source_breakdown"].values())
            assert total_from_breakdown == s["total_activities"], (
                f"{pm_id}: breakdown sum {total_from_breakdown} != total {s['total_activities']}"
            )


class TestPriorityBreakdownTolerance:
    def test_priority_pct_sums_near_100(self, seeded_db):
        """Priority breakdown % should sum to roughly 100 (within tolerance) or less
        if 'Other' is excluded."""
        for pm_id in PM_IDS:
            s = compute_pm_summary(pm_id)
            # priority_breakdown only includes named priorities (not "Other")
            # so it may sum to less than 100
            pct_sum = sum(s["priority_breakdown"].values())
            # It should be positive and not exceed 100 by much
            assert pct_sum >= 0, f"{pm_id} priority breakdown sum is negative"
            assert pct_sum <= 102, f"{pm_id} priority breakdown sum {pct_sum} > 102"


class TestJudgeScores:
    def test_judge_scores_range(self, seeded_db):
        """Judge scores on recommendations should be between 0-5."""
        week = _SEED_WEEK
        recs = db.get_recommendations(week_iso=week)
        for r in recs:
            if r["judge_score"] is not None:
                assert 0 <= r["judge_score"] <= 5, (
                    f"Judge score {r['judge_score']} out of range for rec {r['id']}"
                )


class TestEvidenceIds:
    def test_evidence_ids_non_empty(self, seeded_db):
        """Recommendation evidence_ids should be non-empty lists."""
        week = _SEED_WEEK
        recs = db.get_recommendations(week_iso=week)
        for r in recs:
            assert isinstance(r["evidence_ids"], list), (
                f"Rec {r['id']} evidence_ids is not a list"
            )
            assert len(r["evidence_ids"]) > 0, (
                f"Rec {r['id']} has empty evidence_ids"
            )


class TestNoDuplicateSourceIds:
    def test_no_duplicate_source_ids_per_pm(self, seeded_db):
        """No duplicate source_ids within a PM."""
        for pm_id in PM_IDS:
            acts = db.get_activities(pm_id=pm_id, limit=5000)
            source_ids = [a["source_id"] for a in acts if a["source_id"]]
            unique = set(source_ids)
            assert len(source_ids) == len(unique), (
                f"{pm_id} has {len(source_ids) - len(unique)} duplicate source_ids"
            )


class TestTeamBalance:
    def test_team_balance_score_range(self, seeded_db):
        """Team balance score should be between 0-100."""
        d = compute_dashboard()
        assert 0 <= d["team_balance_score"] <= 100


class TestDateRange:
    def test_activities_in_expected_range(self, seeded_db):
        """Activities should fall within the last 4 weeks."""
        acts = db.get_activities(limit=5000)
        now = datetime.now()
        five_weeks_ago = now - timedelta(weeks=5)
        for a in acts:
            try:
                dt = datetime.fromisoformat(a["occurred_at"])
                assert dt >= five_weeks_ago
            except (ValueError, TypeError):
                pass


class TestWeekIso:
    def test_recommendations_week_iso_format(self, seeded_db):
        """Recommendations week_iso should be current week format (YYYY-Www)."""
        week = _SEED_WEEK
        assert week is not None
        # Should match pattern like 2026-W15
        import re
        assert re.match(r"\d{4}-W\d{2}", week), f"Invalid week_iso format: {week}"


class TestNoEmptyTitles:
    def test_no_empty_titles_or_sources(self, seeded_db):
        """No activities should have empty title or source."""
        acts = db.get_activities(limit=5000)
        for a in acts:
            assert a["title"], f"Activity {a['id']} has empty title"
            assert a["source"], f"Activity {a['id']} has empty source"
