<template>
  <article class="card panel-card">
    <div v-if="title || subtitle" class="panel-header">
      <h4>{{ title }}</h4>
      <span>{{ subtitle }}</span>
    </div>
    <slot />
  </article>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title?: string;
    subtitle?: string;
  }>(),
  {
    title: "",
    subtitle: "",
  },
);
</script>
