"""Generate realistic mock activities for 3 PMs across 4 weeks.

Jordan Park  — "Meeting Machine" (58% calendar, heavy Insights Agent & MPR via QB BI)
Morgan Lee — "The Executor" (60% Jira, strong Email Report Reimagine & Custom Reports)
Taylor Kim  — "Balanced Operator" (even spread, Tiger Team + HVC + WhatsApp Reporting)
"""

import random
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from backend.storage import db
from backend import config

random.seed(42)  # reproducible

# ── Helpers ────────────────────────────────────────────────────────────────────


def _rand_time(day: datetime, start_h: int = 8, end_h: int = 18) -> datetime:
    h = random.randint(start_h, end_h - 1)
    m = random.choice([0, 15, 30, 45])
    return day.replace(hour=h, minute=m, second=0, microsecond=0)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def _source_id(source: str, title: str, ts: str) -> str:
    return hashlib.md5(f"{source}:{title}:{ts}".encode()).hexdigest()[:12]


def _weekdays(start: datetime, weeks: int = 4) -> list:
    """Return all weekdays for the given number of weeks ending at start."""
    days = []
    d = start - timedelta(weeks=weeks)
    while d <= start:
        if d.weekday() < 5:  # Mon-Fri
            days.append(d)
        d += timedelta(days=1)
    return days


# ── Activity templates per PM ────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────────────────
# JORDAN PARK — Principal PM, Reporting & Analytics
# Heavy calendar (58%): Analytics Agent funnel, MPR via QB BI, Freddie skills
# ──────────────────────────────────────────────────────────────────────────────

JORDAN_CALENDAR = [
    ("Jordan <> Alex 1:1", 30, None, ["alex_chen@company.com"]),
    ("MC Product Review | Scaled AI", 60, "Insights Agent & Scaled AI", ["sam_r@company.com", "chris_n@company.com", "vp_tech@company.com"]),
    ("Weekly OpMech: Marketing Performance Reporting via QB BI Platform", 60, "Marketing Performance Reporting via QB BI", ["dana_g@company.com", "morgan_lee@company.com", "raj_m@company.com"]),
    ("RNA Leads Sync", 45, None, ["alex_chen@company.com", "morgan_lee@company.com", "raj_m@company.com"]),
    ("Enabling AI-powered SMS insights", 45, "Insights Agent & Scaled AI", ["pat_c@company.com", "blake_r@company.com"]),
    ("OBS + Analytics Agent Opportunities", 60, "Insights Agent & Scaled AI", ["chris_n@company.com", "jamie_b@company.com"]),
    ("Confirm Analytics Agent for May 11 GTM", 30, "Insights Agent & Scaled AI", ["sam_r@company.com", "alex_chen@company.com"]),
    ("MC - KPI and Dashboard requirements", 60, "Marketing Performance Reporting via QB BI", ["dana_g@company.com", "morgan_lee@company.com"]),
    ("R&A Weekly Program Review", 60, None, ["alex_chen@company.com", "morgan_lee@company.com", "taylor_kim@company.com", "raj_m@company.com"]),
    ("MC Product Reviews | R&A Report powered by BI Platform", 60, "Marketing Performance Reporting via QB BI", ["morgan_lee@company.com", "raj_m@company.com", "vp_tech@company.com"]),
    ("Analytics Agent — Freddie Skills Alignment", 45, "Insights Agent & Scaled AI", ["dev_k@company.com", "chris_n@company.com"]),
    ("Analytics Agent Beta v2 — Feature Flags Review", 30, "Insights Agent & Scaled AI", ["sam_r@company.com"]),
    ("Omni Integration of Analytics Agent to QBO", 45, "Insights Agent & Scaled AI", ["raj_m@company.com", "dana_g@company.com"]),
    ("S2S Events for Shopify Analytics", 45, "Insights Agent & Scaled AI", ["blake_r@company.com"]),
    ("Analytics Agent Discoverability — Entry Points Review", 30, "Insights Agent & Scaled AI", ["jamie_b@company.com", "sam_r@company.com"]),
    ("Deliverability Agent — CDP Data Sync", 45, "Insights Agent & Scaled AI", ["dev_k@company.com"]),
]

JORDAN_SLACK = [
    ("#mp-insights-agent: Shared updated funnel performance numbers — discoverability to activation is up 12% since entry point changes", "Insights Agent & Scaled AI"),
    ("#mp-insights-agent: Beta v2 feature flag is live for 10% rollout — monitoring repeat engagement over 30d", "Insights Agent & Scaled AI"),
    ("#reporting-analytics-deliverability-agent: Email bounce reasons from CDP are now flowing into StarRocks — SMS bounce data is next", "Insights Agent & Scaled AI"),
    ("#reporting-analytics-deliverability-agent: Blocked on CDP data for SMS bounce categories — need Dev to unblock the pipeline", "Insights Agent & Scaled AI"),
    ("#internal-mpr-via-qb-bi: MPR filter decisions still waiting on Morgan — can we get alignment by EOW?", "Marketing Performance Reporting via QB BI"),
    ("#mp-product-feedback: Email bounce reason enrichment in StarRocks is live — eng confirmed data freshness is <2hr", "Insights Agent & Scaled AI"),
    ("#analytics-pm-team: Q3 launch timeline for Analytics Agent confirmed — May 11 GTM is a go pending test results", "Insights Agent & Scaled AI"),
    ("#analytics-leadership-team: Scale AI funnel dashboard update — 30d repeat engagement is trending up, need to confirm with test cohort", "Insights Agent & Scaled AI"),
    ("#mp-reporting-agent-support: Feature flags for beta v2 are set — need eng to confirm canary rollout plan", "Insights Agent & Scaled AI"),
    ("#mp-insights-agent: Preventing duplicate mc_insights_skill across AI teams — Freddie alignment doc shared in thread", "Insights Agent & Scaled AI"),
]

