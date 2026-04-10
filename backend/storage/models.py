"""Pydantic v2 models — used for API schemas, LLM structured output, and DB serialization."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────────

class Source(str, Enum):
    calendar = "calendar"
    slack = "slack"
    email = "email"
    jira = "jira"
    gdrive = "gdrive"
    transcript = "transcript"


class ActivityType(str, Enum):
    strategy = "Strategy"
    discovery = "Discovery"
    execution = "Execution"
    stakeholder = "Stakeholder"
    internal_ops = "InternalOps"
    reactive = "Reactive"
    low_value = "LowValue"


class Leverage(str, Enum):
    high = "High"
    medium = "Medium"
    low = "Low"


class RecKind(str, Enum):
    accelerate = "Accelerate"
    cut = "Cut"
    redirect = "Redirect"


class RecStatus(str, Enum):
    draft = "draft"
    published = "published"
    blocked = "blocked"


# ── Core domain models ─────────────────────────────────────────────────────────

class TeamMember(BaseModel):
    id: str
    name: str
    email: str
    role: str = "pm"


class Priority(BaseModel):
    id: int
    name: str
    description: str = ""
    weight: float = 1.0
    active: bool = True
    updated_at: Optional[str] = None


class Activity(BaseModel):
    id: int
    pm_id: str
    source: Source
    source_id: Optional[str] = None
    title: str
    summary: str = ""
    duration_minutes: Optional[int] = None
    participants: list[str] = Field(default_factory=list)
    url: str = ""
    occurred_at: str
    ingested_at: Optional[str] = None
    # classification (filled after classifier runs)
    activity_type: Optional[ActivityType] = None
    priority_name: Optional[str] = None
    leverage: Optional[Leverage] = None
    confidence: Optional[float] = None


class ActivityClassification(BaseModel):
    id: int
    activity_id: int
    priority_id: Optional[int] = None
    priority_name: Optional[str] = None
    activity_type: Optional[ActivityType] = None
    leverage: Optional[Leverage] = None
    confidence: Optional[float] = None
    reasoning: str = ""
    classified_at: Optional[str] = None


# ── LLM output contracts ──────────────────────────────────────────────────────

class ClassifierOutput(BaseModel):
    """Structured output from the Sonnet classifier (matches spec §4.4)."""
    type: ActivityType
    priority: str = Field(description="Exact priority name or 'Other'")
    leverage: Leverage
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(description="One sentence explanation")


class Recommendation(BaseModel):
    kind: RecKind
    action: str
    rationale: str
    evidence_ids: list[int] = Field(min_length=1, description="Activity IDs supporting this rec")


class BriefingOutput(BaseModel):
    """Structured output from the Opus recommender (matches spec §4.4)."""
    summary: str = Field(description="2-3 sentences on where time went")
    alignment_pct: float = Field(ge=0.0, le=100.0, description="% time on stated priorities")
    recommendations: list[Recommendation] = Field(min_length=3, max_length=3)
    uncertainty_flags: list[str] = Field(default_factory=list)


class JudgeScore(BaseModel):
    """Structured output from the Opus judge (matches spec §4.4)."""
    reasoning: str = Field(description="Chain-of-thought reasoning BEFORE scores")
    faithfulness: int = Field(ge=1, le=3)
    priority_fit: int = Field(ge=1, le=3)
    specificity: int = Field(ge=1, le=3)
    harm_risk: bool = Field(description="True = safe, False = blocked")
    privacy_compliance: bool = Field(description="True = compliant, False = blocked")
    block: bool = Field(description="True if recommendation should be blocked")


# ── API response models ────────────────────────────────────────────────────────

class RecommendationRecord(BaseModel):
    id: int
    week_iso: str
    pm_id: Optional[str] = None
    pm_name: Optional[str] = None
    kind: RecKind
    action: str
    rationale: str
    evidence_ids: list[int] = Field(default_factory=list)
    judge_score: Optional[float] = None
    judge_reasoning: Optional[str] = None
    status: RecStatus = RecStatus.published
    created_at: Optional[str] = None


class PMSummary(BaseModel):
    pm_id: str
    pm_name: str
    total_activities: int = 0
    meetings: int = 0
    messages: int = 0
    emails: int = 0
    tickets: int = 0
    alignment_pct: float = 0.0
    top_priority: str = ""
    meeting_hours: float = 0.0
    fragmentation_score: float = 0.0
    source_breakdown: dict[str, int] = Field(default_factory=dict)
    type_breakdown: dict[str, int] = Field(default_factory=dict)
    priority_breakdown: dict[str, float] = Field(default_factory=dict)


class DashboardData(BaseModel):
    total_activities: int = 0
    avg_alignment_pct: float = 0.0
    total_recommendations: int = 0
    team_balance_score: float = 0.0
    pm_summaries: list[PMSummary] = Field(default_factory=list)
    priority_coverage: dict[str, dict[str, float]] = Field(default_factory=dict)
    top_insight: str = ""
    recommendations: list[RecommendationRecord] = Field(default_factory=list)


class PipelineRun(BaseModel):
    id: int
    week_iso: str
    triggered_by: str
    status: str = "running"
    activities_ingested: int = 0
    activities_classified: int = 0
    recommendations_generated: int = 0
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    pm_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    context: Optional[dict] = None
