// AgentPulse Real API Client

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";

export interface AgentRecord {
  id: string;
  name: string;
  description?: string;
  intended_use?: string;
  tone_guidelines?: string;
  prohibited_behaviours?: string[];
  adapter_type: "http_json" | "openai_compat" | "mock" | string;
  adapter_config: Record<string, any>;
  version_label?: string;
  status: "healthy" | "at_risk" | "degraded" | string;
  overall_score?: number | null;
  score?: number;
  lastRun?: string;
  conversationsCount?: number;
  alertsCount?: number;
  mode?: string;
}

export interface MetricSummary {
  score: number;
  threshold: number;
  passed: boolean;
  is_blocking: boolean;
  sample_count?: number;
}

export interface RunRecord {
  id: string;
  agent_id: string;
  suite_id: string;
  agent_version: string;
  status: "running" | "completed" | "failed" | string;
  scenario_count: number;
  verdict?: "PASS" | "FAIL" | string | null;
  score_overall?: number | null;
  cost_usd?: number;
  avg_latency_ms?: number;
  scorecard?: {
    overall_score: number;
    verdict: string;
    metrics_summary: Record<string, MetricSummary>;
    total_conversations: number;
    passed_conversations: number;
    failed_conversations: number;
    failure_clusters?: Array<{
      reason: string;
      count: number;
      metric_key?: string;
      sample_quote?: string;
    }>;
  } | null;
}

export interface ConversationTurn {
  idx: number;
  role: "user" | "agent" | string;
  content: string;
  latency_ms?: number;
  raw_response?: any;
}

export interface EvaluationResult {
  conversation_id: string;
  metric_key: string;
  score: number;
  passed: boolean;
  verdict: string;
  reasoning: string;
  evidence?: {
    turn: number;
    quote: string;
    verified: boolean;
  };
  judge_model: string;
}

export interface ConversationRecord {
  id: string;
  scenario_id: string;
  scenario_goal?: string;
  category: string;
  run_id: string;
  avg_latency_ms: number;
  passed: boolean;
  termination_reason?: string;
  turns: ConversationTurn[];
  evaluations: EvaluationResult[];
}

export interface ReviewQueueItem {
  evaluation_id: string;
  conversation_id: string;
  metric_key: string;
  score: number;
  verdict: string;
  reasoning: string;
  quote: string;
  confidence: number;
  agent_name: string;
  status?: string;
}

export interface AlertRecord {
  id: string;
  monitor_id: string;
  agent_name: string;
  severity: "info" | "warning" | "critical" | string;
  metric_key: string;
  status: "open" | "acknowledged" | "resolved" | string;
  summary: string;
  opened_at: string;
  evidence_quote?: string;
}

export interface TraceRecord {
  id: string;
  external_id: string;
  agent_id: string;
  channel: string;
  ingested_at: string;
  redacted: boolean;
  metadata?: Record<string, any>;
  turns: Array<{
    idx: number;
    role: string;
    content: string;
    latency_ms?: number;
  }>;
}

export interface AuditRecord {
  id: string;
  timestamp: string;
  org_id?: string;
  actor_id?: string;
  actor_email: string;
  action: string;
  resource_type: string;
  resource_id: string;
  client_ip: string;
  status: string;
  metadata?: Record<string, any>;
}

export interface CalibrationStats {
  judge_model: string;
  overall_kappa: number;
  metrics: Record<
    string,
    {
      metric_key: string;
      judge_model: string;
      sample_size: number;
      accuracy: number;
      precision: number;
      recall: number;
      cohen_kappa: number;
      confusion_matrix: {
        true_positive: number;
        false_positive: number;
        true_negative: number;
        false_negative: number;
      };
    }
  >;
}

// -------------------------------------------------------------
// Real Fetch Operations
// -------------------------------------------------------------

export async function fetchAgents(): Promise<AgentRecord[]> {
  const res = await fetch(`${API_BASE}/agents`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch agents: ${res.statusText}`);
  const data = await res.json();
  return data.map((a: any) => ({
    ...a,
    score: a.overall_score ?? a.score ?? 0.95,
    mode: a.adapter_type === "mock" ? (a.adapter_config?.mode || "good") : (a.mode || "live"),
    lastRun: a.lastRun || "Ready",
    conversationsCount: a.conversationsCount || 10,
    alertsCount: a.alertsCount || 0,
  }));
}

export async function fetchRuns(): Promise<RunRecord[]> {
  const res = await fetch(`${API_BASE}/runs`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch runs: ${res.statusText}`);
  return res.json();
}

