"""PM self-view API routes."""

from fastapi import APIRouter, HTTPException
from backend.storage import db
from backend.analysis.engine import compute_pm_summary, compute_pm_trends, detect_anomalies

router = APIRouter(prefix="/api", tags=["pm"])


@router.get("/team")
def list_team():
    return db.get_team_members()


@router.get("/pm/{pm_id}/summary")
def pm_summary(pm_id: str, date_from: str = None, date_to: str = None):
    pm = db.get_team_member(pm_id)
    if not pm:
        raise HTTPException(404, "PM not found")
    return compute_pm_summary(pm_id, date_from=date_from, date_to=date_to)


@router.get("/pm/{pm_id}/activities")
def pm_activities(pm_id: str, source: str = None, date_from: str = None, date_to: str = None,
                  limit: int = 100, offset: int = 0):
    pm = db.get_team_member(pm_id)
    if not pm:
        raise HTTPException(404, "PM not found")
    return db.get_activities(pm_id=pm_id, source=source, date_from=date_from,
                             date_to=date_to, limit=limit, offset=offset)


@router.get("/pm/{pm_id}/trends")
def pm_trends(pm_id: str, weeks: int = 4):
    pm = db.get_team_member(pm_id)
    if not pm:
        raise HTTPException(404, "PM not found")
    return compute_pm_trends(pm_id, weeks=weeks)


@router.get("/pm/{pm_id}/anomalies")
def pm_anomalies(pm_id: str):
    return detect_anomalies(pm_id=pm_id)
