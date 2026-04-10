"use client";
import { useEffect, useState } from "react";
import { getDecisions, DecisionsData, KeyDecision, OpenQuestion } from "@/lib/api";

export default function DecisionsPage() {
  const [data, setData] = useState<DecisionsData | null>(null);
  const [filterPM, setFilterPM] = useState<string>("all");

  useEffect(() => {
    getDecisions().then(setData);
  }, []);

  if (!data) {
    return (
      <div className="p-8 text-[14px]" style={{ color: "var(--text-secondary)" }}>
        Loading decisions...
      </div>
    );
  }

  // Get unique PM names from decisions
  const pmNames = [...new Set(data.key_decisions.map((d) => d.pm_name))];

  // Filter decisions by PM
  const filteredDecisions =
    filterPM === "all"
      ? data.key_decisions
      : data.key_decisions.filter((d) => d.pm_id === filterPM);

  // Filter open questions by PM
  const filteredQuestions =
    filterPM === "all"
      ? data.open_questions
      : data.open_questions.filter((q) => q.owner_pm_id === filterPM);

  // Group decisions by PM
  const groupedDecisions: Record<string, KeyDecision[]> = {};
  filteredDecisions.forEach((d) => {
    if (!groupedDecisions[d.pm_name]) groupedDecisions[d.pm_name] = [];
    groupedDecisions[d.pm_name].push(d);
  });

  const urgencyStyles: Record<string, { bg: string; text: string }> = {
    high: { bg: "#fde8ea", text: "#d13438" },
    medium: { bg: "#fff8e1", text: "#f5a623" },
    low: { bg: "#e8f0fd", text: "#0070d2" },
  };

  const highCount = filteredQuestions.filter((q) => q.urgency === "high").length;

  return (
    <div className="p-6 max-w-[1000px] mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[24px] font-semibold flex items-center gap-2">
            <span style={{ color: "var(--ai-teal)" }}>✦</span> Key Decisions &amp; Open Questions
          </h1>
          <p className="text-[13px] mt-1" style={{ color: "var(--text-secondary)" }}>
            Week {data.week_iso} &middot; {data.key_decisions.length} decisions &middot; {data.open_questions.length} open questions
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setFilterPM("all")}
            className={`source-pill ${filterPM === "all" ? "active" : ""}`}
          >
            All
          </button>
          {pmNames.map((name) => {
            const pmId = data.key_decisions.find((d) => d.pm_name === name)?.pm_id || "";
            return (
              <button
                key={pmId}
                onClick={() => setFilterPM(pmId)}
                className={`source-pill ${filterPM === pmId ? "active" : ""}`}
              >
                {name}
              </button>
            );
          })}
        </div>
      </div>

      {/* Key Decisions grouped by PM */}
      <div>
        <h2 className="text-[18px] font-semibold flex items-center gap-2 mb-4">
          <span style={{ color: "var(--ai-teal)" }}>✦</span> Key Decisions
        </h2>
        {Object.entries(groupedDecisions).map(([pmName, decisions]) => (
          <div key={pmName} className="mb-6">
            <h3 className="text-[16px] font-semibold mb-3 flex items-center gap-2">
              <div
                className="w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-semibold text-white"
                style={{ background: "var(--accent-blue)" }}
              >
                {pmName
                  .split(" ")
                  .map((n) => n[0])
                  .join("")}
              </div>
              {pmName}
              <span className="text-[12px] font-normal" style={{ color: "var(--text-secondary)" }}>
                ({decisions.length})
              </span>
            </h3>
            <div className="space-y-3">
              {decisions.map((d) => (
                <div key={d.id} className="card p-5">
                  <div className="flex items-start gap-3">
                    <span style={{ color: "var(--ai-teal)", fontSize: 14, marginTop: 2 }}>✦</span>
                    <div className="flex-1">
                      <div className="text-[14px] font-medium" style={{ color: "var(--text-primary)" }}>
                        {d.description}
                      </div>
                      <div className="flex items-center gap-4 mt-3 text-[12px]" style={{ color: "var(--text-secondary)" }}>
                        <span>{d.channel}</span>
                        <span>&middot;</span>
                        <span>{d.date}</span>
                        <span>&middot;</span>
                        <span
                          className="px-2 py-0.5 rounded-full text-[11px]"
                          style={{ background: "rgba(0,185,169,0.08)", color: "var(--ai-teal)" }}
                        >
                          {d.related_priority}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
        {filteredDecisions.length === 0 && (
          <div className="card p-8 text-center">
            <div className="text-[14px]" style={{ color: "var(--text-secondary)" }}>
              No decisions found for this filter.
            </div>
          </div>
        )}
      </div>

      {/* Open Questions */}
      <div>
        <h2 className="text-[18px] font-semibold flex items-center gap-2 mb-4">
          <span>&#x2753;</span> Open Questions
          {highCount > 0 && (
            <span
              className="text-[12px] font-normal px-2 py-0.5 rounded-full"
              style={{ background: "#fde8ea", color: "#d13438" }}
            >
              {highCount} high priority
            </span>
          )}
        </h2>
        <div className="space-y-3">
          {filteredQuestions.map((q) => {
            const style = urgencyStyles[q.urgency] || urgencyStyles.medium;
            return (
              <div key={q.id} className="card p-5">
                <div className="flex items-start gap-3">
                  <span style={{ fontSize: 14, marginTop: 2 }}>&#x2753;</span>
                  <div className="flex-1">
                    <div className="text-[14px] font-medium" style={{ color: "var(--text-primary)" }}>
                      {q.description}
                    </div>
                    <div className="flex items-center gap-4 mt-3 text-[12px]" style={{ color: "var(--text-secondary)" }}>
                      <span>Owner: {q.owner_pm_name}</span>
                      <span>&middot;</span>
                      <span>{q.channel}</span>
                      <span>&middot;</span>
                      <span
                        className="px-2 py-0.5 rounded-full text-[11px] font-medium"
                        style={{ background: style.bg, color: style.text }}
                      >
                        {q.urgency}
                      </span>
                      <span>&middot;</span>
                      <span
                        className="px-2 py-0.5 rounded-full text-[11px]"
                        style={{ background: "rgba(0,185,169,0.08)", color: "var(--ai-teal)" }}
                      >
                        {q.related_priority}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        {filteredQuestions.length === 0 && (
          <div className="card p-8 text-center">
            <div className="text-[14px]" style={{ color: "var(--text-secondary)" }}>
              No open questions found for this filter.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
