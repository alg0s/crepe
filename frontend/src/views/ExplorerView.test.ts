import { mount } from "@vue/test-utils";
import ExplorerView from "./ExplorerView.vue";

vi.mock("../stores/app", () => {
  const state = {
    runs: [{ run_id: "fixture-run" }],
    currentRunId: "fixture-run",
    graphMode: "user_network",
    edgeThreshold: 0,
    graph: { run_id: "fixture-run", mode: "user_network", nodes: [], links: [] },
    nodeDetail: null,
    edgeDetail: null
  };
  return {
    useAppStore: () => ({
      state,
      refreshRuns: vi.fn(),
      loadGraph: vi.fn(),
      selectNode: vi.fn(),
      selectEdge: vi.fn(),
      setCurrentRun: vi.fn((value: string) => {
        state.currentRunId = value;
      }),
      setGraphMode: vi.fn((value: string) => {
        state.graphMode = value;
      }),
      setEdgeThreshold: vi.fn((value: number) => {
        state.edgeThreshold = value;
      }),
      resetSelection: vi.fn()
    })
  };
});

describe("ExplorerView", () => {
  it("renders graph controls", () => {
    const wrapper = mount(ExplorerView, {
      global: {
        stubs: {
          GraphCanvas: true
        }
      }
    });
    expect(wrapper.get("[data-testid='graph-mode']").exists()).toBe(true);
    expect(wrapper.get("[data-testid='edge-threshold']").exists()).toBe(true);
  });
});
