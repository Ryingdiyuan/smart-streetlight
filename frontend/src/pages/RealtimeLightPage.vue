<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Real‑time Monitor</p>
        <h3>实时光照监测</h3>
      </div>
      <p class="section-note">
        每 5 秒自动刷新 · 聚合真实设备与最新光照上报
        <span class="auto-refresh-dot" :class="{ refreshing }"></span>
      </p>
    </header>

    <div class="stats-grid">
      <StatCard v-for="item in stats" :key="item.label" :stat="item" />
    </div>

    <div class="device-grid">
      <article
        v-for="reading in readings"
        :key="reading.deviceId"
        class="card light-card"
        :class="{ 'is-offline-card': reading.status === 'offline' }"
      >
        <div class="light-card-header">
          <div>
            <strong>{{ reading.deviceName }}</strong>
            <p class="light-card-meta">
              {{ reading.deviceCode }} · {{ reading.location }}
            </p>
          </div>
          <div class="light-card-badges">
            <StatusBadge
              :status="reading.status"
              :text="reading.status === 'online' ? '在线' : '离线'"
            />
            <StatusBadge
              :status="reading.lampStatus === 'ON' ? 'success' : 'info'"
              :text="reading.lampStatus === 'ON' ? '开灯' : '关灯'"
            />
          </div>
        </div>

        <div class="light-intensity-area">
          <div class="light-value-row">
            <span
              class="light-value"
              :style="{ color: intensityColor(reading.lightIntensity) }"
            >
              {{ reading.lightIntensity }}
            </span>
            <span class="light-unit">lux</span>
          </div>
          <div class="light-bar-track">
            <div
              class="light-bar-fill"
              :style="{
                width: barWidth(reading.lightIntensity),
                background: intensityGradient(reading.lightIntensity),
              }"
            ></div>
          </div>
          <div class="light-bar-labels">
            <span>0</span>
            <span>200</span>
            <span>400</span>
          </div>
        </div>

        <div class="light-card-footer">
          <span class="update-label">最后更新</span>
          <span class="update-time">{{ reading.updatedAt }}</span>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

import StatCard from "@/components/StatCard.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import { getRealtimeLightReadings } from "@/services/lightService";
import type { DashboardStat, RealtimeLightReading } from "@/types/models";

const readings = ref<RealtimeLightReading[]>([]);
const refreshing = ref(false);

let timer: ReturnType<typeof setInterval> | null = null;

const stats = computed<DashboardStat[]>(() => {
  const items = readings.value;
  const total = items.length;
  const intensities = items
    .filter((d) => d.status === "online")
    .map((d) => d.lightIntensity);
  const avg =
    intensities.length > 0
      ? Math.round(intensities.reduce((a, b) => a + b, 0) / intensities.length)
      : 0;
  const max = intensities.length > 0 ? Math.max(...intensities) : 0;
  const lampOn = items.filter((d) => d.lampStatus === "ON").length;

  return [
    { label: "监测设备", value: String(total), helper: "全部路灯设备" },
    { label: "平均光照", value: `${avg} lux`, helper: "在线设备均值" },
    { label: "最高光照", value: `${max} lux`, helper: "当前峰值" },
    { label: "开灯数量", value: String(lampOn), helper: `共 ${total} 台` },
  ];
});

function intensityColor(val: number): string {
  if (val < 80) return "#dc2626";
  if (val < 180) return "#ca8a04";
  if (val < 300) return "#16a34a";
  return "#0284c7";
}

function barWidth(val: number): string {
  const pct = Math.min((val / 450) * 100, 100);
  return `${pct}%`;
}

function intensityGradient(val: number): string {
  if (val < 80) return "linear-gradient(90deg, #ef4444, #f97316)";
  if (val < 180) return "linear-gradient(90deg, #ca8a04, #facc15)";
  if (val < 300) return "linear-gradient(90deg, #16a34a, #4ade80)";
  return "linear-gradient(90deg, #0284c7, #38bdf8)";
}

async function fetchReadings() {
  refreshing.value = true;
  try {
    readings.value = await getRealtimeLightReadings();
  } finally {
    refreshing.value = false;
  }
}

onMounted(() => {
  fetchReadings();
  timer = setInterval(fetchReadings, 5000);
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>

<style scoped>
.device-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.light-card {
  padding: 20px;
  display: grid;
  gap: 16px;
  transition: border-color 0.3s ease;
  border-color: var(--border-soft);
}

.light-card:hover {
  border-color: var(--border-bright);
}

.is-offline-card {
  border-color: rgba(239, 68, 68, 0.32);
}

.light-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.light-card-header strong {
  font-size: 16px;
  color: var(--text-main);
}

.light-card-meta {
  margin: 4px 0 0;
  color: var(--text-muted);
  font-size: 13px;
}

.light-card-badges {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.light-intensity-area {
  display: grid;
  gap: 6px;
}

.light-value-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.light-value {
  font-size: 42px;
  font-weight: 700;
  line-height: 1;
  transition: color 0.4s ease;
  font-variant-numeric: tabular-nums;
}

.light-unit {
  color: var(--text-muted);
  font-size: 16px;
}

.light-bar-track {
  height: 10px;
  border-radius: 999px;
  background: rgba(100, 116, 139, 0.28);
  overflow: hidden;
}

.light-bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.6s ease, background 0.6s ease;
}

.light-bar-labels {
  display: flex;
  justify-content: space-between;
  color: var(--text-muted);
  font-size: 11px;
}

.light-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--border-soft);
  color: var(--text-muted);
  font-size: 13px;
}

.update-label {
  color: var(--text-muted);
}

.update-time {
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.auto-refresh-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-left: 6px;
  border-radius: 50%;
  background: #22c55e;
  vertical-align: middle;
  transition: opacity 0.3s;
}

.auto-refresh-dot.refreshing {
  animation: pulse-dot 0.6s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}
</style>
