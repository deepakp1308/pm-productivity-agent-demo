"""Central configuration for the PM Productivity Agent."""

import os

# ── Team ───────────────────────────────────────────────────────────────────────

TEAM_LEAD = {
    "id": "alex-chen",
    "name": "Alex Chen",
    "email": "alex_chen@company.com",
    "role": "pm_lead",
}

TEAM_MEMBERS = [
    {"id": "jordan-park", "name": "Jordan Park", "email": "jordan_park@company.com", "role": "pm", "description": "Principal Product Manager, Reporting & Analytics"},
    {"id": "morgan-lee", "name": "Morgan Lee", "email": "morgan_lee@company.com", "role": "pm", "description": "Senior Staff Product Manager"},
    {"id": "taylor-kim", "name": "Taylor Kim", "email": "taylor_kim@company.com", "role": "pm", "description": "Product Manager 2"},
]

# ── Priorities ─────────────────────────────────────────────────────────────────

DEFAULT_PRIORITIES = [
    {
        "name": "Insights Agent & Scaled AI",
        "description": "Ship Analytics/Insights Agent: discoverability, funnel performance, May 11 GTM, deliverability insights, SMS insights, and Freddie skills alignment.",
        "weight": 0.40,
    },
    {
        "name": "Email Report Reimagine & Custom Reports",
        "description": "Modernize reporting: Email Report Reimagine, Comparative→Custom Reports transition, segment discovery, marketing diagnostics, and data consistency.",
        "weight": 0.35,
    },
    {
        "name": "Marketing Performance Reporting via QB BI",
        "description": "Enable Marketing Performance Reporting in QBO via BI Platform: KPI/dashboard requirements, cross-functional alignment, and Marketing Platform-QBO data integration.",
        "weight": 0.25,
    },
]

# ── LLM Model Routing ─────────────────────────────────────────────────────────

MODEL_MAP = {
    "filter": "claude-haiku-4-5-20251001",
    "classify": "claude-sonnet-4-5-20250514",
    "recommend": "claude-sonnet-4-5-20250514",
    "judge": "claude-sonnet-4-5-20250514",
    "chat": "claude-sonnet-4-5-20250514",
}

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ── Classification taxonomy ────────────────────────────────────────────────────

ACTIVITY_TYPES = [
    "Strategy",       # strategic planning, roadmap, vision
    "Discovery",      # user research, interviews, data analysis
    "Execution",      # ticket work, PRs, implementation
    "Stakeholder",    # stakeholder mgmt, exec alignment, cross-team
    "InternalOps",    # team processes, hiring, admin
    "Reactive",       # interrupts, escalations, firefighting
    "LowValue",       # low-impact meetings, status updates, duplicate work
]

LEVERAGE_LEVELS = ["High", "Medium", "Low"]

# ── Rule-based classification patterns ─────────────────────────────────────────
# Format: (title_pattern, activity_type, priority_hint)
# These are checked BEFORE the LLM classifier runs.

RULE_BASED_PATTERNS = [
    # Jira/ticket patterns → Execution
    (r"(?i)\bREPORTING-\d+", "Execution", None),
    (r"(?i)\b(ticket|bug|sprint|story|epic)\b", "Execution", None),
    # 1:1 patterns → Stakeholder
    (r"(?i)\b1[:\-]1\b", "Stakeholder", None),
    (r"(?i)\b(skip.?level|exec.?sync|leadership)\b", "Stakeholder", None),
    # Standup/retro → InternalOps
    (r"(?i)\b(standup|stand.up|retro|retrospective|team.sync|all.hands)\b", "InternalOps", None),
    # User research / interview → Discovery
    (r"(?i)\b(user.research|interview|usability|discovery|prototype.review)\b", "Discovery", None),
    # Roadmap / strategy → Strategy
    (r"(?i)\b(roadmap|strategy|vision|OKR|quarterly.planning|PRD)\b", "Strategy", None),
    # 1:1 with <> notation → Stakeholder
    (r"<>", "Stakeholder", None),
    # Program Review / Leads Sync → InternalOps
    (r"(?i)\b(program.review|leads.sync|OpMech)\b", "InternalOps", None),
    # Priority hints from keywords
    (r"(?i)\b(insights.agent|analytics.agent|deliverability.agent|scaled.ai|freddie|mc_insights_skill|SMS.insight|funnel.performance|discoverability|GTM|bounce.reason|CDP|StarRocks|agent.support|repeat.engagement|entry.point|feature.flag|beta.v2|S2S.event|shopify.analytics)\b", None, "Insights Agent & Scaled AI"),
    (r"(?i)\b(email.report|custom.report|comparative|segment.discovery|diagnostics|driver.analysis|tiger|voc|hvc|escalation|canary|click.performance|click.map|whatsapp.report|export|recipient.activity|ecomm|tooltip|DFAD|data.consistency|multivariate|MVT|zero.state|marketing.dashboard|CHEQ|IP.feeds|data.retention|purchase.prediction|close.the.loop|QA.timeline)\b", None, "Email Report Reimagine & Custom Reports"),
    (r"(?i)\b(MPR|BI.platform|QB.BI|marketing.performance|QBO.*plan|joint.*user|KPI.*dashboard|dashboard.requirement|mp.into.bi|57k|plan.type.distribution)\b", None, "Marketing Performance Reporting via QB BI"),
]

# ── Anomaly thresholds ─────────────────────────────────────────────────────────

MEETING_HOURS_THRESHOLD = 20.0  # >20 hrs/week = meeting bloat alert
FRAGMENTATION_THRESHOLD = 5.0   # >5 context switches per hour
PRIORITY_DRIFT_WEEKS = 2        # alert if off-priority for >2 weeks
LOW_VALUE_THRESHOLD = 0.20      # >20% of time on LowValue = alert

# ── Server ─────────────────────────────────────────────────────────────────────

API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("API_PORT", "8000"))
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
