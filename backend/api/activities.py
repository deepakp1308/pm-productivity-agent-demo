"""Activities API routes."""

from fastapi import APIRouter, Query, HTTPException
from backend.storage import db

router = APIRouter(prefix="/api", tags=["activities"])


@router.get("/activities")
def list_activities(
    pm_id: str = None,
    source: str = None,
    priority_name: str = None,
    date_from: str = None,
    date_to: str = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
):
    return db.get_activities(
        pm_id=pm_id, source=source, priority_name=priority_name,
        date_from=date_from, date_to=date_to, limit=limit, offset=offset,
    )


@router.get("/activities/{activity_id}")
def get_activity(activity_id: int):
    act = db.get_activity(activity_id)
    if not act:
        raise HTTPException(404, "Activity not found")
    return act


@router.get("/activities/search/{query}")
def search_activities(query: str, limit: int = Query(default=50, le=200)):
    return db.search_activities_fts(query, limit=limit)
