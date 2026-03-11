import { mount } from "@vue/test-utils";
import { nextTick } from "vue";
import ThemesView from "./ThemesView.vue";

const refreshRuns = vi.fn(async () => undefined);
const loadClusters = vi.fn(async () => undefined);

vi.mock("../stores/app", () => ({
  useAppStore: () => ({
    state: {
      clusters: {
        summary: [
          {
            cluster_id: 1,
            keywords: "PERSON_u1 CHANNEL_c1",
            conversation_count: 3,
            top_channels: "c1|c2",
            top_participants: "u1|u2"
          }
        ]
      }
    },
    refreshRuns,
    loadClusters
  })
}));

describe("ThemesView", () => {
  it("loads clusters and renders cluster cards", async () => {
    const wrapper = mount(ThemesView, {
      global: {
        stubs: {
          MiniChart: true
        }
      }
    });
    await nextTick();
    expect(refreshRuns).toHaveBeenCalled();
    expect(loadClusters).toHaveBeenCalled();
    expect(wrapper.text()).toContain("Cluster 1");
    expect(wrapper.text()).toContain("Top channels: c1|c2");
  });
});
