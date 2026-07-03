<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Light History</p>
        <h3>历史光照数据</h3>
      </div>
      <p class="section-note">
        查看各设备的历史光照趋势 · 共 {{ totalPoints }} 个采样点
      </p>
    </header>

    <div class="stats-grid">
      <StatCard v-for="item in stats" :key="item.label" :stat="item" />
    </div>

    <PanelCard title="数据筛选" subtitle="选择设备和查看时段">
      <div class="filter-row">
        <div class="filter-group">
          <label>选择设备</label>
          <div class="device-selector">
            <button
              v-for="device in devices"
              :key="device.id"
              class="filter-chip"
              :class="{ active: selectedDeviceId === device.id }"
              @click="selectDevice(device.id)"
            >
              {{ device.deviceName }}
              <span class="chip-code">{{ device.deviceCode }}</span>
            </button>
          </div>
        </div>

        <div class="filter-group">
          <label>时间范围</label>
          <div class="device-selector">
            <button
              v-for="range in timeRanges"
              :key="range.value"
              class="filter-chip"
              :class="{ active: selectedRange === range.value }"
              @click="selectRange(range.value)"
            >
              {{ range.label }}
            </button>
          </div>
        </div>
      </div>
    </PanelCard>

    <div class="content-grid two-columns">
      <PanelCard title="光照趋势曲线" subtitle="选定设备与时段">
        <TrendLineChart v-if="filteredPoints.length" :points="filteredPoints" />
        <div v-else class="placeholder-box">该时段暂无数据</div>
      </PanelCard>

      <PanelCard title="数据摘要" subtitle="统计信息">
        <div v-if="summary" class="summary-grid">
          <div class="summary-box">
            <span>平均光照</span>
            <strong>{{ summary.avg }} lux</strong>
          </div>
          <div class="summary-box">
            <span>最高光照</span>
            <strong>{{ summary.max }} lux</strong>
          </div>
          <div class="summary-box">
            <span>最低光照</span>
            <strong>{{ summary.min }} lux</strong>
          </div>
          <div class="summary-box">
            <span>采样点数</span>
            <strong>{{ summary.count }}</strong>
          </div>
          <div class="summary-box">
            <span>开灯时长占比</span>
            <strong>{{ summary.lampOnRatio }}%</strong>
          </div>
          <div class="summary-box">
            <span>数据跨度</span>
            <strong>{{ summary.span }}</strong>
          </div>
        </div>
        <div v-else class="placeholder-box">请选择设备查看摘要</div>
      </PanelCard>
    </div>

    <PanelCard title="采样记录" subtitle="详细数据列表">
      <div class="toolbar-row">
        <span class="record-count">共 {{ filteredPoints.length }} 条记录</span>
      </div>
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>时间</th>
              <th>光照强度 (lux)</th>
              <th>路灯状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(point, idx) in pagedPoints" :key="idx">
              <td>{{ point.timestamp }}</td>
              <td>
                <span class="intensity-cell" :style="{ color: cellColor(point.lightIntensity) }">
                  {{ point.lightIntensity }}
                </span>
              </td>
              <td>
                <StatusBadge
                  :status="point.lampStatus === 'ON' ? 'success' : 'info'"
                  :text="point.lampStatus === 'ON' ? '开灯' : '关灯'"
                />
              </td>
            </tr>
            <tr v-if="!filteredPoints.length">
              <td colspan="3" class="table-empty">暂无数据</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="totalPages > 1" class="pagination-row">
        <button class="ghost-button" :disabled="currentPage <= 1" @click="currentPage--">
          上一页
        </button>
        <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
        <button class="ghost-button" :disabled="currentPage >= totalPages" @click="currentPage++">
          下一页
        </button>
      </div>
    </PanelCard>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import PanelCard from "@/components/PanelCard.vue";
import StatCard from "@/components/StatCard.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import TrendLineChart from "@/components/TrendLineChart.vue";
import { getLightHistory } from "@/services/lightService";
import type { DashboardStat, Device, LightHistoryPoint } from "@/types/models";
import { mockDevices } from "@/mock/data";

const PAGE_SIZE = 20;

const devices = ref<Device[]>([]);
const allHistory = ref<LightHistoryPoint[]>([]);
const selectedDeviceId = ref<number>(1);
const selectedRange = ref<number>(1);
const currentPage = ref(1);

