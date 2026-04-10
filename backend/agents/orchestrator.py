"""Pipeline orchestrator: classify → analyze → recommend → judge → publish."""

import logging
from datetime import datetime, timedelta, date

from backend.storage import db
from backend.agents.classifier import classify_batch
from backend.agents.recommender import generate_recommendations
from backend.agents.judge import judge_recommendation, compute_judge_score
from backend import config

logger = logging.getLogger(__name__)


def run_pipeline(week_iso: str = None, triggered_by: str = "manual",
                 use_llm: bool = True) -> dict:
    """Run the full analysis pipeline.

    Args:
        week_iso: Target week in ISO format (e.g., "2026-W15"). Defaults to current week.
        triggered_by: "manual", "scheduler", or "api"
        use_llm: If False, skip LLM calls (use rule-based only)
    """
    if not week_iso:
        week_iso = date.today().strftime("%G-W%V")

    run_id = db.start_pipeline_run(week_iso, triggered_by)
    logger.info(f"Pipeline started: run_id={run_id}, week={week_iso}, llm={use_llm}")

    try:
        # ── Step 1: Classify unclassified activities ──────────────────────
        unclassified = db.get_unclassified_activities(limit=1000)
        logger.info(f"Found {len(unclassified)} unclassified activities")

        if unclassified:
            classifications = classify_batch(unclassified, use_llm=use_llm)
            count = db.insert_classifications_bulk(classifications)
            logger.info(f"Classified {count} activities")
            db.update_pipeline_run(run_id, activities_classified=count)

        # ── Step 2: Generate recommendations per PM ───────────────────────
        # Compute date range for the target week
        # Parse week_iso to get start/end dates
        year, week_num = week_iso.split("-W")
        week_start = datetime.strptime(f"{year}-W{week_num}-1", "%G-W%V-%u")
        week_end = week_start + timedelta(days=6, hours=23, minutes=59)
        date_from = week_start.strftime("%Y-%m-%dT00:00:00")
        date_to = week_end.strftime("%Y-%m-%dT23:59:59")

        recs_generated = 0
        members = [m for m in config.TEAM_MEMBERS]

        for member in members:
            pm_id = member["id"]
            pm_name = member["name"]
            logger.info(f"Generating recommendations for {pm_name}...")

            if use_llm:
                try:
                    briefing = generate_recommendations(pm_id, week_iso, date_from, date_to)

                    for rec in briefing.recommendations:
                        # Judge each recommendation
                        evidence = []
                        for eid in rec.evidence_ids:
                            act = db.get_activity(eid)
                            if act:
                                evidence.append({
                                    "id": act["id"],
                                    "title": act["title"],
                                    "summary": (act.get("summary") or "")[:150],
                                })

                        judge_result = judge_recommendation(
                            {"kind": rec.kind.value, "action": rec.action,
                             "rationale": rec.rationale, "evidence_ids": [e["id"] for e in evidence]},
                            evidence,
                        )

                        score = compute_judge_score(judge_result)
                        status = "blocked" if judge_result.block else "published"

                        db.insert_recommendation(
                            week_iso=week_iso,
                            pm_id=pm_id,
                            pm_name=pm_name,
                            kind=rec.kind.value,
                            action=rec.action,
                            rationale=rec.rationale,
                            evidence_ids=[e["id"] for e in evidence] if evidence else rec.evidence_ids,
                            judge_score=score,
                            judge_reasoning=judge_result.reasoning,
                            status=status,
                        )
                        recs_generated += 1
                except Exception as e:
                    logger.error(f"Failed to generate recs for {pm_name}: {e}")
            else:
                logger.info(f"Skipping LLM recommendations for {pm_name} (use_llm=False)")

        db.update_pipeline_run(run_id,
                               status="completed",
                               recommendations_generated=recs_generated,
                               completed_at=datetime.now().isoformat())
        logger.info(f"Pipeline completed: {recs_generated} recommendations generated")

        return {
            "run_id": run_id,
            "week_iso": week_iso,
            "status": "completed",
            "activities_classified": len(unclassified),
            "recommendations_generated": recs_generated,
        }

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        db.update_pipeline_run(run_id, status="failed", error_message=str(e),
                               completed_at=datetime.now().isoformat())
        return {
            "run_id": run_id,
            "week_iso": week_iso,
            "status": "failed",
            "error": str(e),
        }
