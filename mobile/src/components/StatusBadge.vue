<template>
  <view class="status-badge" :class="[typeClass, sizeClass]">
    <text class="badge-dot"></text>
    <text class="badge-text"><slot /></text>
  </view>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    type?: "online" | "offline" | "on" | "off" | "handled" | "info" | "warn" | "critical" | "success" | "failed" | "pending";
    size?: "sm" | "md";
  }>(),
  { type: "offline", size: "sm" },
);

const typeClass = computed(() => `badge-${props.type}`);
const sizeClass = computed(() => `size-${props.size}`);
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  gap: 4px;
}

.size-md {
  padding: 4px 14px;
  font-size: 14px;
  border-radius: 14px;
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.badge-online,
.badge-success,
.badge-handled {
  background: rgba(0, 200, 83, 0.15);
  color: #00c853;
}
.badge-online .badge-dot,
.badge-success .badge-dot,
.badge-handled .badge-dot {
  background: #00c853;
}

.badge-offline,
.badge-failed {
  background: rgba(255, 82, 82, 0.15);
  color: #ff5252;
}
.badge-offline .badge-dot,
.badge-failed .badge-dot {
  background: #ff5252;
}

.badge-on,
.badge-warn {
  background: rgba(255, 193, 7, 0.15);
  color: #ffc107;
}
.badge-on .badge-dot,
.badge-warn .badge-dot {
  background: #ffc107;
}

.badge-off {
  background: rgba(158, 180, 200, 0.15);
  color: #9fb4c8;
}
.badge-off .badge-dot {
  background: #9fb4c8;
}

.badge-info {
  background: rgba(56, 213, 255, 0.15);
  color: #38d5ff;
}
.badge-info .badge-dot {
  background: #38d5ff;
}

.badge-critical {
  background: rgba(255, 23, 68, 0.15);
  color: #ff1744;
}
.badge-critical .badge-dot {
  background: #ff1744;
}

.badge-pending {
  background: rgba(158, 180, 200, 0.15);
  color: #9fb4c8;
}
.badge-pending .badge-dot {
  background: #9fb4c8;
}
</style>
