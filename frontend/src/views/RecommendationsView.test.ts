import { mount } from "@vue/test-utils";
import { nextTick } from "vue";
import RecommendationsView from "./RecommendationsView.vue";

const refreshRuns = vi.fn(async () => undefined);
const loadRecommendations = vi.fn(async () => undefined);

vi.mock("../stores/app", () => ({
  useAppStore: () => ({
    state: {
      recommendations: {
        recommendations: [
          {
            suggestion_id: "s1",
            action: "merge",
            proposed_channel_name: "Merged",
            source_channels: "c1|c2",
            rationale: "overlap",
            confidence: 0.8,
            evidence_count: 5
          }
        ],
        taxonomy_markdown: "# Taxonomy\n- sample"
      }
    },
    refreshRuns,
    loadRecommendations
  })
}));

describe("RecommendationsView", () => {
  it("loads recommendations and renders markdown section", async () => {
    const wrapper = mount(RecommendationsView, {
      global: {
        stubs: {
          RecommendationPanel: true
        }
      }
    });
    await nextTick();
    expect(refreshRuns).toHaveBeenCalled();
    expect(loadRecommendations).toHaveBeenCalled();
    expect(wrapper.text()).toContain("Taxonomy markdown");
    expect(wrapper.text()).toContain("sample");
  });
});
