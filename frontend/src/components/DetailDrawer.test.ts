import { mount } from "@vue/test-utils";
import DetailDrawer from "./DetailDrawer.vue";

describe("DetailDrawer", () => {
  it("renders node detail metrics", () => {
    const wrapper = mount(DetailDrawer, {
      props: {
        nodeDetail: {
          node: { label: "Alice", node_type: "user" },
          metrics: { pagerank: 0.5, degree_centrality: 0.7 },
          conversations: [{ conversation_id: "c1", combined_text: "hello" }],
          messages: [{ message_id: "m1", body_text: "hello" }]
        },
        edgeDetail: null
      }
    });
    expect(wrapper.text()).toContain("Alice");
    expect(wrapper.text()).toContain("Pagerank");
  });
});
