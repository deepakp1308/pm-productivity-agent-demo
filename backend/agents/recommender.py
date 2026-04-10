"""Opus-powered recommendation generator — produces weekly coaching for each PM."""

import json
import logging

from backend.storage import db
from backend.storage.models import BriefingOutput
from backend.analysis.engine import compute_pm_summary
from backend.llm.claude import call_structured

logger = logging.getLogger(__name__)

RECOMMENDER_SYSTEM = """You are a coaching assistant for a PM lead. You see one PM's last week.
Aggregates: {aggregates_json}
Evidence rows (id + summary): {evidence_json}
Priorities: {priorities_json}

Produce exactly 3 recommendations: one Accelerate, one Cut, one Redirect.
Each must cite evidence_ids from the list above. No claim without evidence.
Tone: coaching, not judging. Respect invisible work.

Return JSON matching this exact schema:
{{
  "summary": "<2-3 sentences on where time went>",
  "alignment_pct": <float 0-100>,
  "recommendations": [
    {{"kind": "Accelerate", "action": "...", "rationale": "...", "evidence_ids": [int, ...]}},
    {{"kind": "Cut", "action": "...", "rationale": "...", "evidence_ids": [int, ...]}},
    {{"kind": "Redirect", "action": "...", "rationale": "...", "evidence_ids": [int, ...]}}
  ],
  "uncertainty_flags": ["..."]
}}"""


def generate_recommendations(pm_id: str, week_iso: str,
                              date_from: str = None, date_to: str = None) -> BriefingOutput:
    """Generate coaching recommendations for one PM for one week."""
    # Gather data
    summary = compute_pm_summary(pm_id, date_from, date_to)
    activities = db.get_activities(pm_id=pm_id, date_from=date_from, date_to=date_to, limit=200)
    priorities = db.get_priorities()

    # Build evidence rows (id + title + source + classification)
    evidence = []
    for a in activities[:100]:  # cap to manage token count
        evidence.append({
            "id": a["id"],
            "source": a["source"],
            "title": a["title"],
            "summary": (a.get("summary") or "")[:150],
            "type": a.get("activity_type"),
            "priority": a.get("priority_name"),
            "leverage": a.get("leverage"),
        })

    aggregates_json = json.dumps({
        "pm_name": summary["pm_name"],
        "total_activities": summary["total_activities"],
        "meeting_hours": summary["meeting_hours"],
        "alignment_pct": summary["alignment_pct"],
        "source_breakdown": summary["source_breakdown"],
        "type_breakdown": summary["type_breakdown"],
        "priority_breakdown": summary["priority_breakdown"],
        "fragmentation_score": summary["fragmentation_score"],
    })

    evidence_json = json.dumps(evidence)
    priorities_json = json.dumps([{"name": p["name"], "description": p.get("description", ""),
                                    "weight": p.get("weight", 1.0)} for p in priorities])

    system = RECOMMENDER_SYSTEM.format(
        aggregates_json=aggregates_json,
        evidence_json=evidence_json,
        priorities_json=priorities_json,
    )

    result = call_structured(
        stage="recommend",
        system=system,
        user_message=f"Generate coaching recommendations for {summary['pm_name']} for week {week_iso}.",
        output_model=BriefingOutput,
        max_tokens=2048,
    )

    logger.info(f"Generated {len(result.recommendations)} recommendations for {pm_id}")
    return result
