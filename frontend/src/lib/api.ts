// Static mode: reads from pre-baked JSON files in /api/ folder
// No backend required — all data is bundled at build time

const API_BASE = "/api";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

export function getDashboard() {
  return fetchJSON<DashboardData>("/dashboard.json");
}

export function getTeam() {
  return fetchJSON<TeamMember[]>("/team.json");
}

export function getPMSummary(pmId: string) {
  return fetchJSON<PMSummary>(`/pm-${pmId}-summary.json`);
}

export function getPMActivities(pmId: string, source?: string) {
  // In static mode, load all activities then filter client-side
  return fetchJSON<Activity[]>(`/activities-${pmId}.json`).then((acts) =>
    source ? acts.filter((a) => a.source === source) : acts
  );
}

export function getPMTrends(pmId: string) {
  // Trends not available in static mode — return empty
  return Promise.resolve([] as PMSummary[]);
}

export function getPriorities() {
  return fetchJSON<Priority[]>("/priorities.json");
}

export function createPriority(data: { name: string; description?: string; weight?: number }) {
  return Promise.resolve({ id: 0 });
}

export function updatePriority(id: number, data: Partial<Priority>) {
  return Promise.resolve({ updated: false });
}

export function getLatestRecommendations(pmId?: string) {
  return fetchJSON<{ week_iso: string; recommendations: Recommendation[] } | Recommendation[]>("/recommendations.json").then((data) => {
    // Handle both formats: {week_iso, recommendations} or raw array
    const isWrapped = !Array.isArray(data) && (data as { recommendations: Recommendation[] }).recommendations;
    const allRecs: Recommendation[] = isWrapped
      ? (data as { recommendations: Recommendation[] }).recommendations
      : (data as Recommendation[]);
    const weekIso = isWrapped ? (data as { week_iso: string }).week_iso : (allRecs.length > 0 ? allRecs[0].week_iso : "");
    const filtered = pmId ? allRecs.filter((r) => r.pm_id === pmId) : allRecs;
    return { week_iso: weekIso, recommendations: filtered };
  });
}

export function getDecisions() {
  return fetchJSON<DecisionsData>("/decisions.json");
}

export async function sendChatMessage(message: string, sessionId?: string) {
  // Client-side chat engine — queries static JSON data directly
  const { answerQuestion } = await import("./chat-engine");
  const response = await answerQuestion(message);
  return {
    response,
    context: { session_id: sessionId || "static" },
  };
}

export function triggerPipeline(useLlm: boolean = false) {
  return Promise.resolve({
    run_id: 0,
    week_iso: "",
    status: "static_mode",
    error: "Pipeline not available in static mode",
  } as PipelineResult);
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: string;
}

export interface Priority {
  id: number;
  name: string;
  description: string;
  weight: number;
  active: boolean;
  updated_at: string;
}

export interface Activity {
  id: number;
  pm_id: string;
  source: string;
  title: string;
  summary: string;
  duration_minutes: number | null;
  occurred_at: string;
  priority_name: string | null;
  activity_type: string | null;
  leverage: string | null;
  confidence: number | null;
}

export interface PMSummary {
  pm_id: string;
  pm_name: string;
  total_activities: number;
  meetings: number;
  messages: number;
  emails: number;
  tickets: number;
  alignment_pct: number;
  top_priority: string;
  meeting_hours: number;
  fragmentation_score: number;
  source_breakdown: Record<string, number>;
  type_breakdown: Record<string, number>;
  priority_breakdown: Record<string, number>;
  week_iso?: string;
}

export interface Recommendation {
  id: number;
  week_iso: string;
  pm_id: string;
  pm_name: string;
  kind: "Accelerate" | "Cut" | "Redirect";
  action: string;
  rationale: string;
  evidence_ids: number[];
  judge_score: number | null;
  judge_reasoning: string | null;
  status: string;
  created_at: string;
}

export interface DashboardData {
  total_activities: number;
  avg_alignment_pct: number;
  total_recommendations: number;
  team_balance_score: number;
  pm_summaries: PMSummary[];
  priority_coverage: Record<string, Record<string, number>>;
  top_insight: string;
  recommendations: Recommendation[];
}

export interface PipelineResult {
  run_id: number;
  week_iso: string;
  status: string;
  activities_classified?: number;
  recommendations_generated?: number;
  error?: string;
}

export interface KeyDecision {
  id: number;
  description: string;
  pm_id: string;
  pm_name: string;
  date: string;
  channel: string;
  related_priority: string;
}

export interface OpenQuestion {
  id: number;
  description: string;
  owner_pm_id: string;
  owner_pm_name: string;
  urgency: "high" | "medium" | "low";
  channel: string;
  related_priority: string;
}

export interface DecisionsData {
  week_iso: string;
  generated_at: string;
  key_decisions: KeyDecision[];
  open_questions: OpenQuestion[];
}
