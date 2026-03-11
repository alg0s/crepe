import { reactive, readonly } from "vue";
import {
  createRun,
  getClusters,
  getEdgeDetail,
  getGraph,
  getNodeDetail,
  getRecommendations,
  getSummary,
  listRuns
} from "../lib/api";
import type {
  ClusterPayload,
  EdgeDetailPayload,
  GraphPayload,
  NodeDetailPayload,
  RecommendationsPayload,
  RunRecord,
  SummaryPayload
} from "../types/api";

type GraphMode = "user_network" | "channel_overlap" | "theme_network" | "activity_network" | "team_channel_flow";

const state = reactive({
  runs: [] as RunRecord[],
  currentRunId: "",
  graphMode: "user_network" as GraphMode,
  edgeThreshold: 0,
  graph: null as GraphPayload | null,
  summary: null as SummaryPayload | null,
  clusters: null as ClusterPayload | null,
  recommendations: null as RecommendationsPayload | null,
  nodeDetail: null as NodeDetailPayload | null,
  edgeDetail: null as EdgeDetailPayload | null,
  loading: false,
  error: ""
});

export function useAppStore() {
  async function refreshRuns() {
    await runTask(async () => {
      state.runs = await listRuns();
      if (!state.currentRunId && state.runs.length) {
        state.currentRunId = state.runs[0].run_id;
      }
    });
  }

  async function launchRun() {
    await runTask(async () => {
      const run = await createRun({ pipeline: "all", background: true, scope: {} });
      state.currentRunId = run.run_id;
      await refreshRuns();
    });
  }

  async function loadSummary() {
    if (!state.currentRunId) return;
    await runTask(async () => {
      state.summary = await getSummary(state.currentRunId);
    });
  }

  async function loadGraph() {
    if (!state.currentRunId) return;
    await runTask(async () => {
      state.graph = await getGraph(state.currentRunId, state.graphMode, state.edgeThreshold);
    });
  }

  async function loadClusters() {
    if (!state.currentRunId) return;
    await runTask(async () => {
      state.clusters = await getClusters(state.currentRunId);
    });
  }

  async function loadRecommendations() {
    if (!state.currentRunId) return;
    await runTask(async () => {
      state.recommendations = await getRecommendations(state.currentRunId);
    });
  }

  async function selectNode(nodeId: string) {
    if (!state.currentRunId) return;
    await runTask(async () => {
      state.edgeDetail = null;
      state.nodeDetail = await getNodeDetail(state.currentRunId, nodeId);
    });
  }

  async function selectEdge(edgeId: string) {
    if (!state.currentRunId) return;
    await runTask(async () => {
      state.nodeDetail = null;
      state.edgeDetail = await getEdgeDetail(state.currentRunId, edgeId);
    });
  }

  function setGraphMode(mode: GraphMode) {
    state.graphMode = mode;
  }

  function setCurrentRun(runId: string) {
    state.currentRunId = runId;
  }

  function setEdgeThreshold(value: number) {
    state.edgeThreshold = value;
  }

  function resetSelection() {
    state.nodeDetail = null;
    state.edgeDetail = null;
  }

  return {
    state: readonly(state),
    refreshRuns,
    launchRun,
    loadSummary,
    loadGraph,
    loadClusters,
    loadRecommendations,
    selectNode,
    selectEdge,
    setGraphMode,
    setCurrentRun,
    setEdgeThreshold,
    resetSelection
  };
}

async function runTask(fn: () => Promise<void>) {
  state.loading = true;
  state.error = "";
  try {
    await fn();
  } catch (error) {
    state.error = error instanceof Error ? error.message : String(error);
  } finally {
    state.loading = false;
  }
}
