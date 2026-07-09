<template>
  <view class="alarm-item">
    <view class="alarm-header">
      <view class="alarm-type-row">
        <StatusBadge :type="levelBadgeType" size="sm">{{ alarm.alarmLevel }}</StatusBadge>
        <text class="alarm-type">{{ alarmTypeLabel }}</text>
      </view>
      <StatusBadge v-if="alarm.handled" type="handled" size="sm">已处理</StatusBadge>
      <StatusBadge v-else type="warn" size="sm">未处理</StatusBadge>
    </view>
    <text class="alarm-content">{{ alarm.alarmContent }}</text>
    <view class="alarm-footer">
      <text class="alarm-time">{{ alarm.createdAt }}</text>
      <view
        v-if="!alarm.handled && showHandle"
        class="handle-btn"
        @tap.stop="onHandle"
      >
        确认
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { AlarmRecord } from "@/types/models";
import StatusBadge from "@/components/StatusBadge.vue";

const props = withDefaults(
  defineProps<{
    alarm: AlarmRecord;
    showHandle?: boolean;
  }>(),
  { showHandle: true },
);

const emit = defineEmits<{
  (e: "handle", alarm: AlarmRecord): void;
}>();

const alarmTypeLabel = computed(() => {
  const map: Record<string, string> = {
    DEVICE_OFFLINE: "设备离线",
    LIGHT_ABNORMAL: "光照异常",
    COMMAND_FAILED: "命令失败",
  };
  return map[props.alarm.alarmType] || props.alarm.alarmType;
});

const levelBadgeType = computed(() => {
  const level = props.alarm.alarmLevel;
  if (level === "CRITICAL") return "critical";
  if (level === "WARN") return "warn";
  return "info";
});

function onHandle() {
  emit("handle", props.alarm);
}
</script>

<style scoped>
.alarm-item {
  background: rgba(10, 26, 45, 0.8);
  border: 1px solid rgba(56, 213, 255, 0.1);
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 10px;
}

.alarm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.alarm-type-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.alarm-type {
  font-size: 14px;
  color: #e8edf3;
  font-weight: 500;
}

.alarm-content {
  font-size: 13px;
  color: #9fb4c8;
  line-height: 1.5;
  margin-bottom: 8px;
  display: block;
}

.alarm-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alarm-time {
  font-size: 11px;
  color: #6a8299;
}

.handle-btn {
  padding: 4px 14px;
  border-radius: 14px;
  background: rgba(56, 213, 255, 0.15);
  color: #38d5ff;
  font-size: 12px;
  border: 1px solid rgba(56, 213, 255, 0.3);
}
</style>
