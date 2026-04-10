"""Ad-hoc Q&A chat API route — uses FTS5 + Claude tool_use (or local fallback)."""

import json
import re
import uuid
import logging
from typing import Optional

from fastapi import APIRouter
from backend.storage import db
from backend.storage.models import ChatRequest, ChatResponse
from backend.config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

CHAT_SYSTEM = """You are the PM Productivity Agent assistant. You help the PM lead (Alex) answer questions about his team's activities, time allocation, and priorities.

Team members: Jordan Park, Morgan Lee, Taylor Kim.
Priorities: Analytics Agent Beta, Omni Integration, Data Platform Alignment.

You have tools to search and query the activity database. Use them to find evidence before answering.
Always cite specific activities or data points. Never make claims without evidence from the database.
Be concise and coaching-oriented in tone."""

TOOLS = [
    {
        "name": "search_activities",
        "description": "Full-text search over activity titles and summaries. Returns matching activities with their classifications.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (keywords)"},
                "limit": {"type": "integer", "description": "Max results", "default": 20},
            },
            "required": ["query"],
        },
    },
    {
        "name": "run_sql_query",
        "description": """Run a read-only SQL query against the activity database. Tables:
- activities (id, pm_id, source, title, summary, duration_minutes, occurred_at)
- activity_classifications (activity_id, priority_name, activity_type, leverage, confidence)
- recommendations (week_iso, pm_id, pm_name, kind, action, rationale, evidence_ids, judge_score, status)
- team_members (id, name, email, role)
- priorities (id, name, description, weight, active)""",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SELECT SQL query"},
            },
            "required": ["query"],
        },
    },
]


