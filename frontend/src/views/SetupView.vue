<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useAppStore } from "../stores/app";

const store = useAppStore();
const saveNotice = ref("");

const form = reactive({
  tenantId: "",
  clientId: "",
  clientSecret: ""
});

const settings = computed(() => store.state.settings);
const status = computed(() => store.state.systemStatus);

async function saveSettings() {
  saveNotice.value = "";
  await store.saveSettings({
    tenant_id: form.tenantId.trim() || undefined,
    client_id: form.clientId.trim() || undefined,
    client_secret: form.clientSecret.trim() || undefined
  });
  if (!store.state.error) {
    saveNotice.value = "Settings saved.";
    form.tenantId = "";
    form.clientId = "";
    form.clientSecret = "";
  }
}

async function testConnection() {
  await store.runSettingsTest();
}

onMounted(async () => {
  await store.loadSettings();
  await store.loadSystemStatus();
});
</script>

<template>
  <section class="setup-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Setup</p>
        <h1>Configure Teams credentials</h1>
      </div>
    </header>

    <article class="panel">
      <p class="muted">Managed secret file: <code>{{ settings?.managed_env_path ?? "loading..." }}</code></p>

      <div class="credential-grid">
        <label>
          Tenant ID
          <input v-model="form.tenantId" type="password" placeholder="Enter new value to update" />
        </label>
        <label>
          Client ID
          <input v-model="form.clientId" type="password" placeholder="Enter new value to update" />
        </label>
        <label>
          Client Secret
          <input v-model="form.clientSecret" type="password" placeholder="Enter new value to update" />
        </label>
      </div>

      <div class="actions">
        <button type="button" class="action-button" @click="saveSettings">Save settings</button>
        <button type="button" class="ghost-button" @click="testConnection">Test connection</button>
      </div>

      <p v-if="saveNotice" class="notice">{{ saveNotice }}</p>
      <p v-if="store.state.settingsTest" class="notice" :class="{ error: !store.state.settingsTest.ok }">
        {{ store.state.settingsTest.ok ? "Graph token test passed." : store.state.settingsTest.error }}
      </p>
    </article>

    <article class="panel">
      <p class="eyebrow">Status</p>
      <h3>{{ status?.graph_auth_configured ? "Ready to run" : "Missing credentials" }}</h3>
      <p class="muted">
        Active env file: <code>{{ status?.active_env_path ?? "n/a" }}</code>
      </p>
      <p class="muted" v-if="status && status.missing_credentials.length">
        Missing: <code>{{ status.missing_credentials.join(", ") }}</code>
      </p>
    </article>
  </section>
</template>

<style scoped>
.setup-page {
  display: grid;
  gap: 1rem;
}

.panel {
  display: grid;
  gap: 0.9rem;
  padding: 1.1rem;
  border-radius: 24px;
  border: 1px solid rgba(255, 227, 184, 0.14);
  background: rgba(12, 16, 18, 0.88);
}

.credential-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.8rem;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.notice {
  margin: 0;
  color: #bde7d5;
}

.notice.error {
  color: #ffd7ca;
}

.muted {
  margin: 0;
  color: var(--crepe-muted);
}

.eyebrow {
  margin: 0;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-size: 0.68rem;
  color: var(--crepe-accent);
}

@media (max-width: 980px) {
  .credential-grid {
    grid-template-columns: 1fr;
  }
}
</style>