const timeRanges = [
  { label: "近 24 小时", value: 1 },
  { label: "近 3 天", value: 3 },
  { label: "近 7 天", value: 7 },
];

const totalPoints = computed(() => allHistory.value.length);

const filteredPoints = computed(() => {
  const all = allHistory.value;
  if (!all.length) return [];

  const rangeHours = selectedRange.value * 24;
  // 估算有多少个点（每 10 分钟一个点）
  const pointsInRange = rangeHours * 6;
  return all.slice(-pointsInRange);
});

const pagedPoints = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE;
  return filteredPoints.value.slice(start, start + PAGE_SIZE);
});

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredPoints.value.length / PAGE_SIZE)),
);

const summary = computed(() => {
  const pts = filteredPoints.value;
  if (!pts.length) return null;

  const intensities = pts.map((p) => p.lightIntensity);
  const avg = Math.round(intensities.reduce((a, b) => a + b, 0) / intensities.length);
  const max = Math.max(...intensities);
  const min = Math.min(...intensities);
  const lampOnCount = pts.filter((p) => p.lampStatus === "ON").length;
  const lampOnRatio = Math.round((lampOnCount / pts.length) * 100);

  const firstTs = pts[0].timestamp;
  const lastTs = pts[pts.length - 1].timestamp;
  const span = pts.length > 1 ? `${firstTs} ~ ${lastTs}` : firstTs;

  return { avg, max, min, count: pts.length, lampOnRatio, span };
});

const stats = computed<DashboardStat[]>(() => {
  const s = summary.value;
  if (!s) {
    return [
      { label: "选择设备", value: "-", helper: "请从上方选择" },
      { label: "数据范围", value: "-", helper: "-" },
      { label: "平均光照", value: "-", helper: "-" },
      { label: "采样点数", value: "-", helper: "-" },
    ];
  }
  const device = devices.value.find((d) => d.id === selectedDeviceId.value);
  return [
    { label: "当前设备", value: device?.deviceName ?? "-", helper: device?.deviceCode ?? "" },
    { label: "时间范围", value: `${selectedRange.value} 天`, helper: "可切换时段" },
    { label: "平均光照", value: `${s.avg} lux`, helper: "选定范围内" },
    { label: "采样点数", value: String(s.count), helper: "每 10 分钟一条" },
  ];
});

function cellColor(val: number): string {
  if (val < 80) return "#fca5a5";
  if (val < 180) return "#fde68a";
  if (val < 300) return "#86efac";
  return "#7dd3fc";
}

async function selectDevice(id: number) {
  selectedDeviceId.value = id;
  currentPage.value = 1;
  allHistory.value = await getLightHistory(id);
}

function selectRange(range: number) {
  selectedRange.value = range;
  currentPage.value = 1;
}

onMounted(async () => {
  devices.value = structuredClone(mockDevices);
  allHistory.value = await getLightHistory(selectedDeviceId.value);
});
</script>

<style scoped>
.filter-row {
  display: grid;
  gap: 16px;
}

.filter-group label {
  display: block;
  margin-bottom: 8px;
  color: #94a3b8;
  font-size: 13px;
}

.device-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 10px;
  color: #cbd5e1;
  font-size: 14px;
  background: rgba(8, 17, 31, 0.55);
  transition: 0.2s ease;
  cursor: pointer;
}

.filter-chip:hover {
  border-color: rgba(96, 165, 250, 0.45);
  background: rgba(15, 23, 42, 0.8);
}

.filter-chip.active {
  border-color: #60a5fa;
  color: #dbeafe;
  background: rgba(59, 130, 246, 0.2);
}

.chip-code {
  color: #64748b;
  font-size: 12px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.summary-box {
  display: grid;
  gap: 4px;
  padding: 16px;
  border-radius: 14px;
  background: rgba(8, 17, 31, 0.55);
  text-align: center;
}

.summary-box span {
  color: #94a3b8;
  font-size: 13px;
}

.summary-box strong {
  font-size: 22px;
  color: #e2e8f0;
}

.record-count {
  color: #94a3b8;
  font-size: 13px;
}

.intensity-cell {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.pagination-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
}

.page-info {
  color: #94a3b8;
  font-size: 14px;
}

.ghost-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}
</style>
