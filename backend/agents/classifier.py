"""Tiered activity classifier: rule-based fast path + Claude Sonnet for ambiguous."""

import re
import json
import logging
from typing import Optional

from backend.config import RULE_BASED_PATTERNS, DEFAULT_PRIORITIES
from backend.storage import db
from backend.storage.models import ClassifierOutput
from backend.llm.claude import call_structured

logger = logging.getLogger(__name__)

CLASSIFIER_SYSTEM = """You are classifying a single work activity for a product manager.
Current team priorities: {priorities_json}

Return JSON ONLY matching this exact schema:
{{
  "type": "Strategy|Discovery|Execution|Stakeholder|InternalOps|Reactive|LowValue",
  "priority": "<exact priority name or 'Other'>",
  "leverage": "High|Medium|Low",
  "confidence": 0.0-1.0,
  "reasoning": "<1 sentence>"
}}"""


def classify_activity(activity: dict, priorities: list[dict] = None) -> dict:
    """Classify a single activity. Returns classification dict.

    Uses rule-based fast path first, falls back to LLM for ambiguous cases.
    """
    if priorities is None:
        priorities = db.get_priorities()

    title = activity.get("title", "")
    summary = activity.get("summary", "")
    source = activity.get("source", "")
    text = f"{title} {summary}"

    # ── Rule-based fast path ───────────────────────────────────────────────
    rule_type = None
    rule_priority = None

    for pattern, act_type, pri_hint in RULE_BASED_PATTERNS:
        if re.search(pattern, text):
            if act_type and not rule_type:
                rule_type = act_type
            if pri_hint and not rule_priority:
                rule_priority = pri_hint

    # If both type and priority resolved, skip LLM
    if rule_type and rule_priority:
        return {
            "activity_id": activity["id"],
            "priority_name": rule_priority,
            "priority_id": _find_priority_id(rule_priority, priorities),
            "activity_type": rule_type,
            "leverage": _guess_leverage(text),
            "confidence": 0.85,
            "reasoning": f"Rule-based: matched patterns for {rule_type}/{rule_priority}",
        }

    # ── LLM classification (Sonnet) ────────────────────────────────────────
    try:
        priorities_json = json.dumps([{"name": p["name"], "description": p.get("description", "")}
                                       for p in priorities])
        system = CLASSIFIER_SYSTEM.format(priorities_json=priorities_json)

        activity_json = json.dumps({
            "source": source,
            "title": title,
            "summary": summary[:500],
            "duration_minutes": activity.get("duration_minutes"),
        })

        result = call_structured(
            stage="classify",
            system=system,
            user_message=f"Activity: {activity_json}",
            output_model=ClassifierOutput,
            max_tokens=512,
        )

        return {
            "activity_id": activity["id"],
            "priority_name": result.priority,
            "priority_id": _find_priority_id(result.priority, priorities),
            "activity_type": result.type.value,
            "leverage": result.leverage.value,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
        }
    except Exception as e:
        logger.warning(f"LLM classification failed for activity {activity['id']}: {e}")
        # Fallback to rule-based partial result
        return {
            "activity_id": activity["id"],
            "priority_name": rule_priority or "Other",
            "priority_id": _find_priority_id(rule_priority or "Other", priorities),
            "activity_type": rule_type or "Execution",
            "leverage": _guess_leverage(text),
            "confidence": 0.5,
            "reasoning": f"Fallback: partial rule match. LLM error: {str(e)[:100]}",
        }


def classify_batch(activities: list[dict], use_llm: bool = True) -> list[dict]:
    """Classify a batch of activities. Returns list of classification dicts."""
    priorities = db.get_priorities()
    results = []

    for act in activities:
        if use_llm:
            result = classify_activity(act, priorities)
        else:
            # Rule-only mode (for seed data or dry-run)
            title = act.get("title", "")
            summary = act.get("summary", "")
            text = f"{title} {summary}"
            rule_type = None
            rule_priority = None
            for pattern, act_type, pri_hint in RULE_BASED_PATTERNS:
                if re.search(pattern, text):
                    if act_type and not rule_type:
                        rule_type = act_type
                    if pri_hint and not rule_priority:
                        rule_priority = pri_hint
            result = {
                "activity_id": act["id"],
                "priority_name": rule_priority or "Other",
                "priority_id": _find_priority_id(rule_priority or "Other", priorities),
                "activity_type": rule_type or "Execution",
                "leverage": _guess_leverage(text),
                "confidence": 0.7,
                "reasoning": "Rule-based classification (LLM disabled)",
            }
        results.append(result)

    return results


def _find_priority_id(name: str, priorities: list[dict]) -> Optional[int]:
    for p in priorities:
        if p["name"] == name:
            return p["id"]
    return None


def _guess_leverage(text: str) -> str:
    text_lower = text.lower()
    if any(w in text_lower for w in ["shipped", "completed", "done", "approved", "merged", "decision", "unblocked"]):
        return "High"
    if any(w in text_lower for w in ["blocked", "waiting", "pending", "tbd", "tentative"]):
        return "Low"
    return "Medium"
