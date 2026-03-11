<script setup lang="ts">
defineProps<{
  nodeDetail: Record<string, unknown> | null;
  edgeDetail: Record<string, unknown> | null;
}>();
</script>

<template>
  <aside class="drawer">
    <template v-if="nodeDetail">
      <div class="drawer-header">
        <p class="eyebrow">Node Detail</p>
        <h3>{{ (nodeDetail.node as any)?.label }}</h3>
      </div>
      <dl class="metric-grid">
        <div>
          <dt>Type</dt>
          <dd>{{ (nodeDetail.node as any)?.node_type }}</dd>
        </div>
        <div>
          <dt>Pagerank</dt>
          <dd>{{ Number((nodeDetail.metrics as any)?.pagerank ?? 0).toFixed(3) }}</dd>
        </div>
        <div>
          <dt>Degree</dt>
          <dd>{{ Number((nodeDetail.metrics as any)?.degree_centrality ?? 0).toFixed(3) }}</dd>
        </div>
        <div>
          <dt>Messages</dt>
          <dd>{{ (nodeDetail.messages as any[])?.length ?? 0 }}</dd>
        </div>
      </dl>
      <section class="detail-list">
        <h4>Conversations</h4>
        <ul>
          <li v-for="conversation in (nodeDetail.conversations as any[]).slice(0, 8)" :key="conversation.conversation_id">
            <strong>{{ conversation.conversation_id }}</strong>
            <span>{{ conversation.combined_text }}</span>
          </li>
        </ul>
      </section>
    </template>
    <template v-else-if="edgeDetail">
      <div class="drawer-header">
        <p class="eyebrow">Edge Detail</p>
        <h3>{{ (edgeDetail.edge as any)?.edge_type }}</h3>
      </div>
      <dl class="metric-grid">
        <div>
          <dt>Weight</dt>
          <dd>{{ (edgeDetail.edge as any)?.weight }}</dd>
        </div>
        <div>
          <dt>Conversations</dt>
          <dd>{{ (edgeDetail.conversations as any[])?.length ?? 0 }}</dd>
        </div>
      </dl>
      <section class="detail-list">
        <h4>Evidence</h4>
        <ul>
          <li v-for="conversation in (edgeDetail.conversations as any[]).slice(0, 8)" :key="conversation.conversation_id">
            <strong>{{ conversation.conversation_id }}</strong>
            <span>{{ conversation.combined_text }}</span>
          </li>
        </ul>
      </section>
    </template>
    <div v-else class="empty-state">
      <p class="eyebrow">Selection</p>
      <h3>No node or edge selected</h3>
      <p>Click a node or edge in the graph to inspect its evidence.</p>
    </div>
  </aside>
</template>

<style scoped>
.drawer {
  min-height: 460px;
  padding: 1.25rem;
  border-radius: 28px;
  background: linear-gradient(180deg, rgba(17, 22, 25, 0.92), rgba(12, 15, 17, 0.84));
  border: 1px solid rgba(255, 227, 184, 0.14);
}

.drawer-header h3,
.empty-state h3 {
  margin: 0.35rem 0 0;
  font-size: 1.5rem;
}

.eyebrow {
  margin: 0;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-size: 0.68rem;
  color: var(--crepe-accent);
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  margin: 1.4rem 0;
}

.metric-grid dt {
  color: var(--crepe-muted);
  font-size: 0.8rem;
}

.metric-grid dd {
  margin: 0.25rem 0 0;
  font-size: 1.05rem;
}

.detail-list ul {
  padding: 0;
  margin: 0;
  list-style: none;
  display: grid;
  gap: 0.9rem;
}

.detail-list li {
  padding: 0.9rem;
  border-radius: 18px;
  background: rgba(255, 246, 229, 0.04);
}

.detail-list span {
  display: block;
  margin-top: 0.35rem;
  color: var(--crepe-muted);
  line-height: 1.45;
}

.empty-state {
  display: grid;
  gap: 0.6rem;
}
</style>
