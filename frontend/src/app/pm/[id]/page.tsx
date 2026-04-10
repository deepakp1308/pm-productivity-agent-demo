"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getPMSummary, getPMActivities, getLatestRecommendations, PMSummary, Activity, Recommendation } from "@/lib/api";
import Link from "next/link";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, AreaChart, Area, Legend } from "recharts";

interface TrendData {
  weeks: string[];
  alignment_pct: number[];
  priority_breakdown: Record<string, number[]>;
}

const PRIORITY_COLORS: Record<string, string> = {
  "Insights Agent & Scaled AI": "#1e3a6e",
  "Email Report Reimagine & Custom Reports": "#4472c4",
  "Marketing Performance Reporting via QB BI": "#00b9a9",
  "Other": "#f4809b",
};

const SOURCE_COLORS: Record<string, string> = {
  calendar: "#1e3a6e",
  slack: "#4472c4",
  email: "#00b9a9",
  jira: "#f4809b",
};

const SOURCE_ICONS: Record<string, string> = {
  calendar: "📅",
  slack: "💬",
  email: "✉️",
  jira: "🎫",
};

export default function PMDetail() {
  const params = useParams();
  const pmId = params.id as string;
  const [summary, setSummary] = useState<PMSummary | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [sourceFilter, setSourceFilter] = useState<string>("all");
  const [trends, setTrends] = useState<TrendData | null>(null);

  useEffect(() => {
    getPMSummary(pmId).then(setSummary);
    getPMActivities(pmId).then(setActivities);
    getLatestRecommendations(pmId).then((d) => setRecs(d.recommendations));
    fetch("/api/trends.json")
      .then((r) => r.json())
      .then((all: Record<string, TrendData>) => {
        if (all[pmId]) setTrends(all[pmId]);
      })
      .catch(() => {});
  }, [pmId]);

  const filteredActivities = sourceFilter === "all"
    ? activities
    : activities.filter((a) => a.source === sourceFilter);

  if (!summary) return <div className="p-8 text-[14px]" style={{ color: "var(--text-secondary)" }}>Loading...</div>;

  const sourceData = Object.entries(summary.source_breakdown).map(([name, value]) => ({
    name, value, color: SOURCE_COLORS[name] || "#9ca3af",
  }));

  const priorityData = Object.entries(summary.priority_breakdown).map(([name, value]) => ({
    name: name.length > 18 ? name.slice(0, 16) + "…" : name,
    fullName: name,
    value,
  }));

  const kindColors: Record<string, string> = {
    Accelerate: "badge-accelerate",
    Cut: "badge-cut",
    Redirect: "badge-redirect",
  };

  return (
    <div className="p-6 max-w-[1200px] mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div
          className="w-12 h-12 rounded-full flex items-center justify-center text-[16px] font-semibold text-white"
          style={{ background: "var(--accent-blue)" }}
        >
          {summary.pm_name.split(" ").map((n) => n[0]).join("")}
        </div>
        <div>
          <h1 className="text-[24px] font-semibold">{summary.pm_name}</h1>
          <p className="text-[13px]" style={{ color: "var(--text-secondary)" }}>
            Top priority: {summary.top_priority} · {summary.meeting_hours}h meetings this period
          </p>
        </div>
        <Link href="/" className="ml-auto text-[13px]" style={{ color: "var(--accent-blue)" }}>
          ← Back to dashboard
        </Link>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-5 gap-3">
        {[
          { label: "Activities", value: summary.total_activities },
          { label: "Meetings", value: summary.meetings },
          { label: "Messages", value: summary.messages },
          { label: "Emails", value: summary.emails },
          { label: "Tickets", value: summary.tickets },
        ].map((kpi) => (
          <div key={kpi.label} className="card p-4 text-center">
            <div className="text-[22px] font-semibold">{kpi.value}</div>
            <div className="text-[11px]" style={{ color: "var(--text-secondary)" }}>{kpi.label}</div>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-2 gap-4">
        {/* Source donut */}
        <div className="card p-5">
          <h3 className="text-[14px] font-semibold mb-3">Time by Source</h3>
          <div className="flex items-center justify-center">
            <PieChart width={200} height={200}>
              <Pie data={sourceData} cx={100} cy={100} innerRadius={55} outerRadius={85}
                dataKey="value" paddingAngle={2}>
                {sourceData.map((s) => <Cell key={s.name} fill={s.color} />)}
              </Pie>
              <Tooltip formatter={(v: number) => `${v} activities`} />
            </PieChart>
            <div className="ml-4 space-y-2">
              {sourceData.map((s) => (
                <div key={s.name} className="flex items-center gap-2 text-[12px]">
                  <span className="w-3 h-3 rounded-sm inline-block" style={{ background: s.color }} />
                  <span className="capitalize">{s.name}</span>
                  <span style={{ color: "var(--text-secondary)" }}>{s.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Priority bars */}
        <div className="card p-5">
          <h3 className="text-[14px] font-semibold mb-3">Priority Breakdown</h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={priorityData} layout="vertical" margin={{ left: 10, right: 20 }}>
              <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: number) => `${v}%`} />
              <Bar dataKey="value" fill="var(--chart-navy)" radius={[0, 4, 4, 0]} barSize={20} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Trend charts */}
      {trends && (
        <div className="grid grid-cols-2 gap-4">
          {/* Priority Alignment Trend */}
          <div className="card p-5">
            <h3 className="text-[14px] font-semibold mb-3">Priority Alignment Trend</h3>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart
                data={trends.weeks.map((w, i) => ({
                  week: w.replace("2026-", ""),
                  alignment: trends.alignment_pct[i],
                }))}
                margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
              >
                <XAxis dataKey="week" tick={{ fontSize: 11 }} />
                <YAxis domain={[60, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => `${v}%`} />
                <Line
                  type="monotone"
                  dataKey="alignment"
                  stroke="#1e3a6e"
                  strokeWidth={2}
                  dot={{ fill: "#1e3a6e", r: 3 }}
                  name="Alignment %"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Priority Breakdown Trend */}
          <div className="card p-5">
            <h3 className="text-[14px] font-semibold mb-3">Priority Breakdown Trend</h3>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart
                data={trends.weeks.map((w, i) => {
                  const point: Record<string, string | number> = { week: w.replace("2026-", "") };
                  Object.entries(trends.priority_breakdown).forEach(([key, vals]) => {
                    point[key] = vals[i];
                  });
                  return point;
                })}
                margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
              >
                <XAxis dataKey="week" tick={{ fontSize: 11 }} />
                <YAxis tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => `${v.toFixed(1)}%`} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {Object.keys(trends.priority_breakdown).map((key) => (
                  <Area
                    key={key}
                    type="monotone"
                    dataKey={key}
                    stackId="1"
                    stroke={PRIORITY_COLORS[key] || "#9ca3af"}
                    fill={PRIORITY_COLORS[key] || "#9ca3af"}
                    fillOpacity={0.7}
                    name={key.length > 20 ? key.slice(0, 18) + "..." : key}
                  />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Alignment score */}
      <div className="card p-5 flex items-center gap-4">
        <div className="text-[32px] font-semibold" style={{ color: summary.alignment_pct >= 70 ? "var(--green)" : "var(--warning)" }}>
          {summary.alignment_pct}%
        </div>
        <div>
          <div className="text-[14px] font-semibold">Priority Alignment</div>
          <div className="text-[12px]" style={{ color: "var(--text-secondary)" }}>
            Percentage of time spent on stated team priorities
          </div>
        </div>
      </div>

      {/* AI Coaching */}
      {recs.length > 0 && (
        <div>
          <h2 className="text-[16px] font-semibold mb-3 flex items-center gap-2">
            <span style={{ color: "var(--ai-teal)" }}>✦</span> Coaching Recommendations
          </h2>
          <div className="space-y-3">
            {recs.map((rec) => (
              <div key={rec.id} className="card p-5">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${kindColors[rec.kind]}`}>
                    {rec.kind}
                  </span>
                  {rec.judge_score && (
                    <span className="text-[11px]" style={{ color: "var(--text-secondary)" }}>
                      Score: {rec.judge_score}/5
                    </span>
                  )}
                </div>
                <div className="text-[13px]">{rec.action}</div>
                <div className="text-[12px] mt-2" style={{ color: "var(--text-secondary)" }}>{rec.rationale}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Activity feed */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[16px] font-semibold">Activity Feed</h2>
          <div className="flex gap-2">
            {["all", "calendar", "slack", "email", "jira"].map((s) => (
              <button
                key={s}
                onClick={() => setSourceFilter(s)}
                className={`source-pill ${sourceFilter === s ? "active" : ""}`}
              >
                {s === "all" ? "All" : SOURCE_ICONS[s]} {s === "all" ? "" : s.charAt(0).toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>
        </div>
        <div className="space-y-2">
          {filteredActivities.slice(0, 30).map((a) => (
            <div key={a.id} className="card p-4 flex items-start gap-3">
              <span className="text-base mt-0.5">{SOURCE_ICONS[a.source] || "📄"}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-[13px] font-medium truncate">{a.title}</span>
                  {a.priority_name && a.priority_name !== "Other" && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-50" style={{ color: "var(--accent-blue)" }}>
                      {a.priority_name}
                    </span>
                  )}
                </div>
                {a.summary && (
                  <div className="text-[12px] mt-0.5 truncate" style={{ color: "var(--text-secondary)" }}>{a.summary}</div>
                )}
              </div>
              <div className="text-[11px] whitespace-nowrap" style={{ color: "var(--text-secondary)" }}>
                {new Date(a.occurred_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
