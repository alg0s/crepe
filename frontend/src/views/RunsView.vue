<script setup lang="ts">
import { onMounted } from "vue";
import { useAppStore } from "../stores/app";

const store = useAppStore();

onMounted(() => {
  store.refreshRuns();
});
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Runs</p>
        <h1>Snapshot orchestration</h1>
      </div>
      <div class="actions">
        <button type="button" class="action-button" @click="store.launchRun">Launch full run</button>
        <button type="button" class="ghost-button" @click="store.refreshRuns">Refresh</button>
      </div>
    </header>

    <div class="run-grid">
      <article
        v-for="run in store.state.runs"
        :key="run.run_id"
        class="run-card"
        :class="{ active: store.state.currentRunId === run.run_id }"
        @click="store.setCurrentRun(run.run_id)"
      >
        <p class="eyebrow">{{ run.status }}</p>
        <h3>{{ run.run_id }}</h3>
        <dl>
          <div>
            <dt>Stage</dt>
            <dd>{{ run.stage }}</dd>
          </div>
          <div>
            <dt>Updated</dt>
            <dd>{{ run.updated_at }}</dd>
          </div>
        </dl>
      </article>
    </div>
  </section>
</template>

<style scoped>
.page {
  display: grid;
  gap: 1rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-end;
}

.actions {
  display: flex;
  gap: 0.75rem;
}

.run-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1rem;
}

.run-card {
  padding: 1.1rem;
  border-radius: 24px;
  border: 1px solid rgba(255, 227, 184, 0.14);
  background: rgba(12, 16, 18, 0.88);
  cursor: pointer;
}

.run-card.active {
  border-color: rgba(224, 182, 108, 0.65);
}

.run-card dl {
  margin: 0.8rem 0 0;
  display: grid;
  gap: 0.5rem;
}

.run-card dt {
  color: var(--crepe-muted);
  font-size: 0.8rem;
}

.eyebrow {
  margin: 0;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-size: 0.68rem;
  color: var(--crepe-accent);
}
</style>
