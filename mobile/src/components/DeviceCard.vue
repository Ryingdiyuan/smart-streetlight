<template>
  <view class="device-card" @tap="onTap">
    <view class="card-header">
      <text class="device-name">{{ device.deviceName }}</text>
      <StatusBadge :type="device.status === 'online' ? 'online' : 'offline'">
        {{ device.status === "online" ? "在线" : "离线" }}
      </StatusBadge>
    </view>
    <view class="card-body">
      <view class="info-row">
        <text class="info-label">编号</text>
        <text class="info-value">{{ device.deviceCode }}</text>
      </view>
      <view class="info-row">
        <text class="info-label">位置</text>
        <text class="info-value">{{ device.location }}</text>
      </view>
    </view>
    <view class="card-footer">
      <StatusBadge :type="device.lampStatus === 'ON' ? 'on' : 'off'" size="sm">
        {{ device.lampStatus === "ON" ? "灯亮" : "灯灭" }}
      </StatusBadge>
      <text class="heartbeat">{{ device.lastHeartbeatAt }}</text>
    </view>
    <view v-if="selected !== undefined" class="select-overlay" :class="{ selected }">
      <view class="checkbox" :class="{ checked: selected }">
        <text v-if="selected" class="check-mark">✓</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import type { Device } from "@/types/models";
import StatusBadge from "@/components/StatusBadge.vue";

defineProps<{
  device: Device;
  selected?: boolean;
}>();

const emit = defineEmits<{
  (e: "tap"): void;
}>();

function onTap() {
  emit("tap");
}
</script>

<style scoped>
.device-card {
  background: rgba(10, 26, 45, 0.8);
  border: 1px solid rgba(56, 213, 255, 0.1);
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 10px;
  position: relative;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.device-name {
  font-size: 16px;
  font-weight: 600;
  color: #e8edf3;
}

.card-body {
  margin-bottom: 10px;
}

.info-row {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
}

.info-label {
  font-size: 13px;
  color: #6a8299;
  width: 40px;
  flex-shrink: 0;
}

.info-value {
  font-size: 13px;
  color: #9fb4c8;
  flex: 1;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.heartbeat {
  font-size: 11px;
  color: #6a8299;
}

.select-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(56, 213, 255, 0.05);
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  padding: 10px;
  pointer-events: none;
}

.select-overlay.selected {
  background: rgba(56, 213, 255, 0.08);
}

.checkbox {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid #9fb4c8;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
}

.checkbox.checked {
  background: #38d5ff;
  border-color: #38d5ff;
}

.check-mark {
  color: #07111d;
  font-size: 14px;
  font-weight: 700;
}
</style>
