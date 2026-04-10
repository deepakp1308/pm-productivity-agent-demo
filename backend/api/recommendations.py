"""Recommendations API routes."""

from fastapi import APIRouter, Query
from backend.storage import db

router = APIRouter(prefix="/api", tags=["recommendations"])


@router.get("/recommendations")
def list_recommendations(
    week_iso: str = None,
    pm_id: str = None,
    status: str = None,
    limit: int = Query(default=50, le=200),
):
    return db.get_recommendations(week_iso=week_iso, pm_id=pm_id, status=status, limit=limit)


@router.get("/recommendations/latest")
def latest_recommendations(pm_id: str = None):
    week = db.get_latest_week_iso()
    if not week:
        return {"week_iso": None, "recommendations": []}
    recs = db.get_recommendations(week_iso=week, pm_id=pm_id)
    return {"week_iso": week, "recommendations": recs}
