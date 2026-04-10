"use client";
import { useEffect, useState } from "react";
import { getDashboard, getDecisions, DashboardData, DecisionsData, KeyDecision, OpenQuestion, Recommendation, PMSummary } from "@/lib/api";
import Link from "next/link";

function MetricCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="card p-5">
      <div className="text-[12px] font-medium" style={{ color: "var(--text-secondary)" }}>{label}</div>
      <div className="text-[28px] font-semibold mt-1" style={{ color: color || "var(--text-primary)" }}>{value}</div>
      {sub && <div className="text-[12px] mt-1" style={{ color: "var(--text-secondary)" }}>{sub}</div>}
    </div>
  );
}

function AIInsightBanner({ insight }: { insight: string }) {
  return (
    <div className="card p-5 flex items-start gap-3" style={{ borderLeft: "3px solid var(--ai-teal)" }}>
      <span className="text-xl" style={{ color: "var(--ai-teal)" }}>✦</span>
      <div>
        <div className="text-[14px] font-semibold" style={{ color: "var(--text-primary)" }}>Weekly Insight</div>
        <div className="text-[13px] mt-1" style={{ color: "var(--text-secondary)" }}>{insight}</div>
      </div>
    </div>
  );
}

function RecCard({ rec }: { rec: Recommendation }) {
  const kindColors: Record<string, string> = {
    Accelerate: "badge-accelerate",
    Cut: "badge-cut",
    Redirect: "badge-redirect",
  };
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span style={{ color: "var(--ai-teal)" }}>✦</span>
          <span className="text-[13px] font-semibold">{rec.pm_name}</span>
        </div>
        <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${kindColors[rec.kind]}`}>
          {rec.kind}
        </span>
      </div>
      <div className="text-[13px]" style={{ color: "var(--text-primary)" }}>{rec.action}</div>
      <div className="text-[12px] mt-2" style={{ color: "var(--text-secondary)" }}>{rec.rationale}</div>
      {rec.judge_score && (
        <div className="mt-2 text-[11px]" style={{ color: "var(--text-secondary)" }}>
          Judge score: {rec.judge_score}/5 · {rec.evidence_ids?.length || 0} evidence items
        </div>
      )}
    </div>
  );
}

// Fixed color map — same priority = same color across all PMs
const PRIORITY_COLOR_MAP: Record<string, string> = {
  "Insights Agent & Scaled AI": "var(--chart-navy)",
  "Email Report Reimagine & Custom Reports": "var(--chart-blue)",
  "Marketing Performance Reporting via QB BI": "var(--chart-teal)",
  "Other": "var(--chart-pink)",
};

function priorityColor(name: string): string {
  return PRIORITY_COLOR_MAP[name] || "var(--chart-pink)";
}

function DecisionCard({ decision }: { decision: KeyDecision }) {
  return (
    <div className="card p-4">
      <div className="flex items-start gap-3">
        <span style={{ color: "var(--ai-teal)", fontSize: 14, marginTop: 2 }}>✦</span>
        <div className="flex-1">
          <div className="text-[13px]" style={{ color: "var(--text-primary)" }}>{decision.description}</div>
          <div className="flex items-center gap-3 mt-2 text-[11px]" style={{ color: "var(--text-secondary)" }}>
            <span>{decision.pm_name}</span>
            <span>·</span>
            <span>{decision.channel}</span>
            <span>·</span>
            <span>{decision.date}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function OpenQuestionCard({ question }: { question: OpenQuestion }) {
  const urgencyStyles: Record<string, { bg: string; text: string }> = {
    high: { bg: "#fde8ea", text: "#d13438" },
    medium: { bg: "#fff8e1", text: "#f5a623" },
    low: { bg: "#e8f0fd", text: "#0070d2" },
  };
  const style = urgencyStyles[question.urgency] || urgencyStyles.medium;
  return (
    <div className="card p-4">
      <div className="flex items-start gap-3">
        <span style={{ fontSize: 14, marginTop: 2 }}>&#x2753;</span>
        <div className="flex-1">
          <div className="text-[13px]" style={{ color: "var(--text-primary)" }}>{question.description}</div>
          <div className="flex items-center gap-3 mt-2 text-[11px]" style={{ color: "var(--text-secondary)" }}>
            <span>Owner: {question.owner_pm_name}</span>
            <span>·</span>
            <span>{question.channel}</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium" style={{ background: style.bg, color: style.text }}>{question.urgency}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function PMRow({ pm }: { pm: PMSummary }) {
  const priorities = Object.entries(pm.priority_breakdown);
  return (
    <Link href={`/pm/${pm.pm_id}`} className="card p-4 hover:shadow-md transition-shadow block">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-semibold text-white"
            style={{ background: "var(--accent-blue)" }}
          >
            {pm.pm_name.split(" ").map(n => n[0]).join("")}
          </div>
          <div>
            <div className="text-[14px] font-semibold">{pm.pm_name}</div>
            <div className="text-[12px]" style={{ color: "var(--text-secondary)" }}>
              {pm.total_activities} activities · {pm.meeting_hours}h meetings
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-[20px] font-semibold" style={{ color: pm.alignment_pct >= 70 ? "var(--green)" : "var(--warning)" }}>
            {pm.alignment_pct}%
          </div>
          <div className="text-[11px]" style={{ color: "var(--text-secondary)" }}>aligned</div>
        </div>
      </div>
      {/* Priority bar */}
      <div className="flex h-2 rounded-full overflow-hidden bg-gray-100">
        {priorities.map(([name, pct]) => (
          <div
            key={name}
            style={{ width: `${pct}%`, background: priorityColor(name) }}
            title={`${name}: ${pct}%`}
          />
        ))}
      </div>
      <div className="flex gap-3 mt-2 flex-wrap">
        {priorities.map(([name, pct]) => (
          <div key={name} className="flex items-center gap-1 text-[11px]" style={{ color: "var(--text-secondary)" }}>
            <span className="w-2 h-2 rounded-full inline-block" style={{ background: priorityColor(name) }} />
            {name}: {pct}%
          </div>
        ))}
      </div>
    </Link>
  );
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [decisions, setDecisions] = useState<DecisionsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboard().then(setData).finally(() => setLoading(false));
    getDecisions().then(setDecisions).catch(() => {});
  }, []);

  if (loading) return <div className="p-8 text-[14px]" style={{ color: "var(--text-secondary)" }}>Loading dashboard...</div>;
  if (!data) return <div className="p-8 text-[14px]" style={{ color: "var(--red)" }}>Failed to load dashboard</div>;

  // Greeting based on time of day
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const dateStr = new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });

  // Analysis period: Monday–Thursday of the current week
  const now = new Date();
  const dayOfWeek = now.getDay(); // 0=Sun, 1=Mon, ...
  const monday = new Date(now);
  monday.setDate(now.getDate() - ((dayOfWeek + 6) % 7)); // most recent Monday
  const thursday = new Date(monday);
  thursday.setDate(monday.getDate() + 3);
  const friday = new Date(monday);
  friday.setDate(monday.getDate() + 4);
  const fmt = (d: Date) => d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  const periodLabel = `${fmt(monday)} \u2013 ${fmt(thursday)}, ${monday.getFullYear()}`;
  const reportDateLabel = `Report generated: ${fmt(friday)}, ${friday.getFullYear()} at 9:00 AM PST`;

  return (
    <div className="p-6 max-w-[1200px] mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[24px] font-semibold">{greeting}, Alex</h1>
          <p className="text-[13px] mt-1" style={{ color: "var(--text-secondary)" }}>{dateStr}</p>
        </div>
        <div className="text-right">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg" style={{ background: "rgba(0,185,169,0.08)", border: "1px solid rgba(0,185,169,0.2)" }}>
            <span style={{ color: "var(--ai-teal)", fontSize: 14 }}>✦</span>
            <span className="text-[13px] font-semibold" style={{ color: "var(--text-primary)" }}>Analysis Period: {periodLabel}</span>
          </div>
          <p className="text-[11px] mt-1" style={{ color: "var(--text-secondary)" }}>{reportDateLabel}</p>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard label="Total Activities" value={String(data.total_activities)} sub="this period" />
        <MetricCard
          label="Priority Alignment"
          value={`${data.avg_alignment_pct}%`}
          sub="team average"
          color={data.avg_alignment_pct >= 70 ? "var(--green)" : "var(--warning)"}
        />
        <MetricCard label="Recommendations" value={String(data.total_recommendations)} sub="this week" color="var(--accent-blue)" />
        <MetricCard label="Team Balance" value={`${data.team_balance_score}%`} sub="workload distribution" color="var(--ai-teal)" />
      </div>

      {/* AI Insight */}
      <AIInsightBanner insight={data.top_insight} />

      {/* Team overview */}
      <div>
        <h2 className="text-[16px] font-semibold mb-3">Team Overview</h2>
        <div className="space-y-3">
          {data.pm_summaries.map((pm) => (
            <PMRow key={pm.pm_id} pm={pm} />
          ))}
        </div>
      </div>

      {/* Key Decisions */}
      {decisions && decisions.key_decisions.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-[16px] font-semibold flex items-center gap-2">
              <span style={{ color: "var(--ai-teal)" }}>✦</span> Key Decisions
            </h2>
            <Link href="/decisions/" className="text-[13px] font-medium" style={{ color: "var(--accent-blue)" }}>View all &rarr;</Link>
          </div>
          <div className="space-y-2">
            {decisions.key_decisions.slice(0, 4).map((d) => (
              <DecisionCard key={d.id} decision={d} />
            ))}
          </div>
        </div>
      )}

      {/* Open Questions */}
      {decisions && decisions.open_questions.length > 0 && (
        <div>
          <h2 className="text-[16px] font-semibold flex items-center gap-2 mb-3">
            <span>&#x2753;</span> Open Questions
            <span className="text-[12px] font-normal px-2 py-0.5 rounded-full" style={{ background: "#fde8ea", color: "#d13438" }}>
              {decisions.open_questions.filter(q => q.urgency === "high").length} high priority
            </span>
          </h2>
          <div className="space-y-2">
            {decisions.open_questions.map((q) => (
              <OpenQuestionCard key={q.id} question={q} />
            ))}
          </div>
        </div>
      )}

      {/* Recent Recommendations */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[16px] font-semibold">This Week&apos;s Coaching</h2>
          <Link href="/recommendations" className="text-[13px] font-medium" style={{ color: "var(--accent-blue)" }}>
            View all →
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {data.recommendations.slice(0, 6).map((rec) => (
            <RecCard key={rec.id} rec={rec} />
          ))}
        </div>
      </div>
    </div>
  );
}
