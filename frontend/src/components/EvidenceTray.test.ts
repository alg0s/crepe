import { mount } from "@vue/test-utils";
import EvidenceTray from "./EvidenceTray.vue";

describe("EvidenceTray", () => {
  it("renders metadata flow fields without message content fields", () => {
    const wrapper = mount(EvidenceTray, {
      props: {
        conversations: [
          {
            conversation_id: "conv-1",
            dominant_entities: "PERSON:u1|PERSON:u2",
            avg_sentiment_score: 0.2
          }
        ],
        messages: [
          {
            message_id: "m1",
            sender_name: "u1",
            receiver_ids: "u2",
            entity_ids: "PERSON:u1|PERSON:u2",
            sentiment_score: 0.2,
            sentiment_label: "positive"
          }
        ]
      }
    });
    expect(wrapper.text()).toContain("Entities:");
    expect(wrapper.text()).toContain("Receivers:");
    expect(wrapper.text()).toContain("Sentiment:");
    expect(wrapper.text()).not.toContain("body_text");
    expect(wrapper.text()).not.toContain("combined_text");
  });
});