JORDAN_EMAIL = [
    ("Re: Analytics Agent May 11 GTM — Test Results Status", "Updated Sam and Alex on test cohort results. Repeat engagement metrics look strong enough for GTM go-ahead. Need final sign-off by Friday.", "Insights Agent & Scaled AI"),
    ("Re: MPR via QB BI — KPI Requirements from Dana G.", "Shared analytics KPI requirements doc with Dana G. Dashboard wireframes attached for BI team review.", "Marketing Performance Reporting via QB BI"),
    ("Fwd: Freddie Skills Alignment — mc_insights_skill Dedup", "Forwarded Freddie skills alignment doc to Chris N. and Dev K. We need to prevent duplicate mc_insights_skill registrations across AI teams.", "Insights Agent & Scaled AI"),
    ("Re: AI-powered SMS Insights — Pat C. Sync", "Follow-up from SMS insights meeting with Pat C. CDP data pipeline for SMS bounce categories needs Dev's team to prioritize.", "Insights Agent & Scaled AI"),
    ("Re: R&A Weekly Program Review — Action Items", "Sent action items from program review. Jordan owns Analytics Agent GTM confirmation, Morgan owns MPR filter decisions.", None),
]

JORDAN_DM = [
    ("DM with Alex: FYI - attribution expansion test is still running. Basically flat as expected, rolling it out. Data science good with this.", "Insights Agent & Scaled AI"),
    ("DM with Alex: Analytics Agent integration into QBO Omni — plan and process shared", "Insights Agent & Scaled AI"),
    ("DM with Alex: Skills deduplication research — Omni actually has a process for that", "Insights Agent & Scaled AI"),
    ("DM with Alex: Added analytics agent L2A — at 70% which is pretty good given entry point can be from homepage", "Insights Agent & Scaled AI"),
]

JORDAN_SHARED_DOCS = [
    ("Analytics Agent integration into QBO Omni — Plan & Process", "Shared doc from Jordan: Plan and process for Analytics Agent integration into QBO Omni. docs.company.com/doc/d/1WiyLfve653mC-T5B85xW8fHaWPlA_y24dbopW4HRrnM", "Insights Agent & Scaled AI"),
]

JORDAN_JIRA = [
    ("REPORTING-9901: Analytics Agent — discoverability entry points v2", "Insights Agent & Scaled AI", "Updated entry point spec based on funnel data. Discoverability-to-activation improved 12%."),
    ("REPORTING-9905: Analytics Agent — 30d repeat engagement tracking", "Insights Agent & Scaled AI", "Added repeat engagement metric to Scale AI funnel dashboard. Monitoring test cohort."),
    ("REPORTING-9910: Deliverability Agent — email bounce reason enrichment", "Insights Agent & Scaled AI", "Email bounce reasons from CDP now in StarRocks. SMS bounce data pipeline in progress."),
    ("REPORTING-9915: MPR via QB BI — dashboard filter requirements", "Marketing Performance Reporting via QB BI", "Filter requirements spec complete. Waiting on Morgan for filter decision alignment."),
    ("REPORTING-9920: Analytics Agent — beta v2 feature flag rollout", "Insights Agent & Scaled AI", "Feature flags set for 10% canary. Monitoring metrics before wider rollout."),
    ("REPORTING-9925: Freddie skills alignment — prevent duplicate mc_insights_skill", "Insights Agent & Scaled AI", "Alignment doc shared with AI team leads. Dev reviewing skill registry dedup approach."),
    ("REPORTING-9930: S2S events — Shopify analytics drop-off tracking", "Insights Agent & Scaled AI", "S2S event pipeline spec drafted. Checkout flow drop-off events from Shopify ready for eng review."),
]

# ──────────────────────────────────────────────────────────────────────────────
# MORGAN LEE — Senior Staff PM
# Heavy Jira (60%): Email Report Reimagine, Custom Reports, HVC, Tiger Team VoC
# ──────────────────────────────────────────────────────────────────────────────

MORGAN_JIRA = [
    ("REPORTING-9850: Email Report Reimagine — ecommerce tab canary release", "Email Report Reimagine & Custom Reports", "Ecomm tab canary release blocked by rendering bug. Working with eng on hotfix."),
    ("REPORTING-9855: Comparative to Custom Reports — segment support", "Email Report Reimagine & Custom Reports", "Segment filtering added to Custom Reports. MVT campaign support in progress."),
    ("REPORTING-9860: Marketing Diagnostics PRD — Driver Analysis", "Email Report Reimagine & Custom Reports", "Q4 PRD draft complete. Driver analysis scope defined with Alex."),
    ("REPORTING-9865: Segment Discovery in Custom Reports PRD", "Email Report Reimagine & Custom Reports", "PRD drafted. Segment discovery UX flow reviewed with design."),
    ("REPORTING-9870: HVC export — rounding bug in CSV export", "Email Report Reimagine & Custom Reports", "Rounding bug confirmed in HVC export CSV. Fix spec written, eng assigned."),
    ("REPORTING-9875: Comparative to Custom transition — MVT campaigns", "Email Report Reimagine & Custom Reports", "MVT campaign reports migration spec complete. HVC export bugs blocking full transition."),
    ("REPORTING-9880: Marketing Dashboard — zero state handling", "Email Report Reimagine & Custom Reports", "Zero state designs approved. Eng implementing empty state for new accounts."),
    ("REPORTING-9885: Tiger Team VoC — failure rate tracking", "Email Report Reimagine & Custom Reports", "Updated failure rate tracker in Amplitude. VOC ticket count down 15% from last sprint."),
    ("REPORTING-9890: Product Purchase Predictions PRD", "Email Report Reimagine & Custom Reports", "Q4 PRD in review. Predictive model scope aligned with data science team."),
    ("REPORTING-9895: Actionable Intelligence for DSB PRD", "Email Report Reimagine & Custom Reports", "Draft PRD shared with Alex for review. DSB integration points mapped."),
    ("REPORTING-9898: Data retention policy — reporting impact assessment", "Email Report Reimagine & Custom Reports", "Impact assessment complete. 3 reports affected by new retention window."),
    ("REPORTING-9899: WhatsApp/SMS as R&A channels — POV doc", "Email Report Reimagine & Custom Reports", "Cross-channel analytics POV doc drafted. WhatsApp and SMS reporting scope defined."),
    ("REPORTING-9902: Marketing Platform into BI Platform — 57k joint user analysis", "Marketing Performance Reporting via QB BI", "Analyzed 57k joint QBO/MC users. Plan type distribution data shared with BI team."),
    ("REPORTING-9903: IP Feeds vendor (CHEQ) follow-up", "Email Report Reimagine & Custom Reports", "Follow-up with Ash K. on CHEQ vendor evaluation. Awaiting pricing proposal."),
    ("REPORTING-9904: HVC escalation — DFAD for canary blocking bug", "Email Report Reimagine & Custom Reports", "DFAD filed for canary blocking bug. Customer health impact documented for CSM team."),
]

