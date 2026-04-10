/**
 * Client-side chat engine — answers questions by querying static JSON data.
 * No backend needed. Works on GitHub Pages.
 */

import { getDashboard, getDecisions, getPMActivities, getPMSummary, Activity, PMSummary, DashboardData, DecisionsData } from "./api";

let dashCache: DashboardData | null = null;
let pmCache: Record<string, { summary: PMSummary; activities: Activity[] }> = {};
let decisionsCache: DecisionsData | null = null;

async function loadData() {
  if (!dashCache) {
    dashCache = await getDashboard();
    for (const pm of dashCache.pm_summaries) {
      const acts = await getPMActivities(pm.pm_id);
      pmCache[pm.pm_id] = { summary: pm, activities: acts };
    }
  }
  if (!decisionsCache) {
    try { decisionsCache = await getDecisions(); } catch {}
  }
}

function detectPM(msg: string): string | null {
  const m = msg.toLowerCase();
  if (m.includes("jordan")) return "jordan-park";
  if (m.includes("morgan") || m.includes("nj")) return "morgan-lee";
  if (m.includes("taylor")) return "taylor-kim";
  return null;
}

function detectPriority(msg: string): string | null {
  const m = msg.toLowerCase();
  if (m.includes("insights agent") || m.includes("scaled ai") || m.includes("analytics agent") || m.includes("deliverability")) return "Insights Agent & Scaled AI";
  if (m.includes("email report") || m.includes("custom report") || m.includes("reimagine") || m.includes("hvc") || m.includes("tiger") || m.includes("voc")) return "Email Report Reimagine & Custom Reports";
  if (m.includes("mpr") || m.includes("bi platform") || m.includes("qbo") || m.includes("marketing performance")) return "Marketing Performance Reporting via QB BI";
  return null;
}

function fmtHours(min: number): string {
  return `${(min / 60).toFixed(1)} hours`;
}

