"""Shared fixtures for the PM Productivity Agent test suite."""

import os
import sys
import tempfile

import pytest

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Point DB at a temporary file so tests never touch the real database
_test_db_fd, _test_db_path = tempfile.mkstemp(suffix=".db", prefix="pm_agent_test_")
os.close(_test_db_fd)
os.environ["DB_PATH"] = _test_db_path

# Force the db module to pick up the test path
from backend.storage import db as _db_mod
_db_mod._db_path = _test_db_path


# ---------------------------------------------------------------------------
# Session-scoped seed fixture — runs seed_all() exactly once
# ---------------------------------------------------------------------------

_seed_result = None  # type: dict


@pytest.fixture(scope="session")
def seeded_db():
    """Seed the test database once per session. Returns the seed result dict."""
    global _seed_result
    if _seed_result is None:
        from backend.seed.seed_data import seed_all
        _seed_result = seed_all()
    return _seed_result


# ---------------------------------------------------------------------------
# FastAPI TestClient (depends on seeded_db so DB has data)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_client(seeded_db):
    """Provide a FastAPI TestClient backed by the seeded test DB."""
    from starlette.testclient import TestClient
    from backend.main import app
    with TestClient(app) as client:
        yield client


# ---------------------------------------------------------------------------
# Sample activity dict for unit-level tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_activity():
    """Return a dict matching the activity schema (not yet inserted)."""
    return {
        "pm_id": "stephen-yu",
        "source": "calendar",
        "source_id": "test-activity-001",
        "title": "Test Meeting: Analytics Agent Review",
        "summary": "Reviewed analytics agent beta v2 rollout metrics.",
        "duration_minutes": 30,
        "participants": ["deepak_kumar2@intuit.com"],
        "occurred_at": "2026-04-01T10:00:00",
    }
