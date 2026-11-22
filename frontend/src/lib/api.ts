/* API client for the AgentProof backend. */

// ---------------------------------------------------------------------------
// TypeScript interfaces matching backend Pydantic models
// ---------------------------------------------------------------------------

export interface RunCreate {
  agent_id: string;
  model_provider: string;
  model_id: string;
  scenario?: Record<string, unknown>;
}

export interface RunState {
  run_id: string;
  agent_id: string;
  model_provider: string;
  model_id: string;
  status: "pending" | "running" | "completed" | "failed";
  events: Record<string, unknown>[];
  created_at: string;
  completed_at: string | null;
}

export interface PolicyDecision {
  action_type: string;
  decision: "ALLOW" | "BLOCK";
  reason: string;
  policy_version: string;
  evaluated_at: string;
}

export interface ToolResult {
  tool: string;
  success: boolean;
  result: Record<string, unknown>;
  blocked: boolean;
  reason: string | null;
}

export interface TimelineEvent {
  sequence: number;
  timestamp: string;
  type: string;
  summary: string;
}

export interface ProofReceipt {
  receipt_version: string;
  run_id: string;
  timestamp: string;
  agent_id: string;
  agent_version: string;
  model_provider: string;
  model_id: string;
  policy_version: string;
  container_image_digest: string;
  sbom_digest: string;
  cbom_digest: string;
  provenance_root: string;
  trace_root: string;
  state_root: string;
  benchmark_id: string | null;
  benchmark_score: number | null;
  receipt_root: string;
  signature: string;
  key_id: string;
}

export interface VerificationResult {
  valid: boolean;
  checks: Record<string, boolean>;
  errors: string[];
}

export interface ScenarioResult {
  scenario_id: string;
  scenario_name: string;
  passed: boolean;
  policy_adherence: boolean;
  unauthorized_actions: number;
  evidence_integrity: boolean;
  latency_ms: number;
  details: string;
}

export interface Scorecard {
  benchmark_id: string;
  timestamp: string;
  total_scenarios: number;
  passed: number;
  failed: number;
  scores: Record<string, number>;
  results: ScenarioResult[];
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export function createRun(
  agentId: string,
  modelProvider: string,
  modelId: string,
  scenario?: Record<string, unknown>,
): Promise<RunState> {
  return request<RunState>("/runs", {
    method: "POST",
    body: JSON.stringify({
      agent_id: agentId,
      model_provider: modelProvider,
      model_id: modelId,
      scenario,
    }),
  });
}

export function evaluateAction(
  runId: string,
  actionType: string,
  parameters: Record<string, unknown>,
): Promise<PolicyDecision> {
  return request<PolicyDecision>("/actions/evaluate", {
    method: "POST",
    body: JSON.stringify({
      run_id: runId,
      action_type: actionType,
      parameters,
    }),
  });
}

export function executeRefund(
  runId: string,
  orderId: string,
  amount: number,
  reason: string,
): Promise<ToolResult> {
  return request<ToolResult>("/tools/refund", {
    method: "POST",
    body: JSON.stringify({
      run_id: runId,
      order_id: orderId,
      amount,
      reason,
    }),
  });
}

export function executeDataSend(
  runId: string,
  destination: string,
  payload: string,
): Promise<ToolResult> {
  return request<ToolResult>("/tools/data-send", {
    method: "POST",
    body: JSON.stringify({
      run_id: runId,
      destination,
      payload,
      content_type: "application/json",
    }),
  });
}

export function getTimeline(runId: string): Promise<TimelineEvent[]> {
  return request<TimelineEvent[]>(`/runs/${runId}/timeline`);
}

export function finalizeRun(runId: string): Promise<ProofReceipt> {
  return request<ProofReceipt>(`/runs/${runId}/finalize`, { method: "POST" });
}

export function getReceipt(receiptId: string): Promise<ProofReceipt> {
  return request<ProofReceipt>(`/receipts/${receiptId}`);
}

export function verifyReceipt(
  receipt: ProofReceipt,
): Promise<VerificationResult> {
  return request<VerificationResult>("/verify", {
    method: "POST",
    body: JSON.stringify({ receipt }),
  });
}

export function runBenchmarks(): Promise<Scorecard> {
  return request<Scorecard>("/benchmarks/run", { method: "POST" });
}

export function getScenarios(): Promise<Scenario[]> {
  return request<Scenario[]>("/benchmarks/scenarios");
}
