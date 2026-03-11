<script setup lang="ts">
import { computed, onMounted } from "vue";
import MiniChart from "../components/MiniChart.vue";
import { useAppStore } from "../stores/app";

const store = useAppStore();

const clusterLabels = computed(() => (store.state.summary?.top_clusters ?? []).slice(0, 5).map((item) => String(item.keywords ?? item.cluster_id)));
const clusterValues = computed(() => (store.state.summary?.top_clusters ?? []).slice(0, 5).map((item) => Number(item.conversation_count ?? 0)));

onMounted(async () => {
  await store.refreshRuns();
  await store.loadSummary();
  await store.loadRecommendations();
});
</script>

<template>
  <section class="page">
    <header class="hero">
      <div>
        <p class="eyebrow">Overview</p>
        <h1>Communication topology at a glance</h1>
        <p class="lede">crepe turns Teams traffic into a navigable map of influence, overlap, and emerging channel structure.</p>
      </div>
      <div class="hero-stat">
        <span>Latest run</span>
        <strong>{{ store.state.currentRunId || "No run selected" }}</strong>
      </div>
    </header>

    <div class="summary-grid">
      <article class="summary-card">
        <span>Conversations</span>
        <strong>{{ store.state.summary?.summary?.conversation_count ?? 0 }}</strong>
      </article>
      <article class="summary-card">
        <span>Graph nodes</span>
        <strong>{{ store.state.summary?.summary?.node_count ?? 0 }}</strong>
      </article>
      <article class="summary-card">
        <span>Recommendations</span>
        <strong>{{ store.state.summary?.recommendation_count ?? 0 }}</strong>
      </article>
    </div>

    <div class="chart-grid">
      <MiniChart title="Dominant themes" :labels="clusterLabels" :values="clusterValues" />
      <article class="narrative-panel">
        <p class="eyebrow">Interpretation</p>
        <h2>Where communication concentrates</h2>
        <p>
          The explorer is optimized for structural questions: who is central, which channels overlap, and where recurring themes spill across boundaries.
          Use the graph to inspect evidence, then move to recommendations to convert those patterns into a proposed channel taxonomy.
        </p>
      </article>
    </div>
  </section>
</template>

<style scoped>
.page {
  display: grid;
  gap: 1.25rem;
}

.hero,
.summary-card,
.narrative-panel,
.hero-stat {
  border-radius: 28px;
  border: 1px solid rgba(255, 227, 184, 0.14);
  background: rgba(12, 16, 18, 0.88);
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 240px;
  gap: 1rem;
  padding: 1.4rem;
}

.hero h1 {
  margin: 0.45rem 0;
  font-size: clamp(2.2rem, 5vw, 4rem);
}

.lede {
  max-width: 62ch;
  color: var(--crepe-muted);
}

.hero-stat,
.summary-card,
.narrative-panel {
  padding: 1.1rem;
}

.hero-stat span,
.summary-card span {
  display: block;
  color: var(--crepe-muted);
}

.hero-stat strong,
.summary-card strong {
  display: block;
  margin-top: 0.45rem;
  font-size: 2rem;
}

.summary-grid,
.chart-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.chart-grid {
  grid-template-columns: 1.4fr 1fr;
}

.eyebrow {
  margin: 0;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-size: 0.68rem;
  color: var(--crepe-accent);
}

@media (max-width: 980px) {
  .hero,
  .summary-grid,
  .chart-grid {
    grid-template-columns: 1fr;
  }
}
</style>
