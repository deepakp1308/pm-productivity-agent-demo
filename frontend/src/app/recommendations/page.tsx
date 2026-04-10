"use client";
import { useEffect, useState } from "react";
import { getLatestRecommendations, Recommendation } from "@/lib/api";

export default function RecommendationsPage() {
  const [weekIso, setWeekIso] = useState<string>("");
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [filterPM, setFilterPM] = useState<string>("all");

  useEffect(() => {
    getLatestRecommendations().then((d) => {
      setWeekIso(d.week_iso || "");
      setRecs(d.recommendations);
    });
  }, []);

  const filteredRecs = filterPM === "all" ? recs : recs.filter((r) => r.pm_id === filterPM);
  const pmNames = [...new Set(recs.map((r) => r.pm_name))];

  // Group by PM
  const grouped: Record<string, Recommendation[]> = {};
  filteredRecs.forEach((r) => {
    if (!grouped[r.pm_name]) grouped[r.pm_name] = [];
    grouped[r.pm_name].push(r);
  });

  const kindColors: Record<string, { bg: string; text: string; icon: string }> = {
    Accelerate: { bg: "#e8f7f0", text: "#1aab68", icon: "🚀" },
    Cut: { bg: "#fde8ea", text: "#d13438", icon: "✂️" },
    Redirect: { bg: "#e8f0fd", text: "#0070d2", icon: "↪️" },
  };

  return (
    <div className="p-6 max-w-[1000px] mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[24px] font-semibold flex items-center gap-2">
            <span style={{ color: "var(--ai-teal)" }}>✦</span> Weekly Coaching
          </h1>
          <p className="text-[13px] mt-1" style={{ color: "var(--text-secondary)" }}>
            Week {weekIso || "—"} · {recs.length} recommendations
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
            const pmId = recs.find((r) => r.pm_name === name)?.pm_id || "";
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

      {/* Recommendations grouped by PM */}
      {Object.entries(grouped).map(([pmName, pmRecs]) => (
        <div key={pmName}>
          <h2 className="text-[16px] font-semibold mb-3 flex items-center gap-2">
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-semibold text-white"
              style={{ background: "var(--accent-blue)" }}
            >
              {pmName.split(" ").map((n) => n[0]).join("")}
            </div>
            {pmName}
          </h2>
          <div className="space-y-3">
            {pmRecs.map((rec) => {
              const kind = kindColors[rec.kind] || kindColors.Redirect;
              return (
                <div key={rec.id} className="card p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-lg">{kind.icon}</span>
                    <span
                      className="text-[12px] font-semibold px-3 py-1 rounded-full"
                      style={{ background: kind.bg, color: kind.text }}
                    >
                      {rec.kind}
                    </span>
                    {rec.judge_score !== null && (
                      <span className="text-[11px] ml-auto" style={{ color: "var(--text-secondary)" }}>
                        Quality: {rec.judge_score}/5
                      </span>
                    )}
                    {rec.status === "blocked" && (
                      <span className="text-[11px] px-2 py-0.5 rounded-full" style={{ background: "#fde8ea", color: "var(--red)" }}>
                        Blocked by judge
                      </span>
                    )}
                  </div>
                  <div className="text-[14px] font-medium" style={{ color: "var(--text-primary)" }}>
                    {rec.action}
                  </div>
                  <div className="text-[13px] mt-2" style={{ color: "var(--text-secondary)" }}>
                    {rec.rationale}
                  </div>
                  {rec.evidence_ids && rec.evidence_ids.length > 0 && (
                    <div className="mt-3 pt-3" style={{ borderTop: "1px solid var(--border)" }}>
                      <div className="text-[11px]" style={{ color: "var(--text-secondary)" }}>
                        📎 {rec.evidence_ids.length} supporting evidence items (IDs: {rec.evidence_ids.slice(0, 5).join(", ")}{rec.evidence_ids.length > 5 ? "..." : ""})
                      </div>
                    </div>
                  )}
                  {rec.judge_reasoning && (
                    <details className="mt-2">
                      <summary className="text-[11px] cursor-pointer" style={{ color: "var(--accent-blue)" }}>
                        Judge reasoning
                      </summary>
                      <div className="text-[12px] mt-1 p-2 rounded" style={{ background: "var(--page-bg)", color: "var(--text-secondary)" }}>
                        {rec.judge_reasoning}
                      </div>
                    </details>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {recs.length === 0 && (
        <div className="card p-8 text-center">
          <div className="text-[14px]" style={{ color: "var(--text-secondary)" }}>
            No recommendations generated yet. Run the pipeline to generate coaching.
          </div>
        </div>
      )}
    </div>
  );
}
