<script setup lang="ts">
defineProps<{
  conversations: Array<Record<string, unknown>>;
  messages: Array<Record<string, unknown>>;
}>();
</script>

<template>
  <section class="tray">
    <div>
      <p class="eyebrow">Evidence</p>
      <h3>Recent conversations</h3>
    </div>
    <div class="tray-grid">
      <article class="tray-panel">
        <h4>Conversations</h4>
        <ul>
          <li v-for="conversation in conversations.slice(0, 6)" :key="String(conversation.conversation_id)">
            <strong>{{ conversation.conversation_id }}</strong>
            <span>Entities: {{ conversation.dominant_entities || "none" }}</span>
            <span>Sentiment: {{ Number(conversation.avg_sentiment_score ?? 0).toFixed(2) }}</span>
          </li>
        </ul>
      </article>
      <article class="tray-panel">
        <h4>Messages</h4>
        <ul>
          <li v-for="message in messages.slice(0, 6)" :key="String(message.message_id)">
            <strong>{{ message.sender_name }}</strong>
            <span>Receivers: {{ message.receiver_ids || "none" }}</span>
            <span>Entities: {{ message.entity_ids || "none" }}</span>
            <span>Sentiment: {{ Number(message.sentiment_score ?? 0).toFixed(2) }} ({{ message.sentiment_label || "neutral" }})</span>
          </li>
        </ul>
      </article>
    </div>
  </section>
</template>

<style scoped>
.tray {
  padding: 1.2rem;
  border-radius: 28px;
  border: 1px solid rgba(255, 227, 184, 0.14);
  background: rgba(13, 17, 19, 0.85);
}

.eyebrow {
  margin: 0;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-size: 0.68rem;
  color: var(--crepe-accent);
}

.tray h3 {
  margin: 0.35rem 0 1rem;
}

.tray-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.tray-panel {
  padding: 1rem;
  border-radius: 20px;
  background: rgba(255, 246, 229, 0.03);
}

.tray-panel ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.75rem;
}

.tray-panel span {
  display: block;
  margin-top: 0.3rem;
  color: var(--crepe-muted);
}

@media (max-width: 900px) {
  .tray-grid {
    grid-template-columns: 1fr;
  }
}
</style>
