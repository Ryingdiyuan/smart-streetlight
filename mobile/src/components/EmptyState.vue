<template>
  <view class="empty-state">
    <text class="empty-icon">{{ icon }}</text>
    <text class="empty-text">{{ message }}</text>
  </view>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    message?: string;
    icon?: string;
  }>(),
  { message: "暂无数据", icon: "📭" },
);
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  gap: 12px;
}

.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.empty-text {
  font-size: 14px;
  color: #6a8299;
}
</style>
