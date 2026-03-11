import { reactive, readonly } from "vue";
import {
  cancelActiveJob,
  createRun,
  getActiveJob,
  getClusters,
  getEdgeDetail,
  getGraph,
  getNodeDetail,
  getRecommendations,
  getSettings,
  getSummary,
  getSystemStatus,
  pauseActiveJob,
  testGraphSettings,
  updateSettings,
  listRuns
} from "../lib/api";
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
  systemStatus: null as SystemStatusPayload | null,
  settings: null as SettingsPayload | null,
  settingsTest: null as SettingsTestResult | null,
  activeJob: null as ActiveJobPayload | null,
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

  async function launchRun(pipeline: "all" | "demo" = "all") {
    await runTask(async () => {
      const run = await createRun({ pipeline, background: true, scope: {} });
      state.currentRunId = run.run_id;
      await refreshRuns();
    });
  }

  async function loadSystemStatus() {
    await runTask(async () => {
      state.systemStatus = await getSystemStatus();
    });
  }

  async function loadSettings() {
    await runTask(async () => {
      state.settings = await getSettings();
    });
  }

  async function saveSettings(payload: SettingsUpdateRequest) {
    await runTask(async () => {
      state.settings = await updateSettings(payload);
      state.systemStatus = await getSystemStatus();
    });
  }

  async function runSettingsTest() {
    await runTask(async () => {
      state.settingsTest = await testGraphSettings();
      state.systemStatus = await getSystemStatus();
    });
  }

  async function loadActiveJob() {
    await runTask(async () => {
      state.activeJob = await getActiveJob();
    });
  }

  async function pauseJob() {
    await runTask(async () => {
      await pauseActiveJob();
      state.activeJob = await getActiveJob();
      state.runs = await listRuns();
    });
  }

  async function cancelJob() {
    await runTask(async () => {
      await cancelActiveJob();
      state.activeJob = await getActiveJob();
      state.runs = await listRuns();
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
    loadSystemStatus,
    loadSettings,
    saveSettings,
    runSettingsTest,
    loadActiveJob,
    pauseJob,
    cancelJob,
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
