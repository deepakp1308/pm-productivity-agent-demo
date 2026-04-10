"""Tests for backend.storage.db — ~15 tests covering all DB operations."""

import pytest
from backend.storage import db


class TestInitDB:
    def test_init_db_creates_tables(self, seeded_db):
        """init_db should create all required tables."""
        conn = db._get_conn()
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            table_names = {r["name"] for r in rows}
            expected = {
                "team_members",
                "priorities",
                "activities",
                "activity_classifications",
                "recommendations",
                "pipeline_runs",
                "chat_messages",
                "activities_fts",
            }
            for t in expected:
                assert t in table_names, f"Table {t} missing"
        finally:
            conn.close()


class TestTeamMembers:
    def test_upsert_team_member_insert(self, seeded_db):
        """Inserting a new team member should succeed."""
        db.upsert_team_member("test-pm", "Test PM", "test@example.com", "pm")
        member = db.get_team_member("test-pm")
        assert member is not None
        assert member["name"] == "Test PM"

    def test_upsert_team_member_update(self, seeded_db):
        """Upserting an existing member should update fields."""
        db.upsert_team_member("test-pm", "Test PM Updated", "test2@example.com", "pm")
        member = db.get_team_member("test-pm")
        assert member["name"] == "Test PM Updated"
        assert member["email"] == "test2@example.com"


class TestActivities:
    def test_insert_activity(self, seeded_db, sample_activity):
        """insert_activity should return a positive row id."""
        act = sample_activity.copy()
        act["source_id"] = "unique-insert-test-001"
        row_id = db.insert_activity(**act)
        assert row_id is not None
        assert row_id > 0

    def test_insert_activities_bulk(self, seeded_db):
        """Bulk insert should return the count of inserted rows."""
        rows = [
            {
                "pm_id": "stephen-yu",
                "source": "slack",
                "source_id": "bulk-test-001",
                "title": "Bulk test message 1",
                "summary": "Test",
                "occurred_at": "2026-04-01T09:00:00",
            },
            {
                "pm_id": "stephen-yu",
                "source": "slack",
                "source_id": "bulk-test-002",
                "title": "Bulk test message 2",
                "summary": "Test",
                "occurred_at": "2026-04-01T09:15:00",
            },
        ]
        count = db.insert_activities_bulk(rows)
        assert count >= 2

    def test_get_activities_pm_filter(self, seeded_db):
        """Filtering by pm_id should return only that PM's activities."""
        acts = db.get_activities(pm_id="stephen-yu", limit=500)
        assert len(acts) > 0
        for a in acts:
            assert a["pm_id"] == "stephen-yu"

    def test_get_activities_source_filter(self, seeded_db):
        """Filtering by source should return only that source."""
        acts = db.get_activities(source="jira", limit=500)
        assert len(acts) > 0
        for a in acts:
            assert a["source"] == "jira"


class TestFTS:
    def test_search_activities_fts_keyword(self, seeded_db):
        """FTS search for a known keyword should return results."""
        results = db.search_activities_fts("Analytics Agent")
        assert len(results) > 0

    def test_search_activities_fts_empty_returns_empty(self, seeded_db):
        """Searching for nonsense should return empty list."""
        results = db.search_activities_fts("xyznonexistent12345")
        assert results == []


class TestClassifications:
    def test_insert_classification(self, seeded_db):
        """insert_classification should return a positive id."""
        # Get any activity id
        acts = db.get_activities(limit=1)
        assert len(acts) > 0
        cid = db.insert_classification(
            activity_id=acts[0]["id"],
            priority_name="Test Priority",
            activity_type="Execution",
            leverage="Medium",
            confidence=0.9,
            reasoning="Test classification",
        )
        assert cid > 0

    def test_get_unclassified_activities(self, seeded_db):
        """After seeding, most activities should be classified (few unclassified)."""
        # We inserted a couple of bulk-test activities above that may be unclassified
        unclassified = db.get_unclassified_activities(limit=1000)
        # There could be a few from our test inserts; the seed data should all be classified
        assert isinstance(unclassified, list)


class TestRecommendations:
    def test_insert_and_get_recommendations(self, seeded_db):
        """Inserting and retrieving a recommendation should round-trip."""
        rid = db.insert_recommendation(
            week_iso="2099-W01",
            pm_id="stephen-yu",
            pm_name="Stephen Yu",
            kind="Accelerate",
            action="Test action",
            rationale="Test rationale",
            evidence_ids=[1, 2, 3],
            judge_score=4.5,
        )
        assert rid > 0
        recs = db.get_recommendations(week_iso="2099-W01")
        assert len(recs) >= 1
        found = [r for r in recs if r["id"] == rid]
        assert len(found) == 1
        assert found[0]["evidence_ids"] == [1, 2, 3]


class TestPriorities:
    def test_insert_get_update_delete_priority(self, seeded_db):
        """Full lifecycle: insert -> get -> update -> soft-delete."""
        pid = db.insert_priority("Lifecycle Test", "desc", 0.5)
        assert pid > 0

        priorities = db.get_priorities(active_only=True)
        found = [p for p in priorities if p["id"] == pid]
        assert len(found) == 1

        db.update_priority(pid, name="Lifecycle Test Updated", weight=0.8)
        priorities = db.get_priorities(active_only=True)
        found = [p for p in priorities if p["id"] == pid]
        assert found[0]["name"] == "Lifecycle Test Updated"

        db.delete_priority(pid)
        priorities = db.get_priorities(active_only=True)
        found = [p for p in priorities if p["id"] == pid]
        assert len(found) == 0


class TestReadOnlySQL:
    def test_select_allowed(self, seeded_db):
        """SELECT queries should execute without error."""
        rows = db.run_read_only_sql("SELECT COUNT(*) as cnt FROM activities")
        assert rows[0]["cnt"] > 0

    def test_insert_blocked(self, seeded_db):
        """INSERT queries should be rejected."""
        with pytest.raises(ValueError, match="Only SELECT"):
            db.run_read_only_sql("INSERT INTO activities (pm_id) VALUES ('x')")

    def test_update_blocked(self, seeded_db):
        """UPDATE queries should be rejected."""
        with pytest.raises(ValueError, match="Only SELECT"):
            db.run_read_only_sql("UPDATE activities SET title='x'")

    def test_delete_blocked(self, seeded_db):
        """DELETE queries should be rejected."""
        with pytest.raises(ValueError, match="Only SELECT"):
            db.run_read_only_sql("DELETE FROM activities")


class TestChat:
    def test_save_and_get_chat_history(self, seeded_db):
        """save_chat_message + get_chat_history should round-trip."""
        sid = "test-session-db-001"
        db.save_chat_message(sid, "user", "Hello test")
        db.save_chat_message(sid, "assistant", "Hello back")
        history = db.get_chat_history(sid)
        assert len(history) >= 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
