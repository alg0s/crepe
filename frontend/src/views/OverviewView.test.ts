import { mount } from "@vue/test-utils";
import OverviewView from "./OverviewView.vue";

const refreshRuns = vi.fn(async () => undefined);
const loadSummary = vi.fn(async () => undefined);
const loadRecommendations = vi.fn(async () => undefined);

vi.mock("../stores/app", () => ({
  useAppStore: () => ({
    state: {
      currentRunId: "demo-run",
      summary: {
        summary: { conversation_count: 8, node_count: 16 },
        recommendation_count: 2,
        top_clusters: [{ cluster_id: 1, keywords: "PERSON_u1", conversation_count: 4 }]
      }
    },
    refreshRuns,
    loadSummary,
    loadRecommendations
  })
}));

describe("OverviewView", () => {
  it("loads overview data on mount", async () => {
    const wrapper = mount(OverviewView, {
      global: {
        stubs: {
          MiniChart: true
        }
      }
    });
    await Promise.resolve();
    await Promise.resolve();
    expect(wrapper.text()).toContain("Communication topology at a glance");
    expect(refreshRuns).toHaveBeenCalled();
    expect(loadSummary).toHaveBeenCalled();
    expect(loadRecommendations).toHaveBeenCalled();
  });
});
