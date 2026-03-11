<script setup lang="ts">
import { computed, ref } from "vue";
import type { Recommendation } from "../types/api";

const props = defineProps<{
  recommendations: Recommendation[];
}>();

const selectedId = ref("");

const selected = computed(() => props.recommendations.find((item) => item.suggestion_id === selectedId.value) ?? props.recommendations[0]);

function choose(id: string) {
  selectedId.value = id;
}
</script>

<template>
  <div class="recommend-grid">
    <div class="recommend-list">
      <button
        v-for="recommendation in recommendations"
        :key="recommendation.suggestion_id"
        class="recommend-card"
        type="button"
        :class="{ active: selected?.suggestion_id === recommendation.suggestion_id }"
        @click="choose(recommendation.suggestion_id)"
      >
        <p class="eyebrow">{{ recommendation.action }}</p>
        <h3>{{ recommendation.proposed_channel_name }}</h3>
        <p>{{ recommendation.rationale }}</p>
      </button>
    </div>
    <article v-if="selected" class="recommend-detail" data-testid="recommendation-detail">
      <p class="eyebrow">Selected recommendation</p>
      <h2>{{ selected.proposed_channel_name }}</h2>
      <dl class="meta">
        <div>
          <dt>Action</dt>
          <dd>{{ selected.action }}</dd>
        </div>
        <div>
          <dt>Source channels</dt>
          <dd>{{ selected.source_channels }}</dd>
        </div>
        <div>
          <dt>Confidence</dt>
          <dd>{{ selected.confidence }}</dd>
        </div>
        <div>
          <dt>Evidence count</dt>
          <dd>{{ selected.evidence_count }}</dd>
        </div>
      </dl>
      <p class="detail-copy">{{ selected.rationale }}</p>
    </article>
  </div>
</template>

<style scoped>
.recommend-grid {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 1rem;
}

.recommend-list {
  display: grid;
  gap: 0.85rem;
}

.recommend-card,
.recommend-detail {
  padding: 1rem;
  border-radius: 22px;
  border: 1px solid rgba(255, 227, 184, 0.14);
  background: rgba(14, 19, 21, 0.85);
  color: inherit;
}

.recommend-card {
  text-align: left;
  cursor: pointer;
}

.recommend-card.active {
  border-color: rgba(224, 182, 108, 0.65);
  box-shadow: 0 0 0 1px rgba(224, 182, 108, 0.25);
}

.eyebrow {
  margin: 0;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-size: 0.68rem;
  color: var(--crepe-accent);
}

.meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.9rem;
}

.detail-copy {
  color: var(--crepe-muted);
  line-height: 1.6;
}

@media (max-width: 980px) {
  .recommend-grid {
    grid-template-columns: 1fr;
  }
}
</style>
