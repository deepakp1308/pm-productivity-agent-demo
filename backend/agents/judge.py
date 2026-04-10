"""Opus-powered judge layer — quality gate on recommendations."""

import json
import logging

from backend.storage.models import JudgeScore, Recommendation
from backend.llm.claude import call_structured

logger = logging.getLogger(__name__)

JUDGE_SYSTEM = """You are a quality reviewer for PM coaching recommendations.
Score this recommendation on the following dimensions.
IMPORTANT: Write your reasoning FIRST, then provide scores.

Scoring:
- faithfulness (1-3): Does the recommendation follow from the evidence?
- priority_fit (1-3): Does it align with stated priorities?
- specificity (1-3): Is it actionable and specific?
- harm_risk (true/false): true = safe, false = could cause harm
- privacy_compliance (true/false): true = compliant, false = privacy concern
- block (true/false): Set true if harm_risk=false OR privacy_compliance=false OR any score is 1

Return JSON:
{{
  "reasoning": "<chain of thought analyzing the recommendation>",
  "faithfulness": <1-3>,
  "priority_fit": <1-3>,
  "specificity": <1-3>,
  "harm_risk": <true/false>,
  "privacy_compliance": <true/false>,
  "block": <true/false>
}}"""


def judge_recommendation(rec: dict, evidence_summaries: list[dict] = None) -> JudgeScore:
    """Score a single recommendation. Returns JudgeScore."""
    evidence_json = json.dumps(evidence_summaries or [])

    rec_json = json.dumps({
        "kind": rec.get("kind"),
        "action": rec.get("action"),
        "rationale": rec.get("rationale"),
        "evidence_ids": rec.get("evidence_ids", []),
    })

    user_message = f"""Recommendation:
{rec_json}

Supporting evidence:
{evidence_json}

Score this recommendation."""

    result = call_structured(
        stage="judge",
        system=JUDGE_SYSTEM,
        user_message=user_message,
        output_model=JudgeScore,
        max_tokens=1024,
    )

    logger.info(f"Judge result: block={result.block}, scores=({result.faithfulness},{result.priority_fit},{result.specificity})")
    return result


def compute_judge_score(judge: JudgeScore) -> float:
    """Compute a composite score from judge dimensions (0-5 scale)."""
    if judge.block:
        return 0.0
    # Average of 1-3 scores, scaled to 0-5
    avg = (judge.faithfulness + judge.priority_fit + judge.specificity) / 3.0
    return round(avg * 5 / 3, 1)
