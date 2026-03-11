import { mount } from "@vue/test-utils";
import RunsView from "./RunsView.vue";

const refreshRuns = vi.fn(async () => undefined);
const launchRun = vi.fn(async () => undefined);
const setCurrentRun = vi.fn();

vi.mock("../stores/app", () => ({
  useAppStore: () => ({
    state: {
      runs: [
        { run_id: "run-1", status: "completed", stage: "all", updated_at: "2025-01-01T00:00:00Z" },
        { run_id: "run-2", status: "running", stage: "analyze", updated_at: "2025-01-01T01:00:00Z" }
      ],
      currentRunId: "run-1"
    },
    refreshRuns,
    launchRun,
    setCurrentRun
  })
}));

describe("RunsView", () => {
  it("renders runs and supports run interactions", async () => {
    const wrapper = mount(RunsView);
    expect(refreshRuns).toHaveBeenCalled();
    expect(wrapper.text()).toContain("run-1");
    expect(wrapper.text()).toContain("run-2");
    await wrapper.find("button.action-button").trigger("click");
    expect(launchRun).toHaveBeenCalled();
    await wrapper.findAll(".run-card")[1].trigger("click");
    expect(setCurrentRun).toHaveBeenCalledWith("run-2");
  });
});