export async function answerQuestion(message: string): Promise<string> {
  await loadData();
  if (!dashCache) return "Unable to load data.";

  const msg = message.toLowerCase();
  const pmId = detectPM(message);
  const priority = detectPriority(message);

  // --- Time on a priority ---
  if (pmId && priority && (msg.includes("time") || msg.includes("spend") || msg.includes("hours") || msg.includes("how much"))) {
    const acts = pmCache[pmId]?.activities || [];
    const matched = acts.filter((a) => a.priority_name === priority);
    const totalMin = matched.reduce((s, a) => s + (a.duration_minutes || 10), 0);
    const pmName = pmCache[pmId]?.summary.pm_name || pmId;
    if (matched.length === 0) return `No activities found for **${pmName}** on **${priority}**.`;
    return `Based on the activity ledger, **${pmName}** spent approximately **${fmtHours(totalMin)}** across **${matched.length} activities** on **${priority}**.\n\nThis includes meetings, Jira tickets, Slack messages, and emails related to this priority.`;
  }

  // --- Meeting hours comparison ---
  if (msg.includes("meeting") && (msg.includes("compare") || msg.includes("across") || msg.includes("all"))) {
    const lines = ["Here's the **meeting hours comparison** across all PMs:\n"];
    const sorted = [...dashCache.pm_summaries].sort((a, b) => b.meeting_hours - a.meeting_hours);
    for (const pm of sorted) {
      lines.push(`• **${pm.pm_name}**: ${pm.meeting_hours.toFixed(1)} hours (${pm.meetings} meetings)`);
    }
    lines.push(`\n${sorted[0].pm_name} has the highest meeting load — worth checking if some can be delegated or made async.`);
    return lines.join("\n");
  }

  // --- Lowest priority alignment ---
  if (msg.includes("lowest") && (msg.includes("alignment") || msg.includes("priority"))) {
    const sorted = [...dashCache.pm_summaries].sort((a, b) => a.alignment_pct - b.alignment_pct);
    const pm = sorted[0];
    return `**${pm.pm_name}** has the lowest priority alignment at **${pm.alignment_pct}%**.\n\nThis means ${(100 - pm.alignment_pct).toFixed(1)}% of their time is going to work outside the team's top 3 stated priorities.`;
  }

  // --- Time sinks / breakdown by type ---
  if (pmId && (msg.includes("time sink") || msg.includes("biggest") || msg.includes("type"))) {
    const pm = pmCache[pmId]?.summary;
    if (!pm) return "PM not found.";
    const types = Object.entries(pm.type_breakdown).sort((a, b) => b[1] - a[1]);
    const lines = [`Here's **${pm.pm_name}'s** activity breakdown by type:\n`];
    for (const [t, count] of types) {
      lines.push(`• **${t}**: ${count} activities`);
    }
    lines.push(`\nThe biggest time investment is in **${types[0][0]}** at ${types[0][1]} activities.`);
    return lines.join("\n");
  }

  // --- Source breakdown ---
  if (pmId && (msg.includes("source") || msg.includes("breakdown") || msg.includes("activity"))) {
    const pm = pmCache[pmId]?.summary;
    if (!pm) return "PM not found.";
    const sources = Object.entries(pm.source_breakdown).sort((a, b) => b[1] - a[1]);
    const lines = [`Here's **${pm.pm_name}'s** activity breakdown by source:\n`];
    for (const [s, count] of sources) {
      lines.push(`• **${s.charAt(0).toUpperCase() + s.slice(1)}**: ${count} activities`);
    }
    return lines.join("\n");
  }

  // --- Team balance on a priority ---
  if (priority && (msg.includes("balance") || msg.includes("coverage") || msg.includes("team"))) {
    const lines = [`Here's the team's coverage of **${priority}**:\n`];
    for (const pm of dashCache.pm_summaries) {
      const pct = pm.priority_breakdown[priority] || 0;
      lines.push(`• **${pm.pm_name}**: ${pct}% of time`);
    }
    return lines.join("\n");
  }

  // --- PM summary ---
  if (pmId && !priority) {
    const pm = pmCache[pmId]?.summary;
    if (!pm) return "PM not found.";
    const sources = Object.entries(pm.source_breakdown).sort((a, b) => b[1] - a[1]);
    const priorities = Object.entries(pm.priority_breakdown).sort((a, b) => b[1] - a[1]);
    const lines = [
      `**${pm.pm_name}** — ${pm.total_activities} activities this period\n`,
      `**Priority Alignment:** ${pm.alignment_pct}%`,
      `**Meeting Hours:** ${pm.meeting_hours.toFixed(1)}h (${pm.meetings} meetings)`,
      `**Top Priority:** ${pm.top_priority}\n`,
      `**Source Breakdown:**`,
    ];
    for (const [s, count] of sources) lines.push(`• ${s}: ${count}`);
    lines.push(`\n**Priority Breakdown:**`);
    for (const [p, pct] of priorities) lines.push(`• ${p}: ${pct}%`);
    return lines.join("\n");
  }

  // --- General dashboard question ---
  if (msg.includes("dashboard") || msg.includes("summary") || msg.includes("team") || msg.includes("overview")) {
    const lines = [
      `**Team Dashboard Summary**\n`,
      `**Total Activities:** ${dashCache.total_activities}`,
      `**Average Priority Alignment:** ${dashCache.avg_alignment_pct}%`,
      `**Team Balance Score:** ${dashCache.team_balance_score}%`,
      `**Active Recommendations:** ${dashCache.total_recommendations}\n`,
    ];
    for (const pm of dashCache.pm_summaries) {
      lines.push(`• **${pm.pm_name}**: ${pm.total_activities} activities, ${pm.alignment_pct}% aligned, ${pm.meeting_hours.toFixed(1)}h meetings`);
    }
    lines.push(`\n**Weekly Insight:** ${dashCache.top_insight}`);
    return lines.join("\n");
  }

  // --- Key decisions ---
  if (decisionsCache && (msg.includes("decision") || msg.includes("decided") || msg.includes("aligned"))) {
    const decisions = pmId
      ? decisionsCache.key_decisions.filter((d) => d.pm_id === pmId)
      : decisionsCache.key_decisions;
    if (decisions.length === 0) return "No key decisions found for that filter.";
    const pmLabel = pmId ? `for **${pmCache[pmId]?.summary.pm_name || pmId}**` : "across the team";
    const lines = [`Here are the **key decisions** ${pmLabel} this week (${decisionsCache.week_iso}):\n`];
    for (const d of decisions) {
      lines.push(`- **${d.description}**\n  ${d.pm_name} · ${d.channel} · ${d.date}`);
    }
    lines.push(`\n${decisions.length} decision(s) total.`);
    return lines.join("\n");
  }

  // --- Open questions / blockers ---
  if (decisionsCache && (msg.includes("open question") || msg.includes("blocker") || msg.includes("unresolved") || msg.includes("pending"))) {
    const questions = pmId
      ? decisionsCache.open_questions.filter((q) => q.owner_pm_id === pmId)
      : decisionsCache.open_questions;
    if (questions.length === 0) return "No open questions found for that filter.";
    const pmLabel = pmId ? `owned by **${pmCache[pmId]?.summary.pm_name || pmId}**` : "across the team";
    const urgencyIcon: Record<string, string> = { high: "!!!", medium: "!!", low: "!" };
    const lines = [`Here are the **open questions** ${pmLabel}:\n`];
    for (const q of questions) {
      lines.push(`- [${urgencyIcon[q.urgency] || "!!"} ${q.urgency.toUpperCase()}] **${q.description}**\n  Owner: ${q.owner_pm_name} · ${q.channel}`);
    }
    const highCount = questions.filter((q) => q.urgency === "high").length;
    if (highCount > 0) lines.push(`\n**${highCount} high-priority** item(s) need attention.`);
    return lines.join("\n");
  }

  // --- Keyword search fallback ---
  const keywords = msg.replace(/[^\w\s]/g, "").split(/\s+/).filter((w) => w.length > 3);
  if (keywords.length > 0) {
    const allActs: Activity[] = [];
    for (const pmData of Object.values(pmCache)) allActs.push(...pmData.activities);
    const matched = allActs.filter((a) => {
      const text = `${a.title} ${a.summary}`.toLowerCase();
      return keywords.some((kw) => text.includes(kw));
    });
    if (matched.length > 0) {
      const lines = [`Found **${matched.length} activities** matching your query:\n`];
      for (const a of matched.slice(0, 8)) {
        const pmName = pmCache[a.pm_id]?.summary.pm_name || a.pm_id;
        lines.push(`• [${a.source}] **${a.title}** — ${pmName}`);
      }
      if (matched.length > 8) lines.push(`\n...and ${matched.length - 8} more.`);
      lines.push(`\nTry asking about a specific PM or priority for deeper analysis.`);
      return lines.join("\n");
    }
  }

  return "I can help you analyze your team's activities, time allocation, and priorities. Try asking something like:\n\n• \"How much time did Jordan spend on Insights Agent?\"\n• \"Which PM has the lowest priority alignment?\"\n• \"Compare meeting hours across all PMs\"\n• \"Show me Morgan's activity breakdown by source\"";
}
