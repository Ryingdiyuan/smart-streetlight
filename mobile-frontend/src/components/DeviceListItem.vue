<template>
  <article class="device-card">
    <div class="device-card-top">
      <div>
        <p class="device-code">{{ device.deviceCode }}</p>
        <h4>{{ device.deviceName }}</h4>
      </div>
      <StatusPill :tone="device.status === 'online' ? 'success' : 'danger'" :text="device.status === 'online' ? '在线' : '离线'" />
    </div>

    <div class="device-meta-grid">
      <span>位置：{{ device.location }}</span>
      <span>灯态：{{ device.lampStatus }}</span>
      <span>心跳：{{ device.lastHeartbeatAt }}</span>
    </div>

    <div class="device-card-actions">
      <button class="action-button action-button-soft" type="button" @click="$emit('view')">查看详情</button>
      <button
        v-if="canOperate"
        class="action-button"
        type="button"
        @click="$emit('toggle')"
      >
        {{ device.lampStatus === "ON" ? "一键关灯" : "一键开灯" }}
      </button>
    </div>
  </article>
</template>

<script setup lang="ts">
import StatusPill from "@/components/StatusPill.vue";
import type { Device } from "@/types/models";

defineProps<{
  device: Device;
  canOperate?: boolean;
}>();

defineEmits<{
  view: [];
  toggle: [];
}>();
</script>

<style scoped>
.device-card {
  display: grid;
  gap: 14px;
  border-radius: 22px;
  padding: 16px;
  background: var(--surface-subtle);
  border: 1px solid var(--border-soft);
}

.device-card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.device-code {
  margin: 0 0 4px;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
}

.device-card h4 {
  margin: 0;
  font-size: 17px;
  color: var(--text-primary);
}

.device-meta-grid {
  display: grid;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.device-card-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
</style>
