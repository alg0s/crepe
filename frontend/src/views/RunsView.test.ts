import { mount } from "@vue/test-utils";
import RunsView from "./RunsView.vue";

const refreshRuns = vi.fn(async () => undefined);
const loadSystemStatus = vi.fn(async () => undefined);
const loadActiveJob = vi.fn(async () => undefined);
const launchRun = vi.fn(async (_pipeline?: "all" | "demo") => undefined);
const setCurrentRun = vi.fn();
const pauseJob = vi.fn(async () => undefined);
const cancelJob = vi.fn(async () => undefined);

vi.mock("../stores/app", () => ({
  useAppStore: () => ({
    state: {
      runs: [
        { run_id: "run-1", status: "completed", stage: "all", updated_at: "2025-01-01T00:00:00Z" },
        { run_id: "run-2", status: "running", stage: "analyze", updated_at: "2025-01-01T01:00:00Z" }
      ],
      currentRunId: "run-1",
      activeJob: {
        is_running: true,
        active_run: { run_id: "run-2", status: "running", stage: "analyze", updated_at: "2025-01-01T01:00:00Z" }
      },
      systemStatus: {
        graph_auth_configured: true,
        missing_credentials: [],
        credential_source: "managed",
        active_env_path: "/tmp/.env"
      }
    },
    refreshRuns,
    loadSystemStatus,
    loadActiveJob,
    launchRun,
    setCurrentRun,
    pauseJob,
    cancelJob
  })
}));

describe("RunsView", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders runs and supports run interactions", async () => {
    const wrapper = mount(RunsView);
    await Promise.resolve();
    expect(refreshRuns).toHaveBeenCalled();
    expect(loadSystemStatus).toHaveBeenCalled();
    expect(wrapper.text()).toContain("run-1");
    expect(wrapper.text()).toContain("run-2");
    await wrapper.find("button.action-button").trigger("click");
    expect(launchRun).toHaveBeenCalledWith("all");
    await wrapper.findAll("button.ghost-button")[0].trigger("click");
    expect(launchRun).toHaveBeenCalledWith("demo");
    await wrapper.findAll("button.ghost-button")[1].trigger("click");
    expect(pauseJob).toHaveBeenCalled();
    await wrapper.findAll("button.ghost-button")[2].trigger("click");
    expect(cancelJob).toHaveBeenCalled();
    await wrapper.findAll(".run-card")[1].trigger("click");
    expect(setCurrentRun).toHaveBeenCalledWith("run-2");
    wrapper.unmount();
  });
});
