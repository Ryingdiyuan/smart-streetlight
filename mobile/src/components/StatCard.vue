<template>
  <view class="stat-card" @tap="onClick">
    <text class="stat-label">{{ label }}</text>
    <text class="stat-value" :style="{ color: valueColor }">{{ value }}</text>
    <text v-if="helper" class="stat-helper">{{ helper }}</text>
  </view>
</template>

<script setup lang="ts">
defineProps<{
  label: string;
  value: string | number;
  helper?: string;
  valueColor?: string;
}>();

const emit = defineEmits<{
  (e: "click"): void;
}>();

function onClick() {
  emit("click");
}
</script>

<style scoped>
.stat-card {
  background: rgba(10, 26, 45, 0.8);
  border: 1px solid rgba(56, 213, 255, 0.15);
  border-radius: 12px;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.stat-label {
  font-size: 13px;
  color: #9fb4c8;
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #38d5ff;
  line-height: 1.2;
}

.stat-helper {
  font-size: 11px;
  color: #6a8299;
  text-align: center;
}
</style>
