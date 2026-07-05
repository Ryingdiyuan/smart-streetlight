<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Light History</p>
        <h3>历史光照数据</h3>
      </div>
      <p class="section-note">
        查看各设备的历史光照趋势 · 当前范围内共 {{ totalPoints }} 个原始采样点
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
      <PanelCard title="光照趋势曲线" :subtitle="`选定设备与时段 · ${aggregationLabel}`">
        <div v-if="loading" class="placeholder-box">正在加载并聚合历史数据...</div>
        <TrendLineChart v-else-if="chartPoints.length" :points="chartPoints" />
        <div v-else class="placeholder-box">该时段暂无数据</div>
      </PanelCard>

      <PanelCard title="数据摘要" subtitle="基于当前范围内原始数据统计">
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

    <PanelCard title="趋势采样记录" :subtitle="aggregationLabel">
      <div class="toolbar-row">
        <span class="record-count">共 {{ aggregatedPoints.length }} 个聚合时间段</span>
      </div>
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>时间段</th>
              <th>平均光照 (lux)</th>
              <th>范围</th>
              <th>开灯占比</th>
              <th>代表状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(point, idx) in pagedPoints" :key="idx">
              <td>{{ point.spanLabel }}</td>
              <td>
                <span class="intensity-cell" :style="{ color: cellColor(point.lightIntensity) }">
                  {{ point.lightIntensity }}
                </span>
              </td>
              <td>{{ point.min }} ~ {{ point.max }}</td>
              <td>{{ point.lampOnRatio }}%</td>
              <td>
                <StatusBadge
                  :status="point.lampStatus === 'ON' ? 'success' : 'info'"
                  :text="point.lampStatus === 'ON' ? '开灯' : '关灯'"
                />
              </td>
            </tr>
            <tr v-if="!aggregatedPoints.length">
              <td colspan="5" class="table-empty">暂无数据</td>
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
import { getDeviceList } from "@/services/deviceService";
import TrendLineChart from "@/components/TrendLineChart.vue";
import { getLightHistory } from "@/services/lightService";
import type { DashboardStat, Device, LightHistoryPoint } from "@/types/models";

const PAGE_SIZE = 20;

interface TimeRangeOption {
  label: string;
  value: number;
  bucketHours: number;
  limit: number;
}

interface AggregatedHistoryPoint extends LightHistoryPoint {
  min: number;
  max: number;
  sampleCount: number;
  lampOnRatio: number;
  spanLabel: string;
}

const devices = ref<Device[]>([]);
const rawHistory = ref<LightHistoryPoint[]>([]);
const selectedDeviceId = ref<number>(1);
const selectedRange = ref<number>(1);
const currentPage = ref(1);
const loading = ref(false);

const timeRanges: TimeRangeOption[] = [
  { label: "近 24 小时", value: 1, bucketHours: 1, limit: 240 },
  { label: "近 3 天", value: 3, bucketHours: 3, limit: 720 },
  { label: "近 7 天", value: 7, bucketHours: 12, limit: 1500 },
];

const totalPoints = computed(() => rawHistory.value.length);

const activeRange = computed(
  () => timeRanges.find((range) => range.value === selectedRange.value) ?? timeRanges[0],
);

const aggregationLabel = computed(() => `按 ${activeRange.value.bucketHours} 小时聚合展示`);

const aggregatedPoints = computed<AggregatedHistoryPoint[]>(() =>
  aggregateHistory(rawHistory.value, activeRange.value.bucketHours),
);

const chartPoints = computed<LightHistoryPoint[]>(() =>
  aggregatedPoints.value.map((point) => ({
    timestamp: point.timestamp,
    lightIntensity: point.lightIntensity,
    lampStatus: point.lampStatus,
  })),
);

const pagedPoints = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE;
  return aggregatedPoints.value.slice(start, start + PAGE_SIZE);
});

const totalPages = computed(() =>
  Math.max(1, Math.ceil(aggregatedPoints.value.length / PAGE_SIZE)),
);

