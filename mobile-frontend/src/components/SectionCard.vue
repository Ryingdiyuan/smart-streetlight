<template>
  <section class="section-card">
    <header v-if="title || subtitle" class="section-card-header">
      <div>
        <h3 v-if="title">{{ title }}</h3>
        <p v-if="subtitle">{{ subtitle }}</p>
      </div>
      <slot name="actions" />
    </header>
    <div class="section-card-body">
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title?: string;
  subtitle?: string;
}>();
</script>

<style scoped>
.section-card {
  border-radius: 24px;
  padding: 16px;
  background: var(--surface-panel);
  border: 1px solid var(--border-soft);
  box-shadow: var(--soft-shadow);
}

.section-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.section-card-header h3,
.section-card-header p {
  margin: 0;
}

.section-card-header h3 {
  font-size: 15px;
  color: var(--text-primary);
}

.section-card-header p {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.section-card-body {
  display: grid;
  gap: 12px;
}
</style>
