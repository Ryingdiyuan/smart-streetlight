<template>
  <div class="page-stack">
    <button class="chip-button back-button" type="button" @click="router.back()">返回上一页</button>

    <div v-if="loading" class="mobile-skeleton-card device-hero-skeleton"></div>

    <template v-else-if="device">
      <SectionCard>
        <div class="device-hero">
          <div>
            <p>{{ device.deviceCode }}</p>
            <h2>{{ device.deviceName }}</h2>
            <span>{{ device.location }}</span>
          </div>
          <StatusPill :tone="device.status === 'online' ? 'success' : 'danger'" :text="device.status === 'online' ? '在线' : '离线'" />
        </div>

        <div class="metric-strip">
          <div>
            <span>当前光照</span>
            <strong>{{ device.currentLightIntensity }}</strong>
          </div>
          <div>
            <span>路灯状态</span>
            <strong>{{ device.lampStatus }}</strong>
          </div>
          <div>
            <span>最近心跳</span>
            <strong>{{ device.lastHeartbeatAt }}</strong>
          </div>
        </div>

        <div v-if="canOperateDevices" class="device-actions">
          <button class="action-button" type="button" @click="sendCommand('TURN_ON')">开灯</button>
          <button class="action-button action-button-soft" type="button" @click="sendCommand('TURN_OFF')">关灯</button>
        </div>
      </SectionCard>

      <SectionCard title="阈值配置" subtitle="移动端可快速调整建议值">
        <div class="threshold-grid">
          <label>
            <span>低阈值</span>
            <input v-model.number="threshold.lowThreshold" type="number" />
          </label>
          <label>
            <span>高阈值</span>
            <input v-model.number="threshold.highThreshold" type="number" />
          </label>
          <label class="switch-row">
            <span>启用阈值</span>
            <input v-model="threshold.enabled" type="checkbox" />
          </label>
        </div>
        <button v-if="canOperateDevices" class="action-button" type="button" @click="saveThreshold">保存阈值</button>
      </SectionCard>

      <SectionCard title="近 24 条趋势" subtitle="便于现场快速判断环境变化">
        <LightTrendChart :points="device.history" />
      </SectionCard>

      <SectionCard title="最近控制记录">
        <div class="compact-list">
          <article v-for="log in device.commandLogs" :key="log.id" class="compact-item">
            <div class="compact-item-top">
              <strong>{{ log.command }}</strong>
              <StatusPill
                :tone="log.result === 'success' ? 'success' : log.result === 'failed' ? 'danger' : 'warning'"
                :text="log.result"
              />
            </div>
            <p>{{ log.source === "manual" ? "人工控制" : "自动控制" }}</p>
            <span>{{ log.createdAt }}</span>
          </article>
          <p v-if="!device.commandLogs.length" class="placeholder-text">暂无控制记录。</p>
        </div>
      </SectionCard>

      <SectionCard title="最近告警">
        <div class="compact-list">
          <article v-for="alarm in device.alarms" :key="alarm.id" class="compact-item">
            <div class="compact-item-top">
              <strong>{{ alarm.alarmType }}</strong>
              <StatusPill :tone="alarm.handled ? 'neutral' : 'warning'" :text="alarm.handled ? '已处理' : '待处理'" />
            </div>
            <p>{{ alarm.alarmContent }}</p>
            <span>{{ alarm.createdAt }}</span>
          </article>
          <p v-if="!device.alarms.length" class="placeholder-text">暂无告警。</p>
        </div>
      </SectionCard>
    </template>

    <p v-else class="placeholder-text">{{ errorMessage || "设备不存在。" }}</p>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import LightTrendChart from "@/components/LightTrendChart.vue";
import SectionCard from "@/components/SectionCard.vue";
import StatusPill from "@/components/StatusPill.vue";
import { getDeviceDetail, sendDeviceCommand, updateDeviceThreshold } from "@/services/api/deviceService";
import { can } from "@/services/permissions";
import type { DeviceDetail, ThresholdConfig } from "@/types/models";

const route = useRoute();
const router = useRouter();
const loading = ref(true);
const errorMessage = ref("");
const device = ref<DeviceDetail | null>(null);
const canOperateDevices = can("operateDevices");

const threshold = reactive<ThresholdConfig>({
  deviceId: "",
  lowThreshold: 0,
  highThreshold: 0,
  enabled: true,
});

function getErrorMessage(error: unknown) {
  if (!(error instanceof Error)) {
    return "操作失败，请稍后重试。";
  }
  try {
    const parsed = JSON.parse(error.message) as { detail?: string };
    return parsed.detail || error.message;
  } catch {
    return error.message;
  }
}

async function loadDetail() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const result = await getDeviceDetail(Number(route.params.id));
    device.value = result;
    if (result) {
      Object.assign(threshold, result.threshold);
    }
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    loading.value = false;
  }
}

async function saveThreshold() {
  if (!device.value) {
    return;
  }
  try {
    await updateDeviceThreshold(device.value.id, threshold);
    await loadDetail();
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  }
}

async function sendCommand(command: "TURN_ON" | "TURN_OFF") {
  if (!device.value) {
    return;
  }
  try {
    await sendDeviceCommand(device.value.id, command);
    await loadDetail();
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  }
}

onMounted(loadDetail);
</script>

<style scoped>
.device-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.device-hero p,
.device-hero h2,
.device-hero span {
  margin: 0;
}

.device-hero p {
  font-size: 11px;
  color: var(--accent);
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.device-hero h2 {
  margin-top: 6px;
  font-size: 24px;
}

.device-hero span {
  display: inline-block;
  margin-top: 8px;
  color: var(--text-secondary);
}

.metric-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.metric-strip div {
  display: grid;
  gap: 6px;
  padding: 14px;
  border-radius: 18px;
  background: var(--surface-inner);
  border: 1px solid var(--border-soft);
}

.metric-strip span {
  font-size: 11px;
  color: var(--text-secondary);
}

.metric-strip strong {
  font-size: 14px;
}

.device-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.threshold-grid {
  display: grid;
  gap: 12px;
}

.threshold-grid label {
  display: grid;
  gap: 8px;
}

.switch-row {
  grid-template-columns: 1fr auto;
  align-items: center;
}

.device-hero-skeleton {
  height: 140px;
}
</style>