const summary = computed(() => {
  const pts = rawHistory.value;
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
      { label: "聚合粒度", value: "-", helper: "-" },
    ];
  }
  const device = devices.value.find((d) => d.id === selectedDeviceId.value);
  return [
    { label: "当前设备", value: device?.deviceName ?? "-", helper: device?.deviceCode ?? "" },
    { label: "时间范围", value: `${selectedRange.value} 天`, helper: "可切换时段" },
    { label: "平均光照", value: `${s.avg} lux`, helper: "选定范围内" },
    { label: "聚合粒度", value: `${activeRange.value.bucketHours} 小时`, helper: `${s.count} 个原始点` },
  ];
});

function cellColor(val: number): string {
  if (val < 80) return "#fca5a5";
  if (val < 180) return "#fde68a";
  if (val < 300) return "#86efac";
  return "#7dd3fc";
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

function formatApiDateTime(value: Date): string {
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}T${pad(value.getHours())}:${pad(value.getMinutes())}:${pad(value.getSeconds())}`;
}

function parsePointDate(value: string): Date {
  return new Date(value.replace(" ", "T"));
}

function formatBucketText(value: Date): string {
  return `${pad(value.getMonth() + 1)}-${pad(value.getDate())} ${pad(value.getHours())}:00`;
}

function formatSpanLabel(start: Date, end: Date): string {
  return `${formatBucketText(start)} ~ ${pad(end.getHours())}:${pad(end.getMinutes())}`;
}

function aggregateHistory(points: LightHistoryPoint[], bucketHours: number): AggregatedHistoryPoint[] {
  if (!points.length) {
    return [];
  }

  const bucketMs = bucketHours * 60 * 60 * 1000;
  const buckets = new Map<number, AggregatedHistoryPoint>();

  for (const point of points) {
    const date = parsePointDate(point.timestamp);
    const bucketStartMs = Math.floor(date.getTime() / bucketMs) * bucketMs;
    const bucketStart = new Date(bucketStartMs);
    const bucketEnd = new Date(bucketStartMs + bucketMs - 1);
    const existing = buckets.get(bucketStartMs);

    if (!existing) {
      buckets.set(bucketStartMs, {
        timestamp: formatBucketText(bucketStart),
        lightIntensity: point.lightIntensity,
        lampStatus: point.lampStatus,
        min: point.lightIntensity,
        max: point.lightIntensity,
        sampleCount: 1,
        lampOnRatio: point.lampStatus === "ON" ? 100 : 0,
        spanLabel: formatSpanLabel(bucketStart, bucketEnd),
      });
      continue;
    }

    const nextCount = existing.sampleCount + 1;
    const lampOnCount = Math.round((existing.lampOnRatio / 100) * existing.sampleCount) + (point.lampStatus === "ON" ? 1 : 0);
    existing.lightIntensity = Math.round(
      (existing.lightIntensity * existing.sampleCount + point.lightIntensity) / nextCount,
    );
    existing.min = Math.min(existing.min, point.lightIntensity);
    existing.max = Math.max(existing.max, point.lightIntensity);
    existing.sampleCount = nextCount;
    existing.lampOnRatio = Math.round((lampOnCount / nextCount) * 100);
    existing.lampStatus = existing.lampOnRatio >= 50 ? "ON" : "OFF";
  }

  return Array.from(buckets.entries())
    .sort((left, right) => left[0] - right[0])
    .map(([, value]) => value);
}

async function loadHistory() {
  loading.value = true;
  currentPage.value = 1;
  const now = new Date();
  const start = new Date(now.getTime() - selectedRange.value * 24 * 60 * 60 * 1000);
  try {
    rawHistory.value = await getLightHistory(selectedDeviceId.value, {
      startTime: formatApiDateTime(start),
      endTime: formatApiDateTime(now),
      limit: activeRange.value.limit,
    });
  } finally {
    loading.value = false;
  }
}

async function selectDevice(id: number) {
  selectedDeviceId.value = id;
  await loadHistory();
}

async function selectRange(range: number) {
  selectedRange.value = range;
  await loadHistory();
}

onMounted(async () => {
  devices.value = await getDeviceList();
  if (!devices.value.length) {
    rawHistory.value = [];
    return;
  }

  selectedDeviceId.value = devices.value[0].id;
  await loadHistory();
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
