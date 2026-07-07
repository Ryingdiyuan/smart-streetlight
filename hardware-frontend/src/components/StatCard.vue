<template>
  <article class="card stat-card">
    <p class="muted-label">{{ stat.label }}</p>
    <strong>{{ stat.value }}</strong>
    <span>{{ stat.helper }}</span>
  </article>
</template>

<script setup lang="ts">
import type { DashboardStat } from "@/types/models";

defineProps<{
  stat: DashboardStat;
}>();
</script>