MORGAN_CALENDAR = [
    ("Alex / Morgan 1:1", 30, None, ["alex_chen@company.com"]),
    ("R&A Weekly Program Review", 60, None, ["alex_chen@company.com", "jordan_park@company.com", "taylor_kim@company.com", "raj_m@company.com"]),
    ("RNA Leads Sync", 45, None, ["alex_chen@company.com", "jordan_park@company.com", "raj_m@company.com"]),
    ("MC Product Reviews | R&A Report powered by BI Platform", 60, "Marketing Performance Reporting via QB BI", ["jordan_park@company.com", "raj_m@company.com", "vp_tech@company.com"]),
    ("Weekly OpMech: Marketing Performance Reporting via QB BI Platform", 60, "Marketing Performance Reporting via QB BI", ["jordan_park@company.com", "dana_g@company.com"]),
    ("R&A: Q4 PRD Review", 60, "Email Report Reimagine & Custom Reports", ["alex_chen@company.com", "taylor_kim@company.com"]),
    ("[Weekly] Top Customer Health: HVC Escalations Review", 45, "Email Report Reimagine & Custom Reports", ["taylor_kim@company.com", "pm_support@company.com"]),
    ("MC - KPI and Dashboard requirements", 60, "Marketing Performance Reporting via QB BI", ["jordan_park@company.com", "dana_g@company.com"]),
]

MORGAN_SLACK = [
    ("#rna-tiger-voc: Failure rates trending down — Amplitude shows 15% improvement since last sprint's fixes", "Email Report Reimagine & Custom Reports"),
    ("#mp-email-report-reimagine: Ecomm tab canary release is blocked — rendering bug needs hotfix before wider rollout", "Email Report Reimagine & Custom Reports"),
    ("#mp-rna-comparative-to-custom-transition: Segment support is live in Custom Reports. MVT campaigns next. HVC export rounding bug (REPORTING-9875) still open.", "Email Report Reimagine & Custom Reports"),
    ("#mp-hvc-escalations: Filed DFAD for canary blocking bug. Customer health ETAs shared with CSM team.", "Email Report Reimagine & Custom Reports"),
    ("#mp-into-bi-platform: 57k joint QBO/MC users analyzed — plan type distribution data ready for BI team review", "Marketing Performance Reporting via QB BI"),
    ("#mp-msg-whatsapp: Wrote POV doc for R&A driving Messaging/WhatsApp — shared in thread for team review", "Email Report Reimagine & Custom Reports"),
    ("#mp-analytics-about-analytics: BigQuery query for user data escalation resolved — sharing fix pattern for future escalations", "Email Report Reimagine & Custom Reports"),
    ("#analytics-pm-team: Q4 PRDs on track — Marketing Diagnostics, Segment Discovery, Product Purchase Predictions, Actionable Intelligence for DSB", "Email Report Reimagine & Custom Reports"),
    ("#mp-voc-kpi: Updated VOC KPI dashboard with latest failure rates and customer sentiment data", "Email Report Reimagine & Custom Reports"),
    ("#internal-mpr-via-qb-bi: MPR filters — need to finalize filter decisions for QBO settings page this week", "Marketing Performance Reporting via QB BI"),
]

MORGAN_DM = [
    ("DM with Alex: I want Taylor to join our review of recent feedback and P0/1 bugs + upcoming releases. Classic backlog management problem stacking up.", "Email Report Reimagine & Custom Reports"),
    ("DM with Alex: Confirmed, shipping Click Performance/Map to canaries by end of this week", "Email Report Reimagine & Custom Reports"),
    ("DM with Alex: Outstanding MRR includes features slipped to April: Ecomm Tab, Exports, Multivariate = $54.6K", "Email Report Reimagine & Custom Reports"),
    ("DM with Alex: Benchmarks, Recipient Activity Export have released - knocking out $21k MRR", "Email Report Reimagine & Custom Reports"),
    ("DM with Alex: Updated pass on Messaging/WhatsApp — upleveled to describe impact beyond mechanics", "Email Report Reimagine & Custom Reports"),
    ("DM with Alex: QBO financial data is not addressed in Q4 work. This is so much bigger than messaging.", "Marketing Performance Reporting via QB BI"),
    ("DM with Alex: I think we have to fix Classic Automations reporting. 100k users, $13 million MRR.", "Email Report Reimagine & Custom Reports"),
]

MORGAN_SHARED_DOCS = [
    ("Actionable Intelligence for DSB — PRD", "Shared doc from Morgan: Actionable Intelligence for DSB PRD. docs.company.com/doc/d/1rYwzJuXsHX8VbO-W2TROnvIVl5dHt_AVVdVZbZViubU", "Email Report Reimagine & Custom Reports"),
    ("Product & Discount prompts — Spreadsheet", "Shared doc from Morgan: Product & Discount prompts analysis. docs.company.com/sheet/d/1w6cqW7ziLXAbJ0Pcu-xkefFsb7mhE4NRD_mfas48Hb8", "Email Report Reimagine & Custom Reports"),
    ("57k joint QBO/MC users — Data Analysis", "Shared doc from Morgan: 57k joint QBO/MC users data analysis. docs.company.com/sheet/d/1Scm0AIHYCoKHP35aAVxb6EAQHFjKXOCKRK0WKkc1Vko", "Marketing Performance Reporting via QB BI"),
    ("Canaries release list — Spreadsheet", "Shared doc from Morgan: Canaries release tracking list. docs.company.com/sheet/d/1XczHF1HTjT6GNKhrWjTS7acZS1YPj9ludhshVdL5I5Y", "Email Report Reimagine & Custom Reports"),
    ("Email Domain Performance timing — Doc", "Shared doc from Morgan: Email Domain Performance timing analysis. docs.company.com/doc/d/1L5W8uX-g4yc7ixfjH6S_s5Efii_BIhW7df3E1FzBXro", "Email Report Reimagine & Custom Reports"),
    ("Messaging/WhatsApp — Impact beyond mechanics", "Shared doc from Morgan: Updated pass on Messaging/WhatsApp upleveled to describe impact beyond mechanics. docs.company.com/doc/d/1_0k21vQfh0lmzLGs8UL4FNpLcGO_EPF8X-Gf1FR76Yo", "Email Report Reimagine & Custom Reports"),
]

