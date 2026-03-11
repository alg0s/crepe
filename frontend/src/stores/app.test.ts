import { useAppStore } from "./app";

describe("app store", () => {
  it("updates graph mode and edge threshold", () => {
    const store = useAppStore();
    store.setGraphMode("theme_network");
    store.setEdgeThreshold(4);
    expect(store.state.graphMode).toBe("theme_network");
    expect(store.state.edgeThreshold).toBe(4);
  });
});
