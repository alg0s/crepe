<script setup lang="ts">
import { useAppStore } from "./stores/app";

const navItems = [
  { label: "Overview", href: "/overview" },
  { label: "Runs", href: "/runs" },
  { label: "Explorer", href: "/explorer" },
  { label: "Themes", href: "/themes" },
  { label: "Recommendations", href: "/recommendations" }
];

const store = useAppStore();
</script>

<template>
  <div class="app-shell">
    <header class="shell-header">
      <div>
        <p class="eyebrow">crepe</p>
        <h1>Teams communication intelligence</h1>
      </div>
      <nav class="shell-nav">
        <RouterLink v-for="item in navItems" :key="item.href" :to="item.href" class="nav-link">{{ item.label }}</RouterLink>
      </nav>
    </header>

    <div v-if="store.state.error" class="error-banner" data-testid="app-error">
      {{ store.state.error }}
    </div>

    <main class="shell-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  padding: 1.2rem;
}

.shell-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 1rem;
  align-items: center;
  margin-bottom: 1rem;
  padding: 1rem 1.2rem;
  border-radius: 32px;
  background:
    radial-gradient(circle at top left, rgba(224, 182, 108, 0.14), transparent 26%),
    radial-gradient(circle at bottom right, rgba(114, 214, 201, 0.12), transparent 22%),
    rgba(10, 13, 15, 0.92);
  border: 1px solid rgba(255, 227, 184, 0.16);
}

.shell-header h1 {
  margin: 0.4rem 0 0;
  font-size: clamp(1.7rem, 3vw, 2.8rem);
}

.shell-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.nav-link {
  padding: 0.7rem 1rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 227, 184, 0.15);
  color: var(--crepe-text);
  text-decoration: none;
  background: rgba(255, 246, 229, 0.02);
}

.nav-link.router-link-active {
  background: rgba(224, 182, 108, 0.15);
  border-color: rgba(224, 182, 108, 0.4);
}

.error-banner {
  margin-bottom: 1rem;
  padding: 0.9rem 1rem;
  border-radius: 18px;
  border: 1px solid rgba(255, 137, 103, 0.32);
  background: rgba(112, 28, 17, 0.55);
  color: #ffd7ca;
}

.eyebrow {
  margin: 0;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-size: 0.68rem;
  color: var(--crepe-accent);
}
</style>
