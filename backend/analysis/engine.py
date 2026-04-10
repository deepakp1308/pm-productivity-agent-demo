"""Pure Python analysis engine — no LLM calls.

Computes time allocation, fragmentation, anomaly detection, priority alignment.
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta

from backend.storage import db
from backend import config


def compute_pm_summary(pm_id: str, date_from: str = None, date_to: str = None) -> dict:
    """Compute a full summary for one PM over a time range."""
    activities = db.get_activities(pm_id=pm_id, date_from=date_from, date_to=date_to, limit=5000)

    source_counts = defaultdict(int)
    type_counts = defaultdict(int)
    priority_hours = defaultdict(float)
    total_duration = 0
    priority_duration = 0
    meeting_hours = 0.0

    for a in activities:
        source_counts[a["source"]] += 1
        if a.get("activity_type"):
            type_counts[a["activity_type"]] += 1
        dur = a.get("duration_minutes") or _estimate_duration(a["source"])
        total_duration += dur
        if a.get("priority_name") and a["priority_name"] != "Other":
            priority_hours[a["priority_name"]] += dur / 60.0
            priority_duration += dur
        if a["source"] == "calendar":
            meeting_hours += dur / 60.0

    total_hours = total_duration / 60.0 if total_duration else 1.0
    alignment_pct = (priority_duration / total_duration * 100) if total_duration else 0

    # Priority breakdown as percentages
    priority_breakdown = {}
    for name, hours in priority_hours.items():
        priority_breakdown[name] = round(hours / total_hours * 100, 1)

    # Fragmentation score: context switches per hour
    frag = _compute_fragmentation(activities)

    # Get PM name
    pm = db.get_team_member(pm_id)
    pm_name = pm["name"] if pm else pm_id

    # Top priority
    top_priority = max(priority_hours, key=priority_hours.get) if priority_hours else "None"

    return {
        "pm_id": pm_id,
        "pm_name": pm_name,
        "total_activities": len(activities),
        "meetings": source_counts.get("calendar", 0),
        "messages": source_counts.get("slack", 0),
        "emails": source_counts.get("email", 0),
        "tickets": source_counts.get("jira", 0),
        "alignment_pct": round(alignment_pct, 1),
        "top_priority": top_priority,
        "meeting_hours": round(meeting_hours, 1),
        "fragmentation_score": round(frag, 2),
        "source_breakdown": dict(source_counts),
        "type_breakdown": dict(type_counts),
        "priority_breakdown": priority_breakdown,
    }


def compute_dashboard(date_from: str = None, date_to: str = None) -> dict:
    """Compute aggregated dashboard data for all PMs."""
    members = db.get_team_members()
    pm_ids = [m["id"] for m in members if m["role"] == "pm"]

    summaries = []
    total_acts = 0
    alignment_sum = 0

    for pm_id in pm_ids:
        s = compute_pm_summary(pm_id, date_from, date_to)
        summaries.append(s)
        total_acts += s["total_activities"]
        alignment_sum += s["alignment_pct"]

    avg_alignment = alignment_sum / len(pm_ids) if pm_ids else 0

    # Priority coverage: which PMs cover which priorities
    priority_coverage = defaultdict(dict)
    for s in summaries:
        for pname, pct in s["priority_breakdown"].items():
            priority_coverage[pname][s["pm_name"]] = pct

    # Team balance: std dev of total activities (lower = more balanced)
    acts_list = [s["total_activities"] for s in summaries]
    if len(acts_list) > 1:
        mean = sum(acts_list) / len(acts_list)
        variance = sum((x - mean) ** 2 for x in acts_list) / len(acts_list)
        std_dev = variance ** 0.5
        balance = max(0, 100 - std_dev * 2)  # higher = more balanced
    else:
        balance = 100

    # Get latest recommendations
    latest_week = db.get_latest_week_iso()
    recs = db.get_recommendations(week_iso=latest_week, limit=12) if latest_week else []

    # Generate top insight
    top_insight = _generate_top_insight(summaries)

    return {
        "total_activities": total_acts,
        "avg_alignment_pct": round(avg_alignment, 1),
        "total_recommendations": len(recs),
        "team_balance_score": round(balance, 1),
        "pm_summaries": summaries,
        "priority_coverage": dict(priority_coverage),
        "top_insight": top_insight,
        "recommendations": recs,
    }


def compute_pm_trends(pm_id: str, weeks: int = 4) -> list[dict]:
    """Compute weekly trend data for a PM."""
    today = datetime.now()
    trends = []

    for w in range(weeks):
        end = today - timedelta(weeks=w)
        start = end - timedelta(weeks=1)
        date_from = start.strftime("%Y-%m-%dT00:00:00")
        date_to = end.strftime("%Y-%m-%dT23:59:59")

        summary = compute_pm_summary(pm_id, date_from, date_to)
        week_iso = start.strftime("%G-W%V")
        summary["week_iso"] = week_iso
        trends.append(summary)

    trends.reverse()
    return trends


def detect_anomalies(pm_id: str = None) -> list[dict]:
    """Detect anomalies for one PM or all PMs."""
    members = db.get_team_members()
    if pm_id:
        members = [m for m in members if m["id"] == pm_id]

    anomalies = []
    for m in members:
        if m["role"] != "pm":
            continue
        summary = compute_pm_summary(m["id"])

        # Meeting bloat
        if summary["meeting_hours"] > config.MEETING_HOURS_THRESHOLD:
            anomalies.append({
                "pm_id": m["id"],
                "pm_name": m["name"],
                "type": "meeting_bloat",
                "severity": "warning",
                "message": f"{m['name']} has {summary['meeting_hours']} meeting hours this week (threshold: {config.MEETING_HOURS_THRESHOLD}h)",
            })

        # Low alignment
        if summary["alignment_pct"] < 50:
            anomalies.append({
                "pm_id": m["id"],
                "pm_name": m["name"],
                "type": "priority_drift",
                "severity": "warning",
                "message": f"{m['name']}'s priority alignment is only {summary['alignment_pct']}%",
            })

        # High fragmentation
        if summary["fragmentation_score"] > config.FRAGMENTATION_THRESHOLD:
            anomalies.append({
                "pm_id": m["id"],
                "pm_name": m["name"],
                "type": "fragmentation",
                "severity": "info",
                "message": f"{m['name']}'s fragmentation score is {summary['fragmentation_score']} (threshold: {config.FRAGMENTATION_THRESHOLD})",
            })

        # Low-value time
        low_value_pct = summary["type_breakdown"].get("LowValue", 0) / max(summary["total_activities"], 1) * 100
        if low_value_pct > config.LOW_VALUE_THRESHOLD * 100:
            anomalies.append({
                "pm_id": m["id"],
                "pm_name": m["name"],
                "type": "low_value",
                "severity": "info",
                "message": f"{m['name']} spent {low_value_pct:.0f}% of time on low-value activities",
            })

    return anomalies


# ── Helpers ────────────────────────────────────────────────────────────────────

def _estimate_duration(source: str) -> int:
    """Estimate duration in minutes for activities without explicit duration."""
    return {"calendar": 30, "slack": 5, "email": 10, "jira": 15, "gdrive": 20, "transcript": 45}.get(source, 10)


def _compute_fragmentation(activities: list[dict]) -> float:
    """Compute context switches per hour based on source/priority changes."""
    if len(activities) < 2:
        return 0.0

    sorted_acts = sorted(activities, key=lambda a: a["occurred_at"])
    switches = 0
    for i in range(1, len(sorted_acts)):
        prev = sorted_acts[i - 1]
        curr = sorted_acts[i]
        # Count a switch if source or priority changed
        if prev["source"] != curr["source"] or prev.get("priority_name") != curr.get("priority_name"):
            switches += 1

    # Estimate total hours from activity span
    if sorted_acts:
        try:
            first = datetime.fromisoformat(sorted_acts[0]["occurred_at"])
            last = datetime.fromisoformat(sorted_acts[-1]["occurred_at"])
            hours = max((last - first).total_seconds() / 3600, 1)
        except (ValueError, TypeError):
            hours = 40  # fallback to standard work week
    else:
        hours = 40

    return switches / hours


def _generate_top_insight(summaries: list[dict]) -> str:
    """Generate a single top insight from PM summaries."""
    insights = []

    # Check for meeting bloat
    for s in summaries:
        if s["meeting_hours"] > config.MEETING_HOURS_THRESHOLD:
            insights.append(
                f"{s['pm_name']}'s meeting load is {s['meeting_hours']}h/week — "
                f"{s['meeting_hours'] / max(min(s2['meeting_hours'] for s2 in summaries), 1):.1f}x "
                f"the team minimum. Consider delegating recurring syncs."
            )

    # Check for alignment gaps
    for s in summaries:
        if s["alignment_pct"] < 60:
            insights.append(
                f"{s['pm_name']}'s priority alignment is {s['alignment_pct']}% — "
                f"below the 60% target. Review time allocation against stated priorities."
            )

    # Check for unbalanced priority coverage
    priority_names = [p["name"] for p in config.DEFAULT_PRIORITIES]
    for pname in priority_names:
        covered_by = [s["pm_name"] for s in summaries if s["priority_breakdown"].get(pname, 0) > 10]
        if not covered_by:
            insights.append(f"No PM is spending significant time on {pname} — potential coverage gap.")

    if insights:
        return insights[0]
    return "Team is well-aligned with stated priorities this week. Keep up the momentum!"
