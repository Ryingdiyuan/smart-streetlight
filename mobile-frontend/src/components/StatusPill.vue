<template>
  <span class="status-pill" :class="toneClass">
    <span class="status-dot"></span>
    {{ text }}
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  tone: "success" | "warning" | "danger" | "neutral";
  text: string;
}>();

const toneClass = computed(() => `status-pill-${props.tone}`);
</script>

<style scoped>
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid transparent;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: currentColor;
  box-shadow: 0 0 10px currentColor;
}

.status-pill-success {
  color: #2dd4a3;
  background: rgba(45, 212, 163, 0.12);
  border-color: rgba(45, 212, 163, 0.2);
}

.status-pill-warning {
  color: #ffb04d;
  background: rgba(255, 176, 77, 0.12);
  border-color: rgba(255, 176, 77, 0.2);
}

.status-pill-danger {
  color: #ff7d7d;
  background: rgba(255, 125, 125, 0.12);
  border-color: rgba(255, 125, 125, 0.2);
}

.status-pill-neutral {
  color: var(--text-secondary);
  background: rgba(148, 163, 184, 0.1);
  border-color: rgba(148, 163, 184, 0.14);
}
</style>
