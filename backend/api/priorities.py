"""Priorities API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.storage import db

router = APIRouter(prefix="/api", tags=["priorities"])


class PriorityCreate(BaseModel):
    name: str
    description: str = ""
    weight: float = 1.0


class PriorityUpdate(BaseModel):
    name: str = None
    description: str = None
    weight: float = None
    active: bool = None


@router.get("/priorities")
def list_priorities(active_only: bool = True):
    return db.get_priorities(active_only=active_only)


@router.post("/priorities")
def create_priority(body: PriorityCreate):
    pid = db.insert_priority(body.name, body.description, body.weight)
    return {"id": pid, "name": body.name}


@router.put("/priorities/{priority_id}")
def update_priority(priority_id: int, body: PriorityUpdate):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(400, "No fields to update")
    db.update_priority(priority_id, **updates)
    return {"id": priority_id, "updated": True}


@router.delete("/priorities/{priority_id}")
def archive_priority(priority_id: int):
    db.delete_priority(priority_id)
    return {"id": priority_id, "archived": True}