MORGAN_EMAIL = [
    ("Re: Q4 PRD Review — Marketing Diagnostics & Segment Discovery", "Sent updated PRD drafts to Alex. Marketing Diagnostics driver analysis scope finalized. Segment Discovery UX reviewed with design.", "Email Report Reimagine & Custom Reports"),
    ("Re: HVC Escalation — Canary Blocking Bug DFAD", "Updated CSM team on DFAD status for canary blocking bug. Customer health impact documented. ETA for fix: end of sprint.", "Email Report Reimagine & Custom Reports"),
    ("Re: Marketing Platform into BI Platform — Joint User Analysis", "Shared 57k joint QBO/MC user analysis with BI team. Plan type distribution shows 72% on Standard+ plans.", "Marketing Performance Reporting via QB BI"),
    ("Fwd: IP Feeds Vendor (CHEQ) — Pricing Follow-up", "Forwarded CHEQ pricing proposal to Ash K. for review. Need decision by next week.", "Email Report Reimagine & Custom Reports"),
    ("Re: Alex / Morgan 1:1 — Fine Toothed Comb on Upcoming Releases", "Prep notes for 1:1: review recent VOC/HOP tickets, data retention policy impact, upcoming canary releases.", None),
]

# ──────────────────────────────────────────────────────────────────────────────
# TAYLOR KIM — PM 2
# Balanced (30% calendar, 25% Slack, 15% email, 30% Jira)
# Tiger Team, HVC close-the-loop, WhatsApp Reporting, VoC
# ──────────────────────────────────────────────────────────────────────────────

TAYLOR_CALENDAR = [
    ("R&A Weekly Program Review", 60, None, ["alex_chen@company.com", "jordan_park@company.com", "morgan_lee@company.com", "raj_m@company.com"]),
    ("R&A: Q4 PRD Review", 60, "Email Report Reimagine & Custom Reports", ["alex_chen@company.com", "morgan_lee@company.com"]),
    ("[Weekly] Top Customer Health: HVC Escalations Review", 45, "Email Report Reimagine & Custom Reports", ["morgan_lee@company.com", "pm_support@company.com"]),
    ("WhatsApp Reporting — Funnel Alignment with Eng S.", 45, "Email Report Reimagine & Custom Reports", ["eng_s@company.com", "eng_d@company.com"]),
    ("Tiger Team — Click Performance Canary Status", 30, "Email Report Reimagine & Custom Reports", ["ash_k@company.com", "eng_lead_m@company.com"]),
    ("HVC Close-the-Loop — CSM Sync", 30, "Email Report Reimagine & Custom Reports", ["customer_a@company.com", "customer_b@company.com", "customer_c@company.com"]),
    ("VoC Collection — Export Feature Customer Outreach", 45, "Email Report Reimagine & Custom Reports", ["cs_lead_r@company.com", "design_n@company.com"]),
    ("Tiger Team — Data Consistency Review for Zero States", 30, "Email Report Reimagine & Custom Reports", ["eng_c@company.com", "eng_e@company.com"]),
    ("Email Report Reimagine — Tooltip Copy Review", 30, "Email Report Reimagine & Custom Reports", ["morgan_lee@company.com"]),
    ("Export & Recipient Activity Working Session", 45, "Email Report Reimagine & Custom Reports", ["ash_k@company.com", "eng_f@company.com"]),
    ("QA Timeline Review — Push for Earlier Release", 30, "Email Report Reimagine & Custom Reports", ["eng_lead_m@company.com"]),
]

TAYLOR_SLACK = [
    ("#rna-tiger-voc: Click Performance canary release rows 1-31 look clean — no rollback needed. Click Map canary next.", "Email Report Reimagine & Custom Reports"),
    ("#rna-tiger-voc: Found data consistency issue in zero state handling — flagging for eng before wider rollout", "Email Report Reimagine & Custom Reports"),
    ("#mp-hvc-escalations: Close-the-loop update sent to Customer A and Customer B. Jira tickets REPORTING-9916 and REPORTING-9940 updated.", "Email Report Reimagine & Custom Reports"),
    ("#mp-hvc-escalations-program-top-customer-health: Canary release status — bug fixes verified, proceeding with rollout", "Email Report Reimagine & Custom Reports"),
    ("#mp-rna-whatsapp-reporting: Delivered->Read->Clicked funnel spec aligned with Eng S. and Eng D. Ready for eng review.", "Email Report Reimagine & Custom Reports"),
    ("#mp-reporting-analytics-feedback: Collecting customers who submitted VOCs for export feature — building email list for close-the-loop outreach", "Email Report Reimagine & Custom Reports"),
    ("#mp-email-report-reimagine: Covering for Morgan (OOO) — ecomm tab tooltip copy updated, shared in thread for review", "Email Report Reimagine & Custom Reports"),
    ("#mp-analytics-support-bridge: Closing loop on Click Performance fix — confirmed with eng, updating CSM team", "Email Report Reimagine & Custom Reports"),
    ("#analytics-pm-team: Pushed back on 13-day QA timeline — proposed 8-day plan with parallel tracks. Need Eng Lead M.'s sign-off.", "Email Report Reimagine & Custom Reports"),
    ("#tmp-insights-agent-reports: Follow-up on count vs rate display — recommending rate as default with count toggle", "Insights Agent & Scaled AI"),
    ("#analytics-leadership-team: Tooltip copy discussion — aligned on concise format for ecomm tab metrics", "Email Report Reimagine & Custom Reports"),
    ("#hvc_feedback: Customer feedback compiled from 12 HVC accounts — top themes: export reliability, data freshness", "Email Report Reimagine & Custom Reports"),
]

