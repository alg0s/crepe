<script setup lang="ts">
import { computed, onMounted } from "vue";
import DetailDrawer from "../components/DetailDrawer.vue";
import EvidenceTray from "../components/EvidenceTray.vue";
import GraphCanvas from "../components/GraphCanvas.vue";
import { useAppStore } from "../stores/app";

const store = useAppStore();
const graph = computed(() => store.state.graph);
const modeOptions = [
  { label: "User network", value: "user_network" },
  { label: "Channel overlap", value: "channel_overlap" },
  { label: "Theme network", value: "theme_network" },
  { label: "Activity network", value: "activity_network" },
  { label: "Team-channel flow", value: "team_channel_flow" }
];

const evidenceConversations = computed(() => (store.state.nodeDetail?.conversations ?? store.state.edgeDetail?.conversations ?? []) as Array<Record<string, unknown>>);
const evidenceMessages = computed(() => (store.state.nodeDetail?.messages ?? []) as Array<Record<string, unknown>>);

onMounted(async () => {
  await store.refreshRuns();
  await store.loadGraph();
});
</script>

<template>
  <section class="explorer-page">
    <aside class="filter-rail">
      <p class="eyebrow">Explorer</p>
      <h2>Investigate the graph</h2>
      <label>
        Run
        <select :value="store.state.currentRunId" @change="store.setCurrentRun(($event.target as HTMLSelectElement).value)">
          <option v-for="run in store.state.runs" :key="run.run_id" :value="run.run_id">{{ run.run_id }}</option>
        </select>
      </label>
      <label>
        Graph mode
        <select
          data-testid="graph-mode"
          :value="store.state.graphMode"
          @change="store.setGraphMode(($event.target as HTMLSelectElement).value as any)"
        >
          <option v-for="option in modeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
        </select>
      </label>
      <label>
        Edge threshold
        <input
          data-testid="edge-threshold"
          type="range"
          min="0"
          max="10"
          step="1"
          :value="store.state.edgeThreshold"
          @input="store.setEdgeThreshold(Number(($event.target as HTMLInputElement).value))"
        />
      </label>
      <div class="actions">
        <button type="button" class="action-button" @click="store.loadGraph">Refresh graph</button>
        <button type="button" class="ghost-button" @click="store.resetSelection">Clear selection</button>
      </div>
    </aside>

    <div class="graph-stack">
      <GraphCanvas
        :nodes="graph?.nodes ?? []"
        :links="graph?.links ?? []"
        @node-selected="store.selectNode"
        @edge-selected="store.selectEdge"
      />
      <EvidenceTray :conversations="evidenceConversations" :messages="evidenceMessages" />
    </div>

    <DetailDrawer :node-detail="store.state.nodeDetail" :edge-detail="store.state.edgeDetail" />
  </section>
</template>

<style scoped>
.explorer-page {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr) 340px;
  gap: 1rem;
}

.filter-rail {
  display: grid;
  gap: 1rem;
  align-content: start;
  padding: 1.15rem;
  border-radius: 28px;
  background: rgba(12, 16, 18, 0.9);
  border: 1px solid rgba(255, 227, 184, 0.14);
}

.filter-rail select,
.filter-rail input {
  width: 100%;
}

.graph-stack {
  display: grid;
  gap: 1rem;
}

.actions {
  display: grid;
  gap: 0.75rem;
}

.eyebrow {
  margin: 0;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-size: 0.68rem;
  color: var(--crepe-accent);
}

@media (max-width: 1180px) {
  .explorer-page {
    grid-template-columns: 1fr;
  }
}
</style>
