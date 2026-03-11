import { mount } from "@vue/test-utils";
import DetailDrawer from "./DetailDrawer.vue";

describe("DetailDrawer", () => {
  it("renders node detail metrics", () => {
    const wrapper = mount(DetailDrawer, {
      props: {
        nodeDetail: {
          node: { label: "Alice", node_type: "user" },
          metrics: { pagerank: 0.5, degree_centrality: 0.7 },
          conversations: [{ conversation_id: "c1", dominant_entities: "PERSON:u1|PERSON:u2", avg_sentiment_score: 0.2 }],
          messages: [{ message_id: "m1", receiver_ids: "u2", entity_ids: "PERSON:u1|PERSON:u2", sentiment_score: 0.2 }]
        },
        edgeDetail: null
      }
    });
    expect(wrapper.text()).toContain("Alice");
    expect(wrapper.text()).toContain("Pagerank");
  });
});