TAYLOR_DM = [
    ("DM with Alex: I have such a good handle of tiger team and WhatsApp work now, very happy with how it's going", "Email Report Reimagine & Custom Reports"),
    ("DM with Alex: Things have been so so much better ever since you got me into shape", None),
]

TAYLOR_EMAIL = [
    ("Re: HVC Close-the-Loop — Customer Outreach Templates", "Sent email templates to Customer A and Customer C for close-the-loop outreach. Jira tickets updated with CSM follow-up status.", "Email Report Reimagine & Custom Reports"),
    ("Re: Tiger Team — Click Performance Canary Results", "Shared canary release results for rows 1-31. No rollback needed. Click Map canary scheduled for next week.", "Email Report Reimagine & Custom Reports"),
    ("Re: WhatsApp Reporting — Funnel Metrics Alignment", "Follow-up with Eng S. on Delivered->Read->Clicked funnel spec. Eng review scheduled for Thursday.", "Email Report Reimagine & Custom Reports"),
    ("Fwd: QA Timeline — Proposed 8-Day Plan", "Forwarded compressed QA plan to Eng Lead M. Pushed back on 13-day timeline with parallel testing approach.", "Email Report Reimagine & Custom Reports"),
    ("Re: VoC Collection — Export Feature Customers", "Compiled list of customers who submitted VOCs about export feature. Spot-checked 5 campaigns for bots/MPP impact.", "Email Report Reimagine & Custom Reports"),
    ("Re: Export & Recipient Activity — Working Session Notes", "Shared session notes with Ash K. and Scott. Export spec updated with recipient activity requirements.", "Email Report Reimagine & Custom Reports"),
]

TAYLOR_JIRA = [
    ("REPORTING-9916: HVC escalation — Click Performance data mismatch", "Email Report Reimagine & Custom Reports", "Close-the-loop with CSM Customer A. Data mismatch root cause identified, fix in canary."),
    ("REPORTING-9940: HVC escalation — export CSV rounding in Click Map", "Email Report Reimagine & Custom Reports", "Updated CSM Customer B on fix ETA. Rounding bug fix in next sprint."),
    ("REPORTING-9945: Tiger Team — Click Performance canary release (rows 1-31)", "Email Report Reimagine & Custom Reports", "Canary release clean. No rollback. Proceeding to Click Map canary."),
    ("REPORTING-9950: Tiger Team — Click Map canary release prep", "Email Report Reimagine & Custom Reports", "QA checklist prepared. Data consistency for zero states verified."),
    ("REPORTING-9955: WhatsApp Reporting — Delivered->Read->Clicked funnel", "Email Report Reimagine & Custom Reports", "Funnel spec aligned with Eng S. Eng review ready."),
    ("REPORTING-9960: VoC — export feature customer outreach list", "Email Report Reimagine & Custom Reports", "Customer list compiled from VOC submissions. 47 customers identified for outreach."),
    ("REPORTING-9965: Email Report Reimagine — ecomm tab tooltip copy", "Email Report Reimagine & Custom Reports", "Tooltip copy finalized. Covering for Morgan while OOO."),
    ("REPORTING-9970: QA timeline optimization — parallel testing plan", "Email Report Reimagine & Custom Reports", "Proposed 8-day QA plan vs original 13-day. Waiting on Eng Lead M. approval."),
    ("REPORTING-9975: Export & recipient activity spec update", "Email Report Reimagine & Custom Reports", "Spec updated with Ash K. and Eng F.'s requirements. Ready for eng."),
    ("REPORTING-9980: Customer spot-check — bots/MPP impact on campaigns", "Email Report Reimagine & Custom Reports", "Spot-checked 5 campaigns. 2 showed bot traffic >15%. Escalating to data quality."),
]


# ── Generator ────────────────────────────────────────────────────────────────


def _gen_activities(pm_id: str, days: list,
                    calendar_tpls: list, slack_tpls: list,
                    email_tpls: list, jira_tpls: list,
                    calendar_pct: float, slack_pct: float,
                    email_pct: float, jira_pct: float,
                    target_per_week: int = 38,
                    dm_tpls: Optional[list] = None,
                    shared_doc_tpls: Optional[list] = None) -> list:
    """Generate activities by sampling from templates across the given days."""
    activities = []
    target_total = target_per_week * 4  # 4 weeks

    cal_count = int(target_total * calendar_pct)
    slack_count = int(target_total * slack_pct)
    email_count = int(target_total * email_pct)
    jira_count = target_total - cal_count - slack_count - email_count

    # Calendar events
    for i in range(cal_count):
        day = random.choice(days)
        tpl = calendar_tpls[i % len(calendar_tpls)]
        title, dur, priority_hint, participants = tpl
        ts = _rand_time(day, 8, 17)
        activities.append({
            "pm_id": pm_id,
            "source": "calendar",
            "source_id": _source_id("calendar", title, _iso(ts)),
            "title": title,
            "summary": f"Meeting: {title} ({dur} min) with {len(participants)} participants.",
            "duration_minutes": dur,
            "participants": participants,
            "occurred_at": _iso(ts),
            "_priority_hint": priority_hint,
        })

    # Slack messages
    for i in range(slack_count):
        day = random.choice(days)
        msg, priority_hint = slack_tpls[i % len(slack_tpls)]
        ts = _rand_time(day, 9, 18)
        activities.append({
            "pm_id": pm_id,
            "source": "slack",
            "source_id": _source_id("slack", msg[:30], _iso(ts)),
            "title": msg.split(":")[0] if ":" in msg else msg[:60],
            "summary": msg,
            "occurred_at": _iso(ts),
            "_priority_hint": priority_hint,
        })

    # DM messages (source=slack, title prefixed with "DM with Alex:")
    if dm_tpls:
        for i, (msg, priority_hint) in enumerate(dm_tpls):
            day = random.choice(days)
            ts = _rand_time(day, 9, 18)
            activities.append({
                "pm_id": pm_id,
                "source": "slack",
                "source_id": _source_id("slack-dm", msg[:30], _iso(ts)),
                "title": msg.split(":")[0] + ":" if ":" in msg else msg[:60],
                "summary": msg,
                "occurred_at": _iso(ts),
                "_priority_hint": priority_hint,
            })

    # Emails
    for i in range(email_count):
        day = random.choice(days)
        subject, body, priority_hint = email_tpls[i % len(email_tpls)]
        ts = _rand_time(day, 8, 19)
        activities.append({
            "pm_id": pm_id,
            "source": "email",
            "source_id": _source_id("email", subject, _iso(ts)),
            "title": subject,
            "summary": body,
            "occurred_at": _iso(ts),
            "_priority_hint": priority_hint,
        })

    # Shared docs (source=email, with doc title and URL in summary)
    if shared_doc_tpls:
        for i, (doc_title, doc_summary, priority_hint) in enumerate(shared_doc_tpls):
            day = random.choice(days)
            ts = _rand_time(day, 8, 19)
            activities.append({
                "pm_id": pm_id,
                "source": "email",
                "source_id": _source_id("shared-doc", doc_title[:30], _iso(ts)),
                "title": doc_title,
                "summary": doc_summary,
                "occurred_at": _iso(ts),
                "_priority_hint": priority_hint,
            })

    # Jira tickets
    for i in range(jira_count):
        day = random.choice(days)
        ticket_title, priority_hint, comment = jira_tpls[i % len(jira_tpls)]
        ts = _rand_time(day, 9, 17)
        activities.append({
            "pm_id": pm_id,
            "source": "jira",
            "source_id": _source_id("jira", ticket_title, _iso(ts)),
            "title": ticket_title,
            "summary": comment,
            "occurred_at": _iso(ts),
            "_priority_hint": priority_hint,
        })

    return activities


