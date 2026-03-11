<script setup lang="ts">
import { computed, onMounted } from "vue";
import MiniChart from "../components/MiniChart.vue";
import { useAppStore } from "../stores/app";

const store = useAppStore();
const labels = computed(() => (store.state.clusters?.summary ?? []).slice(0, 8).map((item) => String(item.keywords ?? item.cluster_id)));
const values = computed(() => (store.state.clusters?.summary ?? []).slice(0, 8).map((item) => Number(item.conversation_count ?? 0)));

onMounted(async () => {
  await store.refreshRuns();
  await store.loadClusters();
});
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Themes</p>
        <h1>Clustered conversation surfaces</h1>
      </div>
    </header>

    <MiniChart title="Theme intensity" :labels="labels" :values="values" type="line" />

    <div class="cluster-grid">
      <article v-for="cluster in store.state.clusters?.summary ?? []" :key="String(cluster.cluster_id)" class="cluster-card">
        <p class="eyebrow">Cluster {{ cluster.cluster_id }}</p>
        <h3>{{ cluster.keywords }}</h3>
        <p>{{ cluster.conversation_count }} conversations</p>
        <p class="muted">Top channels: {{ cluster.top_channels || "n/a" }}</p>
        <p class="muted">Top participants: {{ cluster.top_participants || "n/a" }}</p>
      </article>
    </div>
  </section>
</template>

<style scoped>
.page {
  display: grid;
  gap: 1rem;
}

.cluster-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
}

.cluster-card {
  padding: 1rem;
  border-radius: 24px;
  border: 1px solid rgba(255, 227, 184, 0.14);
  background: rgba(12, 16, 18, 0.88);
}

.muted {
  color: var(--crepe-muted);
}

.eyebrow {
  margin: 0;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-size: 0.68rem;
  color: var(--crepe-accent);
}
</style>
