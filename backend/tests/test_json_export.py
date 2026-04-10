"""Tests validating static JSON files in frontend/public/api/ — ~10 tests."""

import json
import os

import pytest

JSON_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend", "public", "api",
)


def _load_json(filename):
    """Load and return parsed JSON from the static API directory."""
    path = os.path.join(JSON_DIR, filename)
    with open(path, "r") as f:
        return json.load(f)


class TestDashboardJson:
    def test_exists_and_valid(self):
        """dashboard.json should exist and parse as valid JSON."""
        data = _load_json("dashboard.json")
        assert isinstance(data, dict)

    def test_has_required_fields(self):
        """dashboard.json should have total_activities, pm_summaries, recommendations."""
        data = _load_json("dashboard.json")
        assert "total_activities" in data
        assert "pm_summaries" in data
        assert "recommendations" in data


class TestPmSummaryJsons:
    @pytest.mark.parametrize("pm_id", ["stephen-yu", "nicole-jayne", "vivian-wang"])
    def test_pm_summary_json_exists(self, pm_id):
        """Each PM summary JSON should exist."""
        data = _load_json(f"pm-{pm_id}-summary.json")
        assert isinstance(data, dict)


class TestActivityJsons:
    @pytest.mark.parametrize("pm_id", ["stephen-yu", "nicole-jayne", "vivian-wang"])
    def test_activity_json_has_items(self, pm_id):
        """Each activity JSON should exist and have > 0 items."""
        data = _load_json(f"activities-{pm_id}.json")
        assert isinstance(data, list)
        assert len(data) > 0


class TestRecommendationsJson:
    def test_has_week_iso_and_array(self):
        """recommendations.json should have week_iso and recommendations array."""
        data = _load_json("recommendations.json")
        assert "week_iso" in data
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)


class TestDecisionsJson:
    def test_has_required_arrays(self):
        """decisions.json should have key_decisions and open_questions arrays."""
        data = _load_json("decisions.json")
        assert "key_decisions" in data
        assert "open_questions" in data
        assert isinstance(data["key_decisions"], list)
        assert isinstance(data["open_questions"], list)


class TestTrendsJson:
    def test_all_pms_with_weeks(self):
        """trends.json should have all 3 PMs with 10 weeks each."""
        data = _load_json("trends.json")
        assert isinstance(data, dict)
        for pm_id in ["stephen-yu", "nicole-jayne", "vivian-wang"]:
            assert pm_id in data, f"Missing PM {pm_id} in trends"
            pm_data = data[pm_id]
            assert "weeks" in pm_data, f"{pm_id} missing 'weeks' key"
            assert len(pm_data["weeks"]) == 10, (
                f"{pm_id} has {len(pm_data['weeks'])} weeks, expected 10"
            )

    def test_trend_alignment_range(self):
        """All trend alignment values should be between 0-100."""
        data = _load_json("trends.json")
        for pm_id, pm_data in data.items():
            for val in pm_data["alignment_pct"]:
                assert 0 <= val <= 100, (
                    f"{pm_id} alignment value {val} out of range"
                )


class TestAllJsonFilesValid:
    def test_every_json_parses(self):
        """Every .json file in the directory should parse without error."""
        for fname in os.listdir(JSON_DIR):
            if fname.endswith(".json"):
                path = os.path.join(JSON_DIR, fname)
                with open(path, "r") as f:
                    data = json.load(f)  # should not raise
                assert data is not None, f"{fname} parsed to None"

    def test_no_empty_json_files(self):
        """No JSON file should be empty (> 10 bytes)."""
        for fname in os.listdir(JSON_DIR):
            if fname.endswith(".json"):
                path = os.path.join(JSON_DIR, fname)
                size = os.path.getsize(path)
                assert size > 10, f"{fname} is only {size} bytes"