def _handle_tool_call(name: str, input_data: dict) -> str:
    """Execute a tool call and return the result as a string."""
    try:
        if name == "search_activities":
            results = db.search_activities_fts(input_data["query"], limit=input_data.get("limit", 20))
            return json.dumps(results[:20], default=str)
        elif name == "run_sql_query":
            results = db.run_read_only_sql(input_data["query"])
            return json.dumps(results[:50], default=str)
        else:
            return json.dumps({"error": f"Unknown tool: {name}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


def _has_api_key() -> bool:
    import os
    return bool(ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY"))


def _detect_pm(msg: str) -> Optional[str]:
    """Extract PM name/id from the user message."""
    msg_lower = msg.lower()
    for name, pm_id in [("jordan", "jordan-park"), ("morgan", "morgan-lee"), ("taylor", "taylor-kim")]:
        if name in msg_lower:
            return pm_id
    return None


def _detect_priority(msg: str) -> Optional[str]:
    msg_lower = msg.lower()
    for kw, pri in [("omni", "Omni Integration"), ("whatsapp", "Omni Integration"), ("tiger team", "Omni Integration"),
                     ("analytics", "Analytics Agent Beta"), ("aab", "Analytics Agent Beta"),
                     ("voc", "Analytics Agent Beta"), ("voice of customer", "Analytics Agent Beta"),
                     ("csn", "Analytics Agent Beta"), ("bug status", "Analytics Agent Beta"),
                     ("data platform", "Data Platform Alignment"), ("dpa", "Data Platform Alignment")]:
        if kw in msg_lower:
            return pri
    return None


def _local_answer(message: str) -> str:
    """Answer common questions using direct DB queries — no LLM needed."""
    msg = message.lower()
    pm_id = _detect_pm(message)
    priority = _detect_priority(message)

    # --- Time spent on a priority by a PM ---
    if pm_id and priority and ("time" in msg or "spend" in msg or "hours" in msg or "how much" in msg):
        rows = db.run_read_only_sql(
            f"""SELECT SUM(a.duration_minutes) as total_min, COUNT(*) as count
                FROM activities a
                JOIN activity_classifications c ON c.activity_id = a.id
                WHERE a.pm_id = '{pm_id}' AND c.priority_name = '{priority}'"""
        )
        if rows and rows[0]["total_min"]:
            hours = round(rows[0]["total_min"] / 60, 1)
            return f"Based on the activity ledger, **{pm_id.replace('-', ' ').title()}** spent approximately **{hours} hours** across **{rows[0]['count']} activities** on {priority}.\n\nThis includes meetings, Jira tickets, Slack discussions, and emails related to this priority."
        return f"No activities found for {pm_id.replace('-', ' ').title()} on {priority}."

    # --- Meeting hours comparison ---
    if "meeting" in msg and ("compare" in msg or "across" in msg or "all" in msg):
        rows = db.run_read_only_sql(
            """SELECT a.pm_id, tm.name, SUM(a.duration_minutes) as total_min, COUNT(*) as count
               FROM activities a
               JOIN team_members tm ON tm.id = a.pm_id
               WHERE a.source = 'calendar'
               GROUP BY a.pm_id ORDER BY total_min DESC"""
        )
        if rows:
            lines = ["Here's the **meeting hours comparison** across all PMs:\n"]
            for r in rows:
                hours = round(r["total_min"] / 60, 1)
                lines.append(f"• **{r['name']}**: {hours} hours ({r['count']} meetings)")
            lines.append(f"\n{rows[0]['name']} has the highest meeting load — worth checking if some can be delegated or made async.")
            return "\n".join(lines)

    # --- Lowest priority alignment ---
    if "lowest" in msg and ("alignment" in msg or "priority" in msg):
        rows = db.run_read_only_sql(
            """SELECT a.pm_id, tm.name, COUNT(*) as total,
                      SUM(CASE WHEN c.priority_name != 'Other' THEN 1 ELSE 0 END) as aligned
               FROM activities a
               JOIN team_members tm ON tm.id = a.pm_id
               LEFT JOIN activity_classifications c ON c.activity_id = a.id
               GROUP BY a.pm_id ORDER BY (1.0 * aligned / total) ASC"""
        )
        if rows:
            r = rows[0]
            pct = round(100 * r["aligned"] / r["total"], 1) if r["total"] else 0
            return f"**{r['name']}** has the lowest priority alignment at **{pct}%** ({r['aligned']}/{r['total']} activities aligned to a stated priority).\n\nThis suggests some of their time is going to work outside the team's top 3 priorities."

    # --- Time sinks / biggest for a PM ---
    if pm_id and ("time sink" in msg or "biggest" in msg or "breakdown" in msg or "activity" in msg):
        rows = db.run_read_only_sql(
            f"""SELECT c.activity_type, COUNT(*) as count, SUM(a.duration_minutes) as total_min
                FROM activities a
                JOIN activity_classifications c ON c.activity_id = a.id
                WHERE a.pm_id = '{pm_id}'
                GROUP BY c.activity_type ORDER BY total_min DESC"""
        )
        pm_name = pm_id.replace('-', ' ').title()
        if rows:
            lines = [f"Here's **{pm_name}'s** activity breakdown by type:\n"]
            for r in rows:
                hours = round(r["total_min"] / 60, 1)
                lines.append(f"• **{r['activity_type']}**: {hours} hours ({r['count']} activities)")
            top = rows[0]
            lines.append(f"\nThe biggest time investment is in **{top['activity_type']}** at {round(top['total_min']/60,1)} hours.")
            return "\n".join(lines)

    # --- Source breakdown for a PM ---
    if pm_id and ("source" in msg or "breakdown" in msg):
        rows = db.run_read_only_sql(
            f"""SELECT source, COUNT(*) as count, SUM(duration_minutes) as total_min
                FROM activities WHERE pm_id = '{pm_id}'
                GROUP BY source ORDER BY total_min DESC"""
        )
        pm_name = pm_id.replace('-', ' ').title()
        if rows:
            lines = [f"Here's **{pm_name}'s** activity breakdown by source:\n"]
            for r in rows:
                hours = round(r["total_min"] / 60, 1)
                lines.append(f"• **{r['source'].title()}**: {hours} hours ({r['count']} activities)")
            return "\n".join(lines)

    # --- Team balance on a priority ---
    if priority and ("balance" in msg or "coverage" in msg or "team" in msg):
        rows = db.run_read_only_sql(
            f"""SELECT a.pm_id, tm.name, COUNT(*) as count, SUM(a.duration_minutes) as total_min
                FROM activities a
                JOIN activity_classifications c ON c.activity_id = a.id
                JOIN team_members tm ON tm.id = a.pm_id
                WHERE c.priority_name = '{priority}'
                GROUP BY a.pm_id ORDER BY total_min DESC"""
        )
        if rows:
            lines = [f"Here's the team's coverage of **{priority}**:\n"]
            for r in rows:
                hours = round(r["total_min"] / 60, 1)
                lines.append(f"• **{r['name']}**: {hours} hours ({r['count']} activities)")
            if len(rows) >= 2:
                top_h = rows[0]["total_min"] / 60
                bot_h = rows[-1]["total_min"] / 60
                if top_h > bot_h * 2:
                    lines.append(f"\n⚠️ **{rows[0]['name']}** is carrying significantly more load than **{rows[-1]['name']}** on this priority.")
                else:
                    lines.append(f"\nThe team looks relatively balanced on this priority.")
            return "\n".join(lines)

    # --- Fallback: FTS search ---
    keywords = re.sub(r'[^\w\s]', '', message).strip()
    if keywords:
        results = db.search_activities_fts(keywords, limit=10)
        if results:
            lines = [f"I found **{len(results)} activities** matching your query:\n"]
            for r in results[:8]:
                lines.append(f"• [{r.get('source', '?').title()}] **{r.get('title', 'Untitled')}** — {r.get('pm_id', '').replace('-', ' ').title()}")
            lines.append("\nTry asking a more specific question about time, priorities, or a particular team member for deeper analysis.")
            return "\n".join(lines)

    return "I can help you analyze your team's activities, time allocation, and priorities. Try asking something like:\n\n• \"How much time did Jordan spend on Omni Integration?\"\n• \"Which PM has the lowest priority alignment?\"\n• \"Compare meeting hours across all PMs\""


@router.post("/chat")
def chat(body: ChatRequest) -> ChatResponse:
    session_id = body.session_id or str(uuid.uuid4())

    # Save user message
    db.save_chat_message(session_id, "user", body.message)

    if _has_api_key():
        # Full LLM mode with Claude tool_use
        from backend.llm.claude import call_chat_with_tools

        history = db.get_chat_history(session_id, limit=10)
        messages = [{"role": m["role"], "content": m["content"]} for m in history]
        messages.append({"role": "user", "content": body.message})

        response = call_chat_with_tools(messages, TOOLS, system=CHAT_SYSTEM)

        # Handle tool use loop (max 3 iterations)
        iterations = 0
        while response.stop_reason == "tool_use" and iterations < 3:
            iterations += 1
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result_str = _handle_tool_call(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            response = call_chat_with_tools(messages, TOOLS, system=CHAT_SYSTEM)

        final_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                final_text += block.text
    else:
        # Local fallback — answer using direct DB queries
        final_text = _local_answer(body.message)

    db.save_chat_message(session_id, "assistant", final_text)
    return ChatResponse(response=final_text, context={"session_id": session_id})
