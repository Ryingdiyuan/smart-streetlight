<template>
  <article class="metric-card">
    <p class="metric-label">{{ stat.label }}</p>
    <strong class="metric-value">{{ stat.value }}</strong>
    <span class="metric-helper">{{ stat.helper }}</span>
  </article>
</template>

<script setup lang="ts">
import type { DashboardStat } from "@/types/models";

defineProps<{
  stat: DashboardStat;
}>();
</script>

<style scoped>
.metric-card {
  display: grid;
  gap: 6px;
  padding: 16px;
  border-radius: 22px;
  background: var(--surface-panel-alt);
  border: 1px solid var(--border-soft);
  box-shadow: var(--soft-shadow);
}

.metric-label {
  margin: 0;
  font-size: 12px;
  color: var(--text-secondary);
}

.metric-value {
  font-size: 28px;
  line-height: 1;
  color: var(--text-primary);
}

.metric-helper {
  font-size: 12px;
  color: var(--text-muted);
}
</style>
