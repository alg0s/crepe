<script setup lang="ts">
import { onMounted } from "vue";
import RecommendationPanel from "../components/RecommendationPanel.vue";
import { useAppStore } from "../stores/app";

const store = useAppStore();

onMounted(async () => {
  await store.refreshRuns();
  await store.loadRecommendations();
});
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Recommendations</p>
        <h1>Channel migration plan</h1>
      </div>
    </header>

    <RecommendationPanel :recommendations="store.state.recommendations?.recommendations ?? []" />

    <article class="taxonomy-panel">
      <p class="eyebrow">Taxonomy markdown</p>
      <pre>{{ store.state.recommendations?.taxonomy_markdown ?? "" }}</pre>
    </article>
  </section>
</template>

<style scoped>
.page {
  display: grid;
  gap: 1rem;
}

.taxonomy-panel {
  padding: 1rem;
  border-radius: 24px;
  border: 1px solid rgba(255, 227, 184, 0.14);
  background: rgba(12, 16, 18, 0.88);
}

pre {
  white-space: pre-wrap;
  font-family: "Avenir Next", "Segoe UI", sans-serif;
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
