import type {
  ActiveJobPayload,
  ClusterPayload,
  EdgeDetailPayload,
  GraphPayload,
  NodeDetailPayload,
  RecommendationsPayload,
  RunRecord,
  SettingsPayload,
  SettingsTestResult,
  SettingsUpdateRequest,
  SummaryPayload,
  SystemStatusPayload
} from "../types/api";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json"
    },
    ...init
  });
  const raw = await response.text();
  if (!response.ok) {
    let detailMessage = "";
    if (raw) {
      try {
        const payload = JSON.parse(raw) as { detail?: unknown };
        if (typeof payload.detail === "string" && payload.detail) {
          detailMessage = payload.detail;
        }
      } catch {
        // Fall back to raw body as-is.
      }
    }
    throw new Error(detailMessage || raw || `Request failed: ${response.status}`);
  }
  if (!raw) {
    return {} as T;
  }
  return JSON.parse(raw) as T;
}

export function listRuns() {
  return request<RunRecord[]>("/api/runs");
}

export function createRun(payload: { run_id?: string; pipeline?: string; background?: boolean; scope?: Record<string, unknown> }) {
  return request<RunRecord>("/api/runs", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getSystemStatus() {
  return request<SystemStatusPayload>("/api/system/status");
}

export function getSettings() {
  return request<SettingsPayload>("/api/settings");
}

export function updateSettings(payload: SettingsUpdateRequest) {
  return request<SettingsPayload>("/api/settings", {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function testGraphSettings() {
  return request<SettingsTestResult>("/api/settings/test-graph", {
    method: "POST"
  });
}

export function getActiveJob() {
  return request<ActiveJobPayload>("/api/jobs/active");
}

export function pauseActiveJob() {
  return request<{ ok: boolean; run_id: string; status: string; stage: string }>("/api/jobs/pause", {
    method: "POST"
  });
}

export function cancelActiveJob() {
  return request<{ ok: boolean; run_id: string; status: string; stage: string }>("/api/jobs/cancel", {
    method: "POST"
  });
}

export function getSummary(runId: string) {
  return request<SummaryPayload>(`/api/runs/${runId}/summary`);
}

export function getGraph(runId: string, mode: string, edgeThreshold: number) {
  const query = new URLSearchParams({ mode, edge_threshold: String(edgeThreshold) });
  return request<GraphPayload>(`/api/runs/${runId}/graph?${query}`);
}

export function getNodeDetail(runId: string, nodeId: string) {
  return request<NodeDetailPayload>(`/api/runs/${runId}/nodes/${encodeURIComponent(nodeId)}`);
}

export function getEdgeDetail(runId: string, edgeId: string) {
  return request<EdgeDetailPayload>(`/api/runs/${runId}/edges/${encodeURIComponent(edgeId)}`);
}

export function getClusters(runId: string) {
  return request<ClusterPayload>(`/api/runs/${runId}/clusters`);
}

export function getRecommendations(runId: string) {
  return request<RecommendationsPayload>(`/api/runs/${runId}/recommendations`);
}
