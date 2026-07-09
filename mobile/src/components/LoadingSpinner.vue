<template>
  <view class="loading-spinner" :class="{ inline, overlay: !inline }">
    <view class="spinner"></view>
    <text v-if="text" class="loading-text">{{ text }}</text>
  </view>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    text?: string;
    inline?: boolean;
  }>(),
  { inline: false },
);
</script>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.loading-spinner.overlay {
  padding: 40px 0;
  min-height: 200px;
}

.loading-spinner.inline {
  padding: 20px 0;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(56, 213, 255, 0.2);
  border-top-color: #38d5ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 14px;
  color: #9fb4c8;
}
</style>
