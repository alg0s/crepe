import { mount } from "@vue/test-utils";
import RecommendationPanel from "./RecommendationPanel.vue";

describe("RecommendationPanel", () => {
  it("updates the detail view when a recommendation is selected", async () => {
    const wrapper = mount(RecommendationPanel, {
      props: {
        recommendations: [
          {
            suggestion_id: "one",
            action: "merge",
            proposed_channel_name: "Ops-Procurement",
            source_channels: "c1|c2",
            rationale: "Overlap",
            confidence: 0.8,
            evidence_count: 6
          },
          {
            suggestion_id: "two",
            action: "create",
            proposed_channel_name: "Forecast",
            source_channels: "c2|c3",
            rationale: "New theme",
            confidence: 0.6,
            evidence_count: 4
          }
        ]
      }
    });
    await wrapper.findAll("button")[1].trigger("click");
    expect(wrapper.get("[data-testid='recommendation-detail']").text()).toContain("Forecast");
  });
});
