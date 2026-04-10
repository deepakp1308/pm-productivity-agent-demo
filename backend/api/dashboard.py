"""Dashboard API route."""

from fastapi import APIRouter, Query
from backend.analysis.engine import compute_dashboard

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard(date_from: str = None, date_to: str = None):
    return compute_dashboard(date_from=date_from, date_to=date_to)