export async function fetchRun(runId: string): Promise<RunRecord> {
  const res = await fetch(`${API_BASE}/runs/${runId}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch run ${runId}`);
  return res.json();
}

export async function fetchRunConversations(runId: string): Promise<ConversationRecord[]> {
  const res = await fetch(`${API_BASE}/runs/${runId}/conversations`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch conversations for run ${runId}`);
  return res.json();
}

export async function triggerLiveRun(agentId: string, suiteId: string, concurrency: number = 2): Promise<RunRecord> {
  const res = await fetch(`${API_BASE}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ agent_id: agentId, suite_id: suiteId, concurrency }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Failed to trigger run: ${err}`);
  }
  return res.json();
}

export async function testAgentConnection(
  adapterType: string,
  adapterConfig: Record<string, any>,
  testMessage: string
): Promise<{ success: boolean; reply: string; latency_ms: number; error?: string | null }> {
  const res = await fetch(`${API_BASE}/agents/test-connection`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      adapter_type: adapterType,
      adapter_config: adapterConfig,
      test_message: testMessage,
    }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Connection test failed: ${err}`);
  }
  return res.json();
}

export async function registerNewAgent(agentData: {
  name: string;
  description?: string;
  adapter_type: string;
  adapter_config: Record<string, any>;
  intended_use?: string;
  tone_guidelines?: string;
  prohibited_behaviours?: string[];
}): Promise<AgentRecord> {
  const res = await fetch(`${API_BASE}/agents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(agentData),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Failed to register agent: ${err}`);
  }
  return res.json();
}

export async function fetchCalibrationStats(): Promise<CalibrationStats> {
  const res = await fetch(`${API_BASE}/metrics/calibration`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch calibration data");
  return res.json();
}

export async function fetchReviewQueue(): Promise<ReviewQueueItem[]> {
  const res = await fetch(`${API_BASE}/metrics/review-queue`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch review queue");
  return res.json();
}

export async function overrideEvaluationVerdict(
  evalId: string,
  verdict: "pass" | "fail",
  auditReason: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/metrics/evaluations/${evalId}/override`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ new_verdict: verdict, audit_reason: auditReason }),
  });
  if (!res.ok) throw new Error("Failed to submit override");
  return res.json();
}

export async function fetchAlerts(): Promise<AlertRecord[]> {
  const res = await fetch(`${API_BASE}/alerts`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch alerts");
  return res.json();
}

export async function acknowledgeAlert(alertId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/alerts/${alertId}/acknowledge`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to acknowledge alert");
  return res.json();
}

export async function fetchTraces(): Promise<TraceRecord[]> {
  const res = await fetch(`${API_BASE}/traces`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch traces");
  return res.json();
}

export async function convertTraceToScenario(traceId: string, suiteId: string = "suite_people_ai"): Promise<any> {
  const res = await fetch(`${API_BASE}/traces/${traceId}/convert-to-scenario?suite_id=${suiteId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to convert trace to scenario");
  return res.json();
}

export async function fetchAuditLogs(): Promise<AuditRecord[]> {
  const res = await fetch(`${API_BASE}/audit/logs`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch audit logs");
  return res.json();
}

export async function fetchResilienceStatus(): Promise<any> {
  const res = await fetch(`${API_BASE}/system/resilience`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch resilience status");
  return res.json();
}

export async function fetchRlsDdl(): Promise<string> {
  const res = await fetch(`${API_BASE}/system/rls-ddl`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch RLS DDL");
  const data = await res.json();
  return data.ddl || "";
}

export async function compareRunsDiff(runA: string, runB: string): Promise<any> {
  const res = await fetch(`${API_BASE}/runs/compare/diff?run_a=${encodeURIComponent(runA)}&run_b=${encodeURIComponent(runB)}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to compare runs");
  return res.json();
}
