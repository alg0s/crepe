<script setup lang="ts">
import { computed, onMounted, onUnmounted } from "vue";
import { useAppStore } from "../stores/app";

const store = useAppStore();
const missingCredentials = computed(() => store.state.systemStatus?.missing_credentials ?? []);
const hasGraphCredentials = computed(() => store.state.systemStatus?.graph_auth_configured ?? false);
const selectedRun = computed(() => store.state.runs.find((run) => run.run_id === store.state.currentRunId) ?? null);
const activeRun = computed(() => store.state.activeJob?.active_run ?? null);

let pollHandle: number | null = null;
let isRefreshing = false;

async function launchRealRun() {
  await store.launchRun("all");
}

async function launchDemoRun() {
  await store.launchRun("demo");
}

async function refreshRunsAndStatus() {
  if (isRefreshing) return;
  isRefreshing = true;
  try {
    await store.refreshRuns();
    await store.loadSystemStatus();
    await store.loadActiveJob();
  } finally {
    isRefreshing = false;
  }
}

onMounted(async () => {
  await refreshRunsAndStatus();
  pollHandle = window.setInterval(() => {
    void refreshRunsAndStatus();
  }, 3000);
});

onUnmounted(() => {
  if (pollHandle !== null) {
    window.clearInterval(pollHandle);
  }
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
        <button type="button" class="action-button" :disabled="!hasGraphCredentials" @click="launchRealRun">Run real Teams</button>
        <button type="button" class="ghost-button" @click="launchDemoRun">Run demo</button>
        <button type="button" class="ghost-button" :disabled="!activeRun || activeRun.status !== 'running'" @click="store.pauseJob">
          Pause job
        </button>
        <button type="button" class="ghost-button" :disabled="!activeRun" @click="store.cancelJob">Cancel job</button>
        <button type="button" class="ghost-button" @click="store.refreshRuns">Refresh</button>
      </div>
    </header>

    <article class="status-card">
      <p class="eyebrow">Microsoft Graph auth</p>
      <h3 v-if="hasGraphCredentials">Configured</h3>
      <h3 v-else>Missing credentials</h3>
      <p v-if="hasGraphCredentials" class="status-copy">
        Real Teams extraction is ready. You can use <strong>Run real Teams</strong>.
      </p>
      <p v-else class="status-copy">
        Add these credentials in Setup before running extraction: <code>{{ missingCredentials.join(", ") }}</code>.
      </p>
      <p class="status-copy">
        Active source: <code>{{ store.state.systemStatus?.credential_source ?? "managed" }}</code>
      </p>
      <p class="status-copy" v-if="store.state.systemStatus?.active_env_path">
        Active env: <code>{{ store.state.systemStatus?.active_env_path }}</code>
      </p>
      <p class="status-copy" v-if="selectedRun">
        Selected run stage: <strong>{{ selectedRun.stage }}</strong>
      </p>
      <p class="status-copy" v-if="activeRun">
        Active job: <strong>{{ activeRun.run_id }}</strong> ({{ activeRun.status }} / {{ activeRun.stage }})
      </p>
      <p class="status-copy error-copy" v-if="selectedRun?.error_message">
        Last error: {{ selectedRun.error_message }}
      </p>
    </article>

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
  flex-wrap: wrap;
  gap: 0.75rem;
}

.status-card {
  padding: 1rem 1.1rem;
  border-radius: 22px;
  border: 1px solid rgba(255, 227, 184, 0.14);
  background: rgba(12, 16, 18, 0.88);
}

.status-card h3 {
  margin: 0.35rem 0;
}

.status-copy {
  margin: 0;
  color: var(--crepe-muted);
}

.status-copy code {
  font-size: 0.88rem;
}

.error-copy {
  color: #ffd7ca;
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

.action-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
</style>