def seed_all():
    """Seed the database with team members, priorities, and ~600 activities."""
    # Reset and init
    db.reset_db()

    # Team members
    for m in [config.TEAM_LEAD] + config.TEAM_MEMBERS:
        db.upsert_team_member(m["id"], m["name"], m["email"], m["role"])

    # Priorities
    for p in config.DEFAULT_PRIORITIES:
        db.insert_priority(p["name"], p["description"], p["weight"])

    # Generate activity days (4 weeks ending today)
    today = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    days = _weekdays(today, weeks=4)

    # Jordan — Meeting Machine: 58% calendar
    jordan_acts = _gen_activities(
        "jordan-park", days,
        JORDAN_CALENDAR, JORDAN_SLACK, JORDAN_EMAIL, JORDAN_JIRA,
        calendar_pct=0.58, slack_pct=0.20, email_pct=0.08, jira_pct=0.14,
        target_per_week=40,
        dm_tpls=JORDAN_DM,
        shared_doc_tpls=JORDAN_SHARED_DOCS,
    )

    # Morgan — The Executor: 60% Jira
    morgan_acts = _gen_activities(
        "morgan-lee", days,
        MORGAN_CALENDAR, MORGAN_SLACK, MORGAN_EMAIL, MORGAN_JIRA,
        calendar_pct=0.15, slack_pct=0.18, email_pct=0.07, jira_pct=0.60,
        target_per_week=38,
        dm_tpls=MORGAN_DM,
        shared_doc_tpls=MORGAN_SHARED_DOCS,
    )

    # Taylor — Balanced Operator
    taylor_acts = _gen_activities(
        "taylor-kim", days,
        TAYLOR_CALENDAR, TAYLOR_SLACK, TAYLOR_EMAIL, TAYLOR_JIRA,
        calendar_pct=0.30, slack_pct=0.25, email_pct=0.15, jira_pct=0.30,
        target_per_week=36,
        dm_tpls=TAYLOR_DM,
    )

    all_acts = jordan_acts + morgan_acts + taylor_acts

    # Strip internal _priority_hint before DB insert (used by classifier seed)
    hints = {}
    clean_acts = []
    for a in all_acts:
        hint = a.pop("_priority_hint", None)
        clean_acts.append(a)

    count = db.insert_activities_bulk(clean_acts)

    # Pre-seed classifications using the priority hints (so dashboard works immediately)
    priorities = db.get_priorities()
    priority_map = {p["name"]: p["id"] for p in priorities}

    all_db_activities = db.get_activities(limit=2000)
    classifications = []
    for act in all_db_activities:
        # Find matching seed activity to get priority hint
        matching = [a for a in all_acts if a.get("source_id") == act["source_id"]]
        if not matching:
            continue
        orig = matching[0]
        hint = None
        # Re-derive hint from the original templates
        for a_orig in jordan_acts + morgan_acts + taylor_acts:
            if a_orig.get("source_id") == act["source_id"]:
                break

        # Use rule-based classification for seed data
        import re
        title = act["title"] or ""
        summary = act["summary"] or ""
        text = f"{title} {summary}"

        # Determine priority from content
        priority_name = "Other"
        if re.search(r"(?i)(insights.agent|analytics.agent|deliverability.agent|scaled.ai|freddie|mc_insights_skill|SMS.insight|funnel.performance|discoverability|GTM|bounce.reason|CDP|StarRocks|agent.support|repeat.engagement|entry.point|feature.flag|beta.v2|S2S.event|shopify.analytics|OBS.*agent|omni.*analytics.agent)", text):
            priority_name = "Insights Agent & Scaled AI"
        elif re.search(r"(?i)(email.report|custom.report|comparative|segment.discovery|diagnostics|driver.analysis|tiger|voc|hvc|escalation|canary|click.performance|click.map|whatsapp.report|export|recipient.activity|ecomm|tooltip|DFAD|data.consistency|multivariate|MVT|zero.state|marketing.dashboard|CHEQ|IP.feeds|data.retention|POV.doc|purchase.prediction|actionable.intelligence|DSB|close.the.loop|QA.timeline|bots.*MPP|REPORTING-98|REPORTING-99[0-7])", text):
            priority_name = "Email Report Reimagine & Custom Reports"
        elif re.search(r"(?i)(MPR|BI.platform|QB.BI|marketing.performance|QBO.*plan|joint.*user|KPI.*dashboard|dashboard.requirement|mp.into.bi|57k|plan.type.distribution|dana.g|REPORTING-99(?:02|15))", text):
            priority_name = "Marketing Performance Reporting via QB BI"

        # Determine type
        activity_type = "Execution"
        if act["source"] == "calendar":
            if re.search(r"(?i)(1[:\-]1|<>|stakeholder|exec|skip)", title):
                activity_type = "Stakeholder"
            elif re.search(r"(?i)(standup|retro|team.sync|all.hands|weekly.team|program.review|leads.sync)", title):
                activity_type = "InternalOps"
            elif re.search(r"(?i)(strategy|vision|OKR|roadmap|PRD.review|Q4.PRD)", title):
                activity_type = "Strategy"
            elif re.search(r"(?i)(interview|research|usability|discovery|VoC|voice.of.customer|NPS|detractor|customer.outreach)", title):
                activity_type = "Discovery"
            elif re.search(r"(?i)(product.review|MC.Product|sprint|design.review|backlog|grooming|feature.flag|canary|tooltip|QA.timeline|working.session)", title):
                activity_type = "Execution"
            elif re.search(r"(?i)(incident|escalation|firefight|post.mortem|tiger.team.*incident|HVC.*escalation)", title):
                activity_type = "Reactive"
            elif re.search(r"(?i)(HVC|bug.status|bug.review|close.the.loop)", title):
                activity_type = "Reactive"
            else:
                activity_type = "Stakeholder"
        elif act["source"] == "jira":
            activity_type = "Execution"
        elif act["source"] == "slack":
            if re.search(r"(?i)(blocked|escalat|incident|rollback)", text):
                activity_type = "Reactive"
            else:
                activity_type = "Execution"
        elif act["source"] == "email":
            if re.search(r"(?i)(strategy|vision|positioning|PRD|roadmap)", text):
                activity_type = "Strategy"
            else:
                activity_type = "Stakeholder"

        # Leverage
        leverage = "Medium"
        if re.search(r"(?i)(shipped|completed|done|approved|merged|closed|live|confirmed|finalized|clean|aligned|resolved)", text):
            leverage = "High"
        elif re.search(r"(?i)(blocked|waiting|pending|review|need.*sign.off|need.*decision)", text):
            leverage = "Low"

        confidence = round(random.uniform(0.75, 0.95), 2)

        classifications.append({
            "activity_id": act["id"],
            "priority_id": priority_map.get(priority_name),
            "priority_name": priority_name,
            "activity_type": activity_type,
            "leverage": leverage,
            "confidence": confidence,
            "reasoning": f"Classified as {activity_type}/{priority_name} based on content signals.",
        })

    class_count = db.insert_classifications_bulk(classifications)

    # Pre-seed recommendations for the most recent week
    from datetime import date
    today_date = date.today()
    # Get ISO week
    week_iso = today_date.strftime("%G-W%V")

    _seed_recommendations(week_iso)

    return {
        "team_members": len(config.TEAM_MEMBERS) + 1,
        "priorities": len(config.DEFAULT_PRIORITIES),
        "activities": count,
        "classifications": class_count,
        "week_iso": week_iso,
    }


