import type {
  ClusterPayload,
  EdgeDetailPayload,
  GraphPayload,
  NodeDetailPayload,
  RecommendationsPayload,
  RunRecord,
  SummaryPayload
} from "../types/api";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json"
    },
    ...init
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
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
