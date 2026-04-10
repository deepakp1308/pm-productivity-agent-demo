# PM Productivity Agent

> AI-powered productivity coaching for product management teams. Analyzes work signals from Slack, Gmail, Calendar, and Jira to surface priority alignment, key decisions, open blockers, and evidence-backed coaching recommendations.

## Live Demo

[View the live dashboard](https://deepakp1308.github.io/pm-productivity-agent-demo/)

## What It Does

The PM Productivity Agent ingests raw work signals -- Slack messages, calendar events, Gmail threads, Jira tickets, and shared documents -- and transforms them into actionable coaching insights for a PM lead managing a team of product managers. Instead of asking "what did everyone work on this week?", the agent answers that question automatically, classifies every activity against stated team priorities, and surfaces the three most important coaching recommendations per PM: what to **Accelerate**, what to **Cut**, and what to **Redirect**.

The system runs a complete analysis pipeline every week: ingest signals from data sources, classify each activity using a tiered rule-based + LLM approach, compute priority alignment and fragmentation metrics, generate evidence-backed recommendations, run each recommendation through a judge layer for quality control, and deliver results through an interactive dashboard. The dashboard provides a PM lead with a single-pane-of-glass view across their team -- KPIs, priority breakdown bars, 10-week trend charts, key decisions extracted from team discussions, open questions with urgency badges, and a chat interface for ad-hoc queries against the activity database.

Every recommendation must cite specific activity IDs as evidence. Every judge score is computed from chain-of-thought reasoning with binary harm/privacy gates. The system is designed around the principle that coaching should be evidence-backed, never speculative.

## Architecture

### System Overview

```
Data Sources          Classification          Analysis           AI Pipeline          Frontend
-----------          --------------          --------           -----------          --------
Slack MCP     -->    Rule-based fast    -->  compute_pm_     --> Recommender    -->  Dashboard
Gmail MCP            path (regex)            summary()           (3 recs/PM)         PM Detail
Calendar             |                      priority_           |                   Recommendations
Jira                 v                      alignment           v                   Decisions
                     Claude Sonnet          fragmentation       Judge Layer         Ask Agent
                     (ambiguous              anomaly             (score 1-3,         (chat)
                      cases)                 detection           harm/privacy
                                                                 gates)
```

### Tech Stack

- **Frontend**: Next.js 15, React 19, Tailwind CSS 4, Recharts
- **Backend**: Python 3.9+, FastAPI, SQLite + FTS5, Pydantic v2
- **AI Pipeline**: Anthropic Claude API (Sonnet for classification, Opus for recommendations + judging)
- **Data Sources**: Slack MCP, Gmail MCP, Google Calendar (via email invites)
- **Hosting**: GitHub Pages (static export), backend optional for live AI chat
- **Design System**: Custom design tokens (dark navy sidebar, teal AI accents)

## How It Was Built

### Phase 1: Data Collection -- What signals to capture

The agent pulls from four primary data sources to build a complete picture of PM activity:

- **Slack**: Public channel messages (e.g., `#mp-insights-agent`, `#rna-tiger-voc`), DMs with the PM lead, and shared documents posted in threads. Channel messages reveal what PMs are actively pushing forward, blockers they're raising, and decisions they're driving.
- **Gmail**: Email threads including PRD review threads, stakeholder alignment emails, and vendor follow-ups. These capture cross-functional coordination that doesn't happen in Slack.
- **Calendar**: Meeting titles, duration, and participant lists. The agent doesn't read meeting content -- it infers activity type from the meeting title and participants (e.g., a "1:1" with the PM lead is Stakeholder; a "Sprint Review" is Execution).
- **Jira**: Ticket titles, status changes, and comments. These map directly to Execution activities with priority hints from the ticket naming convention (e.g., `REPORTING-9901: Analytics Agent -- discoverability entry points v2`).

Each activity is stored with a source, title, summary, duration, timestamp, and participant list. The schema supports ~600 activities per 4-week period across a 3-person PM team.

### Phase 2: Activity Classification -- Making sense of raw signals

Classification uses a **tiered approach** to maximize accuracy while minimizing LLM costs:

**Tier 1: Rule-based fast path** -- Regex patterns match obvious signals before any LLM call. This handles ~60-70% of activities at zero cost:

```python
RULE_BASED_PATTERNS = [
    # Jira/ticket patterns -> Execution
    (r"(?i)\bREPORTING-\d+", "Execution", None),
    # 1:1 patterns -> Stakeholder
    (r"(?i)\b1[:\-]1\b", "Stakeholder", None),
    # Standup/retro -> InternalOps
    (r"(?i)\b(standup|retro|team.sync)\b", "InternalOps", None),
    # Priority hints from keywords
    (r"(?i)\b(insights.agent|analytics.agent|deliverability)\b",
     None, "Insights Agent & Scaled AI"),
]
```

**Tier 2: Claude Sonnet** -- For activities that don't match any rule, the classifier sends the activity to Claude Sonnet with the team's current priorities as context. The LLM returns structured output matching a Pydantic schema:

```python
class ClassifierOutput(BaseModel):
    type: ActivityType       # Strategy|Discovery|Execution|...
    priority: str            # Exact priority name or "Other"
    leverage: Leverage       # High|Medium|Low
    confidence: float        # 0.0-1.0
    reasoning: str           # One-sentence explanation
```

The **3-axis taxonomy** classifies every activity along:
1. **Type**: Strategy, Discovery, Execution, Stakeholder, InternalOps, Reactive, LowValue
2. **Priority**: Which of the team's stated priorities this maps to (or "Other")
3. **Leverage**: High (shipped/decided), Medium (in progress), Low (blocked/waiting)

### Phase 3: Analysis Engine -- Pure Python aggregation

The analysis engine (`compute_pm_summary`) runs entirely in Python with zero LLM calls. It computes:

- **Priority alignment**: Percentage of time spent on stated team priorities vs. "Other" work
- **Source breakdown**: Distribution across calendar/slack/email/jira
- **Type breakdown**: Distribution across Strategy/Discovery/Execution/etc.
- **Meeting hours**: Total calendar time, used for meeting-bloat detection
- **Fragmentation score**: Context switches per hour (source or priority changes between consecutive activities)
- **Anomaly detection**: Flags when meeting hours exceed threshold, alignment drops below 50%, fragmentation is too high, or low-value time exceeds 20%

```python
def compute_pm_summary(pm_id, date_from, date_to) -> dict:
    activities = db.get_activities(pm_id=pm_id, ...)
    # ... pure aggregation over activities
    return {
        "alignment_pct": round(priority_duration / total_duration * 100, 1),
        "meeting_hours": round(meeting_hours, 1),
        "fragmentation_score": round(switches / hours, 2),
        "priority_breakdown": { "Priority A": 42.1, ... },
        ...
    }
```

### Phase 4: Recommendation Generation -- Claude as coaching advisor

The recommender sends each PM's aggregated summary + evidence rows to Claude and asks for exactly 3 recommendations:

1. **Accelerate** -- What's working and should be doubled down on
2. **Cut** -- What's consuming time without proportional value
3. **Redirect** -- What should be shifted to a different approach or owner

Every recommendation must cite `evidence_ids` -- actual activity IDs from the database. The structured output contract enforces this:

```python
class BriefingOutput(BaseModel):
    summary: str
    alignment_pct: float
    recommendations: list[Recommendation] = Field(min_length=3, max_length=3)
    uncertainty_flags: list[str]

class Recommendation(BaseModel):
    kind: RecKind                            # Accelerate|Cut|Redirect
    action: str                              # What to do
    rationale: str                           # Why
    evidence_ids: list[int] = Field(min_length=1)  # Proof
```

The system prompt provides the PM's aggregates, evidence rows (id + source + title + summary + classification), and current priorities with weights. The tone is "coaching, not judging" -- respecting invisible work like stakeholder management.

### Phase 5: Judge Layer -- Quality gate before delivery

Every recommendation passes through a judge before it reaches the dashboard. The judge uses **chain-of-thought reasoning** followed by structured scoring:

```python
class JudgeScore(BaseModel):
    reasoning: str          # Chain-of-thought BEFORE scores
    faithfulness: int       # 1-3: Does it follow from evidence?
    priority_fit: int       # 1-3: Aligned with stated priorities?
    specificity: int        # 1-3: Actionable and specific?
    harm_risk: bool         # True = safe, False = blocked
    privacy_compliance: bool # True = compliant, False = blocked
    block: bool             # Hard block if any gate fails
```

**Hard-block logic**: A recommendation is blocked if `harm_risk=False` OR `privacy_compliance=False` OR any dimension scores 1. This prevents vague, harmful, or privacy-violating recommendations from reaching the PM lead.

The composite score maps the three 1-3 dimensions to a 0-5 scale shown in the dashboard.

### Phase 6: Decision Synthesis -- What the team decided

Beyond time allocation, the agent extracts **key decisions** and **open questions** from Slack conversations. These are particularly valuable because decisions often happen in DMs or thread replies that a PM lead might miss:

- **Key decisions**: Extracted from messages where PMs align with engineers, designers, or stakeholders on a specific approach (e.g., "Agent discoverability entry point: homepage approach validated")
- **Open questions**: Unresolved items with urgency badges (high/medium/low) and PM ownership (e.g., "StarRocks join query bugs blocking Tiger Team backend schema updates" -- urgency: high)

### Phase 7: Frontend -- Static dashboard with live data feel

The frontend is a Next.js 15 static export that works entirely on GitHub Pages with zero backend. All data comes from pre-baked JSON files in `/public/api/`. The client-side chat engine (`chat-engine.ts`) queries these JSON files directly to answer questions without any server.

Key frontend patterns:
- **Priority color consistency**: The same priority always gets the same color across all charts and views (navy for Priority 1, blue for Priority 2, teal for Priority 3, pink for Other)
- **10-week trend charts**: Line chart for alignment trend, stacked area chart for priority breakdown trend -- both using Recharts
- **Source filter pills**: Activity feeds can be filtered by calendar/slack/email/jira using pill-style toggle buttons
- **Responsive layout**: Dark navy sidebar (240px) + scrollable main content area

### Phase 8: Automation -- Weekly refresh pipeline

The pipeline is designed to run on a weekly cadence (Friday 9 AM):

1. Pull latest Slack/Gmail/Calendar/Jira data via MCP connectors
2. Re-seed the database with fresh activities
3. Run the classification + recommendation + judge pipeline
4. Export dashboard data to static JSON
5. Build and deploy the Next.js static export
6. Send a Slack summary to the PM lead

The pipeline is triggered via CLI (`python -m backend.main --seed --run-pipeline --use-llm`) or the FastAPI endpoint (`POST /api/pipeline/run`).

## Dashboard Views

### Main Dashboard
- KPI cards: total activities, average priority alignment, recommendation count, team balance score
- AI weekly insight banner (auto-generated from PM summaries)
- Team overview with clickable PM rows showing priority breakdown bars
- Key decisions preview with AI attribution markers
- Open questions with urgency badges (high = red, medium = yellow, low = blue)

### PM Detail View
- Source breakdown donut chart (calendar/slack/email/jira)
- Priority breakdown horizontal bars with percentage labels
- 10-week priority alignment trend (line chart)
- 10-week priority breakdown trend (stacked area chart)
- Coaching recommendations grouped by Accelerate/Cut/Redirect
- Activity feed with source filter pills and priority tags

### Recommendations
- Grouped by PM with avatar initials and Accelerate/Cut/Redirect badges
- Judge scores (0-5), evidence item counts, expandable judge reasoning
- Blocked recommendations flagged with "Blocked by judge" badge

### Decisions & Open Questions
- Key decisions with PM attribution, channel source, date, and related priority
- Open questions with urgency badges and PM ownership
- PM filter pills for team-level or individual views

### Ask the Agent (Chat)
- Client-side query engine over static JSON data (no backend needed)
- Handles: time allocation queries, meeting comparisons, priority alignment, decisions, blockers
- Keyword search fallback when structured queries don't match
- Suggested question pills for common queries

## Project Structure

```
pm-agent-demo/
  backend/
    agents/
      classifier.py       # Tiered classification: rules + Claude Sonnet
      recommender.py       # Claude-powered coaching recommendations
      judge.py             # Quality gate with chain-of-thought scoring
      orchestrator.py      # Pipeline: classify -> analyze -> recommend -> judge
    analysis/
      engine.py            # Pure Python aggregation: alignment, fragmentation, anomalies
    api/
      chat.py              # Q&A chat with FTS5 search + Claude tool_use
      dashboard.py         # Dashboard data endpoint
      activities.py        # Activity CRUD + search
      pm_views.py          # PM detail view endpoints
      priorities.py        # Priority management
      recommendations.py   # Recommendation retrieval
    llm/
      claude.py            # Claude API wrapper with structured output
    seed/
      seed_data.py         # Realistic mock data generator (~600 activities)
    storage/
      db.py                # SQLite + FTS5 database layer
      models.py            # Pydantic v2 models for API + LLM contracts
    config.py              # Team, priorities, model routing, thresholds
    main.py                # FastAPI app + CLI entry point
  frontend/
    src/
      app/
        page.tsx           # Main dashboard with KPIs, team overview, decisions
        layout.tsx         # Root layout with dark navy sidebar navigation
        chat/page.tsx      # Chat interface with suggested questions
        decisions/page.tsx # Key decisions and open questions view
        priorities/page.tsx # Priority management with weight sliders
        recommendations/page.tsx # Coaching recommendations grouped by PM
        pm/[id]/
          page.tsx         # PM detail with charts, recs, activity feed
          layout.tsx       # Static params for PM routes
      lib/
        api.ts             # Data fetching layer (static JSON in production)
        chat-engine.ts     # Client-side query engine over JSON data
    public/
      api/                 # Pre-baked JSON data files for static deployment
        dashboard.json
        team.json
        decisions.json
        recommendations.json
        priorities.json
        trends.json
        activities-{pm-id}.json
        pm-{pm-id}-summary.json
    next.config.ts         # Next.js configuration
```

## Running Locally

### Prerequisites

- Python 3.9+
- Node.js 18+
- Anthropic API key (optional -- works without for static mode)

### Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m backend.main --seed --serve

# Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:3000`. The backend API runs at `http://localhost:8000`.

### Static Mode (No Backend)

The frontend works entirely standalone using pre-baked JSON data:

```bash
cd frontend
npm install
npm run dev
```

All data is served from `/public/api/*.json`. The chat engine runs client-side.

### With Live AI Chat

```bash
export ANTHROPIC_API_KEY=your-key-here
python -m backend.main --seed --serve --use-llm
```

This enables Claude-powered chat with tool_use (FTS5 search + SQL queries against the activity database).

### Run the Full Pipeline

```bash
export ANTHROPIC_API_KEY=your-key-here
python -m backend.main --seed --run-pipeline --use-llm
```

This seeds the database, runs classification (rules + Claude Sonnet), generates recommendations (Claude), judges each recommendation, and stores everything in SQLite.

## Key Design Decisions

1. **Tiered classification over LLM-only**: Rule-based patterns handle 60-70% of activities at zero cost. The LLM only processes genuinely ambiguous cases. This keeps the pipeline fast and cheap while maintaining accuracy where it matters.

2. **Pydantic v2 structured output contracts**: Every LLM call uses a Pydantic model as the output schema. This eliminates parsing errors, enforces field constraints (e.g., `evidence_ids` must be non-empty), and makes the API contract between classifier/recommender/judge explicit and testable.

3. **Judge layer with hard-block gates**: Rather than just scoring recommendations, the judge has binary harm/privacy gates that can completely block delivery. A score of 1 on any dimension also triggers a block. This prevents low-quality coaching from reaching the PM lead.

4. **Evidence-mandatory recommendations**: Every coaching recommendation must cite specific activity IDs. This prevents the LLM from generating generic advice and forces recommendations to be grounded in observed behavior.

5. **Static-first frontend**: The Next.js app exports to static HTML/JSON and works on GitHub Pages with zero backend. The client-side chat engine queries JSON data directly. This makes the demo instantly accessible without any infrastructure.

6. **Priority color consistency**: A fixed color map ensures the same priority always appears in the same color across all charts, views, and PMs. This reduces cognitive load when scanning the dashboard -- navy always means Priority 1, teal always means Priority 3.

## License

MIT