def _seed_recommendations(week_iso: str):
    """Pre-seed coaching recommendations for each PM."""
    recs = [
        # ── Jordan Park ────────────────────────────────────────────────────
        {
            "week_iso": week_iso, "pm_id": "jordan-park", "pm_name": "Jordan Park",
            "kind": "Accelerate",
            "action": "The Analytics Agent May 11 GTM is the highest-leverage milestone this quarter. Repeat engagement metrics from the beta v2 10% rollout look strong. Block time this week to finalize the GTM go/no-go decision with Sam R. and lock the release plan. The Freddie skills alignment with Dev is a dependency -- confirm mc_insights_skill dedup is resolved before wider rollout.",
            "rationale": "Jordan's funnel data shows discoverability-to-activation up 12% and 30d repeat engagement trending positive. The beta v2 feature flags are live. The remaining blockers are organizational (Freddie skills dedup, GTM sign-off) not technical. Closing these this week de-risks the May 11 launch.",
            "evidence_ids": [1, 5, 9, 13],
            "judge_score": 4.6, "judge_reasoning": "Strong momentum with clear data. GTM confirmation is time-sensitive and well-evidenced.",
            "status": "published",
        },
        {
            "week_iso": week_iso, "pm_id": "jordan-park", "pm_name": "Jordan Park",
            "kind": "Cut",
            "action": "You attended 23 meetings this week including overlapping syncs on MPR via QB BI (Weekly OpMech, KPI Requirements, BI Platform Product Review). Consolidate the MPR filter discussion into the Weekly OpMech and cancel the standalone KPI meeting until Morgan provides the filter decisions. You're blocked on her anyway -- reclaim 2 hours for the Analytics Agent GTM prep.",
            "rationale": "Jordan has 3 separate recurring meetings touching MPR via QB BI, but the core blocker is Morgan's filter decision which hasn't landed yet. Running parallel MPR meetings without that input produces redundant discussion. The Weekly OpMech with Dana G. is sufficient to maintain BI team alignment.",
            "evidence_ids": [2, 8, 12, 15],
            "judge_score": 4.2, "judge_reasoning": "Clear meeting overlap identified. Practical consolidation with named dependency.",
            "status": "published",
        },
        {
            "week_iso": week_iso, "pm_id": "jordan-park", "pm_name": "Jordan Park",
            "kind": "Redirect",
            "action": "The Deliverability Agent work (email bounce reasons in StarRocks, SMS bounce from CDP) is important but currently blocked on Dev's pipeline team. Instead of waiting, redirect that time toward the S2S events for Shopify analytics spec -- Blake R. is ready to review and this work feeds the Analytics Agent's checkout-flow-drop-off insights for May 11 GTM.",
            "rationale": "SMS bounce data from CDP is a dependency on Dev's team and Jordan can't unblock it alone. Meanwhile, the S2S Shopify events spec is fully in Jordan's control and directly strengthens the Analytics Agent's value proposition for GTM. Better to ship what you can control.",
            "evidence_ids": [4, 11, 14],
            "judge_score": 4.3, "judge_reasoning": "Smart reallocation from blocked work to unblocked high-value work. Both feed the same priority.",
            "status": "published",
        },
        # ── Morgan Lee ──────────────────────────────────────────────────
        {
            "week_iso": week_iso, "pm_id": "morgan-lee", "pm_name": "Morgan Lee",
            "kind": "Accelerate",
            "action": "The Q4 PRD pipeline is your highest-leverage output right now -- Marketing Diagnostics (Driver Analysis), Segment Discovery, Product Purchase Predictions, and Actionable Intelligence for DSB are all in draft. Get the Marketing Diagnostics PRD through Alex review this week. It's the most mature and unblocks eng scoping for Q4 sprint 1. The other three can sequence behind it.",
            "rationale": "Morgan has 4 PRDs in varying stages of completion. Marketing Diagnostics (REPORTING-9860) is closest to done and has the clearest scope. Shipping one strong PRD through review builds credibility and creates a template for the remaining three. Trying to advance all four simultaneously fragments her deep-work time.",
            "evidence_ids": [30, 33, 36],
            "judge_score": 4.5, "judge_reasoning": "Clear prioritization of PRD pipeline. Specific deliverable with named reviewer.",
            "status": "published",
        },
        {
            "week_iso": week_iso, "pm_id": "morgan-lee", "pm_name": "Morgan Lee",
            "kind": "Cut",
            "action": "The Email Report Reimagine ecomm tab canary is blocked by a rendering bug -- Taylor is already covering the tooltip copy and canary monitoring while you focus on PRDs. Let Taylor continue owning the canary release execution and limit your involvement to the go/no-go decision. The CHEQ vendor follow-up with Ash K. can also wait until the pricing proposal arrives -- don't spend cycles chasing it.",
            "rationale": "Morgan is spread across 15 Jira tickets this week spanning PRDs, canary releases, HVC escalations, and vendor evaluations. Taylor has already demonstrated she can cover the ecomm tab work effectively. Morgan's unique leverage is on the PRDs and the comparative-to-custom transition architecture -- not on canary monitoring.",
            "evidence_ids": [31, 35],
            "judge_score": 4.0, "judge_reasoning": "Good delegation identification. Taylor is already covering this work.",
            "status": "published",
        },
        {
            "week_iso": week_iso, "pm_id": "morgan-lee", "pm_name": "Morgan Lee",
            "kind": "Redirect",
            "action": "Your WhatsApp/SMS POV doc for R&A driving cross-channel analytics is strategic but sitting in a Slack thread. Package it as a one-page brief and bring it to the next RNA Leads Sync with Alex and Jordan. This positions R&A as the cross-channel analytics owner before another team claims it. The 57k joint QBO/MC user analysis also deserves a stakeholder-visible format -- combine both into a 'R&A Cross-Channel Vision' brief.",
            "rationale": "Morgan wrote a POV doc for R&A driving Messaging/WhatsApp and completed the 57k joint user analysis, but both are buried in Slack threads. These are strategic assets that could shape R&A's Q4 charter. Elevating them to leadership visibility converts execution work into strategic influence.",
            "evidence_ids": [29, 34, 38],
            "judge_score": 4.4, "judge_reasoning": "Strong insight -- buried strategic work needs visibility. Specific output format and forum.",
            "status": "published",
        },
        # ── Taylor Kim ───────────────────────────────────────────────────
        {
            "week_iso": week_iso, "pm_id": "taylor-kim", "pm_name": "Taylor Kim",
            "kind": "Accelerate",
            "action": "The Click Performance canary (rows 1-31) is clean and Click Map canary is next. You've built strong momentum on the Tiger Team releases -- push to get Click Map canary live by end of week. The data consistency checks for zero states are done and QA prep is ready. Don't let the 13-day QA timeline proposal slow you down -- your 8-day parallel plan is sound, get Eng Lead M.'s sign-off.",
            "rationale": "Taylor's Tiger Team work is the most visible deliverable for the Email Report Reimagine priority. Click Performance canary succeeded without rollback, demonstrating solid QA and bug-catching. The Click Map canary is the logical next step and all prerequisites are met. The QA timeline pushback shows good judgment on velocity.",
            "evidence_ids": [50, 55, 60],
            "judge_score": 4.5, "judge_reasoning": "Clear momentum on high-visibility work. Specific timeline and named approver.",
            "status": "published",
        },
        {
            "week_iso": week_iso, "pm_id": "taylor-kim", "pm_name": "Taylor Kim",
            "kind": "Cut",
            "action": "The HVC close-the-loop outreach with CSMs (Customer A, Customer B, Customer C) is consuming significant time with email templates and Jira updates. Batch the outreach to once per week and create a shared template that CSMs can self-serve. The per-customer Jira update cadence can shift to a weekly summary in #mp-hvc-escalations instead of individual ticket updates.",
            "rationale": "Taylor is manually closing the loop on individual HVC tickets with per-customer emails. This is important relationship work but the current approach doesn't scale. A templatized weekly batch with a shared Slack summary maintains the CSM relationship while reclaiming 3-4 hours per week for higher-leverage Tiger Team and WhatsApp reporting work.",
            "evidence_ids": [53, 58],
            "judge_score": 3.9, "judge_reasoning": "Good efficiency suggestion. Templatization is practical and maintains relationship quality.",
            "status": "published",
        },
        {
            "week_iso": week_iso, "pm_id": "taylor-kim", "pm_name": "Taylor Kim",
            "kind": "Redirect",
            "action": "Your WhatsApp Reporting funnel spec (Delivered->Read->Clicked) is aligned with Eng S. and ready for eng review. But the insights-agent-reports count-vs-rate display question you raised in #tmp-insights-agent-reports is an opportunity to influence the Analytics Agent's reporting UX before May 11 GTM. Coordinate with Jordan to get your rate-as-default recommendation into the beta v2 spec this week.",
            "rationale": "Taylor raised a UX question about count vs rate display that directly affects the Analytics Agent's reporting experience. Jordan owns the GTM but this cross-team input strengthens the product. Getting this resolved before the May 11 launch avoids a post-launch UX iteration cycle.",
            "evidence_ids": [52, 57, 61],
            "judge_score": 4.1, "judge_reasoning": "Good cross-team leverage. Specific timing window (before May 11 GTM) adds urgency.",
            "status": "published",
        },
    ]

    for r in recs:
        db.insert_recommendation(**r)


if __name__ == "__main__":
    result = seed_all()
    print(f"Seeded: {result}")
