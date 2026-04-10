"""Tests for API endpoints using FastAPI TestClient — ~16 tests."""

import pytest


class TestHealth:
    def test_health_endpoint(self, test_client):
        """GET /api/health should return 200."""
        resp = test_client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestDashboard:
    def test_dashboard_200(self, test_client):
        """GET /api/dashboard should return 200."""
        resp = test_client.get("/api/dashboard")
        assert resp.status_code == 200

    def test_dashboard_has_activities(self, test_client):
        """Dashboard response should have total_activities > 0."""
        data = test_client.get("/api/dashboard").json()
        assert data["total_activities"] > 0


class TestActivities:
    def test_list_activities_200(self, test_client):
        """GET /api/activities should return 200 with a list."""
        resp = test_client.get("/api/activities")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_activities_pm_filter(self, test_client):
        """GET /api/activities?pm_id=stephen-yu should return only Stephen's."""
        resp = test_client.get("/api/activities", params={"pm_id": "stephen-yu"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        for a in data:
            assert a["pm_id"] == "stephen-yu"

    def test_activities_source_filter(self, test_client):
        """GET /api/activities?source=slack should return only slack source."""
        resp = test_client.get("/api/activities", params={"source": "slack"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        for a in data:
            assert a["source"] == "slack"


class TestTeam:
    def test_team_endpoint(self, test_client):
        """GET /api/team should return 200 with 4 members."""
        resp = test_client.get("/api/team")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 4  # 3 PMs + 1 lead


class TestPMViews:
    def test_pm_summary_200(self, test_client):
        """GET /api/pm/stephen-yu/summary should return 200 with alignment_pct."""
        resp = test_client.get("/api/pm/stephen-yu/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "alignment_pct" in data

    def test_pm_activities_200(self, test_client):
        """GET /api/pm/stephen-yu/activities should return 200 with a list."""
        resp = test_client.get("/api/pm/stephen-yu/activities")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) > 0

    def test_nonexistent_pm_summary(self, test_client):
        """GET /api/pm/nonexistent/summary should return 404."""
        resp = test_client.get("/api/pm/nonexistent/summary")
        assert resp.status_code == 404


class TestRecommendations:
    def test_latest_recommendations_200(self, test_client):
        """GET /api/recommendations/latest should return 200 with recommendations array."""
        resp = test_client.get("/api/recommendations/latest")
        assert resp.status_code == 200
        data = resp.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) > 0


class TestPriorities:
    def test_priorities_200(self, test_client):
        """GET /api/priorities should return 200 with a list of >= 3."""
        resp = test_client.get("/api/priorities")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 3


class TestChatEndpoint:
    def test_chat_post_200(self, test_client):
        """POST /api/chat should return 200 with non-empty response."""
        resp = test_client.post(
            "/api/chat",
            json={"message": "Compare meeting hours across all PMs"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["response"]) > 0


class TestPipeline:
    def test_pipeline_run_200(self, test_client):
        """POST /api/pipeline/run should return 200."""
        resp = test_client.post("/api/pipeline/run", params={"use_llm": False})
        assert resp.status_code == 200


class TestSearch:
    def test_search_returns_results_or_empty(self, test_client):
        """GET /api/activities/search/canary should return results or empty list."""
        resp = test_client.get("/api/activities/search/canary")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
