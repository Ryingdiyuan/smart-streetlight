<template>
  <section class="bigscreen-dashboard">
    <header class="screen-header">
      <div class="header-wing"></div>
      <div class="title-block">
        <span>Smart Streetlight Dashboard</span>
        <h1>智慧路灯总览大屏</h1>
      </div>
      <div class="header-clock">
        <strong>{{ currentTime }}</strong>
        <span>{{ currentDate }}</span>
      </div>
      <div v-if="isLoading || loadError || historyLoading" class="data-state" :class="{ warning: loadError }">
        {{ stateText }}
      </div>
    </header>

    <main class="screen-grid">
      <aside class="screen-column left-column">
        <section class="screen-panel overview-panel">
          <PanelTitle title="核心概览" />
          <div class="ring-row">
            <div v-for="item in topMetrics" :key="item.label" class="metric-ring">
              <div class="ring-core">{{ item.value }}</div>
              <span>{{ item.label }}</span>
            </div>
          </div>
          <div class="mini-stat-grid">
            <div v-for="item in compactStats" :key="item.label" class="mini-stat">
              <strong>{{ item.value }}</strong>
              <span>{{ item.label }}</span>
            </div>
          </div>
        </section>

        <section class="screen-panel status-panel">
          <PanelTitle title="设备状态分布" />
          <div class="status-list">
            <div v-for="item in statusItems" :key="item.label" class="status-item">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <div class="status-bar">
                <i :style="{ width: item.percent + '%' }"></i>
              </div>
              <em>{{ item.percent }}%</em>
            </div>
          </div>
        </section>

        <section class="screen-panel focus-panel">
          <PanelTitle title="当前展示设备" />
          <div class="focus-card">
            <strong>{{ selectedDevice?.deviceName || "--" }}</strong>
            <span>{{ selectedDevice?.deviceCode || "--" }}</span>
            <div>
              <b :class="{ danger: selectedDevice?.status === 'offline' }">
                {{ deviceStatusText(selectedDevice?.status ?? "offline") }}
              </b>
              <b>{{ lampStatusText(selectedDevice?.lampStatus ?? "OFF") }}</b>
            </div>
            <p>{{ selectedDevice?.location || "--" }}</p>
          </div>
        </section>
      </aside>

      <section class="center-stage">
        <div class="city-map">
          <div class="road road-main"></div>
          <div class="road road-branch"></div>
          <div class="road road-cross"></div>
          <div class="district district-a"></div>
          <div class="district district-b"></div>
          <div class="district district-c"></div>
          <div class="route-line"></div>
          <button
            v-for="(device, index) in sceneDevices"
            :key="device.deviceCode"
            class="streetlight-node"
            :class="{
              'node-offline': device.status === 'offline',
              'node-on': device.lampStatus === 'ON',
              'node-selected': selectedDevice?.id === device.id,
            }"
            :style="nodeStyle(index)"
            type="button"
            @click="selectDevice(device)"
          >
            <i></i>
            <span></span>
          </button>

          <div class="selected-device">
            <small>当前展示设备</small>
            <strong>{{ selectedDevice?.deviceName || "--" }}</strong>
            <span>{{ selectedDevice?.deviceCode || "--" }} · {{ deviceStatusText(selectedDevice?.status ?? "offline") }}</span>
            <em>{{ selectedDevice?.location || "--" }}</em>
            <div class="selected-actions">
              <button type="button" @click="selectPreviousDevice">上一台</button>
              <button type="button" @click="selectNextDevice">下一台</button>
            </div>
          </div>
        </div>

        <div class="bottom-dock">
          <section class="dock-card rate-card">
            <PanelTitle title="开灯率" />
            <div class="rate-body">
              <strong>{{ lampRate }}%</strong>
              <span>{{ lampOnCount }} / {{ totalCount }}</span>
              <em>基于实时设备状态</em>
            </div>
          </section>

          <section class="dock-card table-card">
            <PanelTitle title="全部告警" />
            <div class="table-scroll">
              <table class="screen-table">
                <thead>
                  <tr>
                    <th>设备编号</th>
                    <th>设备位置</th>
                    <th>告警类型</th>
                    <th>告警内容</th>
                    <th>时间</th>
                    <th>状态</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="alarm in visibleAlarms"
                    :key="alarm.id"
                    :class="{ active: alarm.deviceId === selectedDevice?.deviceCode }"
                    @click="selectDeviceByCode(alarm.deviceId)"
                  >
                    <td>{{ alarm.deviceId }}</td>
                    <td>{{ locationForAlarm(alarm.deviceId) }}</td>
                    <td>{{ alarmTypeText(alarm.alarmType) }}</td>
                    <td>{{ alarm.alarmContent }}</td>
                    <td>{{ alarm.createdAt }}</td>
                    <td>{{ alarm.handled ? "已处理" : "待处理" }}</td>
                  </tr>
                  <tr v-if="!visibleAlarms.length">
                    <td colspan="6">当前暂无告警数据</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </section>

      <aside class="screen-column right-column">
        <section class="screen-panel device-panel">
          <PanelTitle title="设备快照" />
          <div class="device-list scroll-list">
            <button
              v-for="device in visibleDevices"
              :key="device.id"
              class="device-row"
              :class="{ active: selectedDevice?.id === device.id }"
              type="button"
              @click="selectDevice(device)"
            >
              <div>
                <strong>{{ device.deviceName }}</strong>
                <span>{{ device.deviceCode }} · {{ device.location }}</span>
              </div>
              <b :class="{ danger: device.status === 'offline' }">{{ deviceStatusText(device.status) }}</b>
            </button>
          </div>
        </section>

        <section class="screen-panel trend-panel">
          <PanelTitle title="当前设备光照" />
          <div class="trend-summary">
            <div>
              <span>最新光照</span>
              <strong>{{ latestLightIntensity }}</strong>
            </div>
            <div>
              <span>采样点</span>
              <strong>{{ selectedHistory.length }}</strong>
            </div>
          </div>
          <div class="bar-chart">
            <i v-for="item in trendBars" :key="item.label" :style="{ height: item.value + '%' }">
              <span>{{ item.label }}</span>
            </i>
          </div>
          <div class="history-list scroll-list">
            <div v-for="point in selectedHistory" :key="`${point.timestamp}-${point.lightIntensity}`" class="history-row">
              <span>{{ point.timestamp }}</span>
              <strong>{{ point.lightIntensity }}</strong>
              <b>{{ lampStatusText(point.lampStatus) }}</b>
            </div>
            <div v-if="!selectedHistory.length" class="empty-line">当前设备暂无光照历史</div>
          </div>
        </section>

        <section class="screen-panel command-panel">
          <PanelTitle title="当前设备控制记录" />
          <div class="command-list scroll-list">
            <div v-for="log in visibleCommands" :key="log.id" class="command-row">
              <div>
                <strong>{{ log.deviceId }}</strong>
                <span>{{ commandText(log.command) }} · {{ sourceText(log.source) }} · {{ log.createdAt }}</span>
              </div>
              <b :class="{ danger: log.result === 'failed', pending: log.result === 'pending' }">
                {{ resultText(log.result) }}
              </b>
            </div>
            <div v-if="!visibleCommands.length" class="empty-line">当前设备暂无控制记录</div>
          </div>
        </section>

        <section class="screen-panel detail-panel">
          <PanelTitle title="当前设备详情" />
          <div class="detail-grid scroll-list">
            <div>
              <span>设备位置</span>
              <strong>{{ selectedDevice?.location || "--" }}</strong>
            </div>
            <div>
              <span>灯状态</span>
              <strong>{{ lampStatusText(selectedDevice?.lampStatus ?? "OFF") }}</strong>
            </div>
            <div>
              <span>设备告警</span>
              <strong>{{ selectedAlarms.length }}</strong>
            </div>
            <div>
              <span>最后心跳</span>
              <strong>{{ selectedDevice?.lastHeartbeatAt || "--" }}</strong>
            </div>
            <div>
              <span>设备编号</span>
              <strong>{{ selectedDevice?.deviceCode || "--" }}</strong>
            </div>
            <div>
              <span>设备状态</span>
              <strong>{{ deviceStatusText(selectedDevice?.status ?? "offline") }}</strong>
            </div>
            <div>
              <span>未处理告警</span>
              <strong>{{ selectedUnhandledAlarms.length }}</strong>
            </div>
            <div>
              <span>控制记录</span>
              <strong>{{ selectedCommands.length || recentCommands.length }}</strong>
            </div>
          </div>
        </section>
      </aside>
    </main>
  </section>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, onUnmounted, ref } from "vue";

import { mockDashboardOverview } from "@/mock/data";
import { getDashboardOverview } from "@/services/dashboardService";
import { getLightHistory } from "@/services/lightService";
import type {
  AlarmRecord,
  AlarmType,
  CommandLog,
  CommandSource,
  CommandType,
  DashboardStat,
  Device,
  DeviceStatus,
  LampStatus,
  LightHistoryPoint,
} from "@/types/models";

const PanelTitle = defineComponent({
  props: {
    title: {
      type: String,
      required: true,
    },
  },
  setup(props) {
    return () => h("div", { class: "panel-title" }, [h("span"), h("strong", props.title), h("span")]);
  },
});

const stats = ref<DashboardStat[]>([]);
const latestAlarms = ref<AlarmRecord[]>([]);
const featuredHistory = ref<LightHistoryPoint[]>([]);
const selectedHistory = ref<LightHistoryPoint[]>([]);
const recentCommands = ref<CommandLog[]>([]);
const devices = ref<Device[]>([]);
const selectedDeviceId = ref<number | null>(null);
const now = ref(new Date());
const isLoading = ref(true);
const historyLoading = ref(false);
const loadError = ref("");

let clockTimer: ReturnType<typeof window.setInterval> | undefined;

const totalCount = computed(() => devices.value.length);
const onlineCount = computed(() => devices.value.filter((item) => item.status === "online").length);
const offlineCount = computed(() => devices.value.filter((item) => item.status === "offline").length);
const lampOnCount = computed(() => devices.value.filter((item) => item.lampStatus === "ON").length);
const lampOffCount = computed(() => devices.value.filter((item) => item.lampStatus === "OFF").length);
const unhandledAlarmCount = computed(() => latestAlarms.value.filter((item) => !item.handled).length);
const handledAlarmCount = computed(() => latestAlarms.value.filter((item) => item.handled).length);
const commandCount = computed(() => recentCommands.value.length);
const onlineRate = computed(() => ratio(onlineCount.value, totalCount.value));
const offlineRate = computed(() => ratio(offlineCount.value, totalCount.value));
const lampRate = computed(() => ratio(lampOnCount.value, totalCount.value));
const lampOffRate = computed(() => ratio(lampOffCount.value, totalCount.value));

const selectedDevice = computed(() => {
  if (!devices.value.length) return null;
  return devices.value.find((item) => item.id === selectedDeviceId.value) ?? devices.value[0];
});

const selectedAlarms = computed(() =>
  latestAlarms.value.filter((item) => item.deviceId === selectedDevice.value?.deviceCode),
);

const selectedUnhandledAlarms = computed(() => selectedAlarms.value.filter((item) => !item.handled));

const selectedCommands = computed(() =>
  recentCommands.value.filter((item) => item.deviceId === selectedDevice.value?.deviceCode),
);

const currentTime = computed(() =>
  now.value.toLocaleTimeString("zh-CN", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }),
);

const currentDate = computed(() =>
  now.value.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    weekday: "long",
  }),
);

const stateText = computed(() => {
  if (isLoading.value) return "数据加载中";
  if (historyLoading.value) return "正在切换设备数据";
  return loadError.value;
});

const latestLightIntensity = computed(() => {
  const point = selectedHistory.value.at(-1);
  return point ? `${point.lightIntensity}` : "--";
});

const topMetrics = computed(() => [
  { label: "设备总数", value: String(totalCount.value || statValue("设备总数", "--")) },
  { label: "在线设备", value: String(onlineCount.value || statValue("在线设备", "0")) },
  { label: "未处理告警", value: String(unhandledAlarmCount.value || statValue("离线告警", "0")) },
]);

const compactStats = computed(() => [
  { label: "离线设备", value: offlineCount.value },
  { label: "当前开灯", value: lampOnCount.value },
  { label: "当前关灯", value: lampOffCount.value },
  { label: "告警总数", value: latestAlarms.value.length },
  { label: "已处理告警", value: handledAlarmCount.value },
  { label: "控制记录", value: commandCount.value },
  { label: "历史采样", value: selectedHistory.value.length },
  { label: "当前设备", value: selectedDevice.value?.deviceCode || "--" },
]);

const statusItems = computed(() => [
  { label: "在线设备", value: onlineCount.value, percent: onlineRate.value },
  { label: "离线设备", value: offlineCount.value, percent: offlineRate.value },
  { label: "开灯设备", value: lampOnCount.value, percent: lampRate.value },
  { label: "关灯设备", value: lampOffCount.value, percent: lampOffRate.value },
]);

const sceneDevices = computed(() => {
  if (devices.value.length) return devices.value.slice(0, 12);
  return [
    {
      id: 0,
      deviceCode: "--",
      deviceName: "暂无设备",
      location: "--",
      status: "offline",
      lampStatus: "OFF",
      lastHeartbeatAt: "--",
    } as Device,
  ];
});

const visibleDevices = computed(() => devices.value);
const visibleAlarms = computed(() => latestAlarms.value);
const visibleCommands = computed(() =>
  selectedCommands.value.length ? selectedCommands.value : recentCommands.value,
);

const trendBars = computed(() => {
  const source = selectedHistory.value.slice(-8);
  if (!source.length) return [];
  const maxValue = Math.max(...source.map((item) => item.lightIntensity), 1);
  return source.map((item) => ({
    label: item.timestamp.slice(-5),
    value: Math.max(16, Math.round((item.lightIntensity / maxValue) * 86)),
  }));
});

function ratio(value: number, total: number) {
  if (!total) return 0;
  return Math.round((value / total) * 100);
}

function statValue(label: string, fallback: string) {
  return stats.value.find((item) => item.label.includes(label))?.value ?? fallback;
}

function nodeStyle(index: number) {
  const positions = [
    [44, 18],
    [52, 25],
    [59, 32],
    [66, 41],
    [57, 48],
    [49, 55],
    [42, 62],
    [35, 69],
    [62, 60],
    [70, 68],
    [29, 53],
    [23, 44],
  ];
  const [left, top] = positions[index % positions.length];
  return { left: `${left}%`, top: `${top}%` };
}

function deviceStatusText(status: DeviceStatus) {
  return status === "online" ? "在线" : "离线";
}

function lampStatusText(status: LampStatus) {
  return status === "ON" ? "开灯" : "关灯";
}

function alarmTypeText(type: AlarmType) {
  const labels: Record<AlarmType, string> = {
    DEVICE_OFFLINE: "设备离线",
    SENSOR_OFFLINE: "传感器离线",
    LIGHT_ABNORMAL: "光照异常",
    COMMAND_FAILED: "指令失败",
  };
  return labels[type];
}

function commandText(command: CommandType) {
  const labels: Record<CommandType, string> = {
    TURN_ON: "开灯",
    TURN_OFF: "关灯",
    SET_BRIGHTNESS: "调节亮度",
  };
  return labels[command];
}

function sourceText(source: CommandSource) {
  return source === "auto" ? "自动" : "手动";
}

function resultText(result: CommandLog["result"]) {
  const labels: Record<CommandLog["result"], string> = {
    pending: "执行中",
    success: "成功",
    failed: "失败",
    skipped: "跳过",
  };
  return labels[result];
}

function locationForAlarm(deviceCode: string) {
  return devices.value.find((item) => item.deviceCode === deviceCode)?.location ?? "--";
}

async function loadSelectedHistory(device: Device | null) {
  if (!device || device.id === 0) {
    selectedHistory.value = [];
    return;
  }

  if (devices.value[0]?.id === device.id && featuredHistory.value.length) {
    selectedHistory.value = featuredHistory.value;
    return;
  }

  try {
    historyLoading.value = true;
    selectedHistory.value = await getLightHistory(device.id, { limit: 20 });
  } catch (error) {
    console.error("Selected device history load failed.", error);
    selectedHistory.value = [];
  } finally {
    historyLoading.value = false;
  }
}

function selectDevice(device: Device) {
  if (!device || device.id === 0 || selectedDeviceId.value === device.id) return;
  selectedDeviceId.value = device.id;
  void loadSelectedHistory(device);
}

function selectDeviceByCode(deviceCode: string) {
  const device = devices.value.find((item) => item.deviceCode === deviceCode);
  if (device) selectDevice(device);
}

function selectPreviousDevice() {
  if (!devices.value.length || !selectedDevice.value) return;
  const currentIndex = devices.value.findIndex((item) => item.id === selectedDevice.value?.id);
  const nextIndex = (currentIndex - 1 + devices.value.length) % devices.value.length;
  selectDevice(devices.value[nextIndex]);
}

function selectNextDevice() {
  if (!devices.value.length || !selectedDevice.value) return;
  const currentIndex = devices.value.findIndex((item) => item.id === selectedDevice.value?.id);
  const nextIndex = (currentIndex + 1) % devices.value.length;
  selectDevice(devices.value[nextIndex]);
}

function applyOverview(overview: {
  stats: DashboardStat[];
  latestAlarms: AlarmRecord[];
  featuredHistory: LightHistoryPoint[];
  devices: Device[];
  recentCommands: CommandLog[];
  featuredDevice: Pick<Device, "deviceCode" | "deviceName" | "status" | "lampStatus">;
}) {
  stats.value = overview.stats;
  latestAlarms.value = overview.latestAlarms;
  featuredHistory.value = overview.featuredHistory;
  selectedHistory.value = overview.featuredHistory;
  devices.value = overview.devices;
  recentCommands.value = overview.recentCommands;

  const featured = overview.devices.find((item) => item.deviceCode === overview.featuredDevice.deviceCode);
  selectedDeviceId.value = featured?.id ?? overview.devices[0]?.id ?? null;
}

onMounted(async () => {
  try {
    isLoading.value = true;
    loadError.value = "";
    applyOverview(await getDashboardOverview());
  } catch (error) {
    console.error("Dashboard overview load failed, fallback to mock data.", error);
    loadError.value = "实时接口暂不可用，当前展示本地演示数据";
    applyOverview(structuredClone(mockDashboardOverview));
  } finally {
    isLoading.value = false;
  }

  clockTimer = window.setInterval(() => {
    now.value = new Date();
  }, 1000);
});

onUnmounted(() => {
  if (clockTimer) {
    window.clearInterval(clockTimer);
  }
});
</script>

<style scoped>
.bigscreen-dashboard {
  position: relative;
  width: 100vw;
  height: 100vh;
  min-width: 1180px;
  min-height: 660px;
  padding: 12px 18px 16px;
  overflow: hidden;
  color: #dff7ff;
  background:
    linear-gradient(rgba(51, 179, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(51, 179, 255, 0.035) 1px, transparent 1px),
    radial-gradient(circle at 50% 36%, rgba(36, 147, 206, 0.24), transparent 34%),
    linear-gradient(180deg, #020712 0%, #061322 55%, #020712 100%);
  background-size: 44px 44px, 44px 44px, auto, auto;
}

.bigscreen-dashboard::before,
.bigscreen-dashboard::after {
  position: absolute;
  inset: 12px;
  pointer-events: none;
  border: 1px solid rgba(80, 199, 255, 0.28);
  content: "";
}

.bigscreen-dashboard::after {
  inset: 23px 34px 20px;
  border-color: rgba(80, 199, 255, 0.1);
}

.screen-header {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  height: 58px;
}

.header-wing {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(72, 197, 255, 0.64), transparent);
}

.title-block {
  min-width: 420px;
  text-align: center;
}

.title-block span {
  display: block;
  color: #68d8ff;
  font-size: 10px;
  letter-spacing: 0.28em;
  text-transform: uppercase;
}

.title-block h1 {
  margin: 0;
  color: #e8fbff;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-shadow: 0 0 18px rgba(89, 210, 255, 0.72);
}

.header-clock {
  justify-self: end;
  display: grid;
  gap: 2px;
  min-width: 210px;
  text-align: right;
}

.header-clock strong {
  color: #eaf9ff;
  font-family: "Consolas", monospace;
  font-size: 18px;
}

.header-clock span {
  color: #9dc6d8;
  font-size: 11px;
}

.data-state {
  position: absolute;
  right: 218px;
  bottom: 8px;
  padding: 4px 10px;
  border: 1px solid rgba(80, 203, 255, 0.24);
  color: #9eeaff;
  background: rgba(4, 17, 30, 0.62);
  font-size: 11px;
}

.data-state.warning {
  border-color: rgba(255, 210, 102, 0.34);
  color: #ffe39b;
  background: rgba(92, 64, 16, 0.24);
}

.screen-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 310px minmax(500px, 1fr) 390px;
  gap: 16px;
  height: calc(100vh - 86px);
  min-height: 570px;
}

.screen-column {
  display: grid;
  gap: 12px;
  min-height: 0;
}

.left-column {
  grid-template-rows: 184px 1fr 150px;
}

.right-column {
  grid-template-rows: minmax(128px, 0.9fr) minmax(190px, 1.05fr) minmax(120px, 0.7fr) minmax(120px, 0.65fr);
}

.screen-panel,
.dock-card {
  min-width: 0;
  min-height: 0;
  padding: 12px;
  overflow: hidden;
  border: 1px solid rgba(68, 185, 255, 0.22);
  border-radius: 4px;
  background:
    linear-gradient(180deg, rgba(5, 21, 38, 0.86), rgba(2, 9, 19, 0.78)),
    radial-gradient(circle at 100% 0%, rgba(55, 190, 255, 0.1), transparent 34%);
  box-shadow: inset 0 0 18px rgba(63, 185, 255, 0.08), 0 0 28px rgba(0, 0, 0, 0.28);
}

.panel-title {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  color: #f3fcff;
  font-size: 13px;
  font-weight: 700;
}

.panel-title span {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(85, 207, 255, 0.58));
}

.panel-title span:last-child {
  background: linear-gradient(90deg, rgba(85, 207, 255, 0.58), transparent);
}

.ring-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.metric-ring {
  display: grid;
  justify-items: center;
  gap: 6px;
  color: #b6d8e8;
  font-size: 11px;
}

.ring-core {
  display: grid;
  place-items: center;
  width: 58px;
  height: 58px;
  border: 4px solid rgba(82, 211, 255, 0.72);
  border-radius: 50%;
  color: #f7fdff;
  font-family: "Consolas", monospace;
  font-size: 15px;
  font-weight: 700;
  box-shadow: inset 0 0 16px rgba(74, 199, 255, 0.25), 0 0 18px rgba(74, 199, 255, 0.22);
}

.mini-stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 7px;
  margin-top: 12px;
}

.mini-stat {
  display: grid;
  gap: 2px;
  min-height: 38px;
  padding: 5px 4px;
  border: 1px solid rgba(86, 196, 255, 0.16);
  background: rgba(3, 15, 28, 0.64);
  text-align: center;
}

.mini-stat strong {
  overflow: hidden;
  color: #e9fbff;
  font-family: "Consolas", monospace;
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mini-stat span,
.status-item span,
.trend-summary span,
.detail-grid span,
.device-row span,
.command-row span,
.rate-body em,
.empty-line,
.focus-card p,
.selected-device small,
.selected-device span,
.selected-device em {
  color: #8eb8ca;
  font-size: 10px;
}

.status-list {
  display: grid;
  gap: 13px;
  padding-top: 4px;
}

.status-item {
  display: grid;
  grid-template-columns: 64px 34px 1fr 38px;
  align-items: center;
  gap: 8px;
}

.status-item strong,
.status-item em {
  color: #e9fbff;
  font-family: "Consolas", monospace;
  font-style: normal;
}

.status-bar {
  height: 8px;
  padding: 1px;
  border: 1px solid rgba(80, 203, 255, 0.24);
  background: rgba(4, 16, 28, 0.86);
}

.status-bar i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #1db6ff, #8ff4ff);
  box-shadow: 0 0 10px rgba(69, 211, 255, 0.5);
}

.focus-card {
  display: grid;
  gap: 7px;
  height: calc(100% - 28px);
  padding: 10px;
  border: 1px solid rgba(80, 203, 255, 0.16);
  background: rgba(3, 15, 28, 0.55);
}

.focus-card strong,
.selected-device strong {
  color: #f7fdff;
}

.focus-card span {
  color: #8edfff;
  font-family: "Consolas", monospace;
}

.focus-card div {
  display: flex;
  gap: 8px;
}

.focus-card b,
.device-row b,
.command-row b {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  min-height: 22px;
  padding: 0 8px;
  border: 1px solid rgba(80, 255, 190, 0.28);
  color: #a7ffd6;
  background: rgba(18, 70, 50, 0.28);
  font-size: 11px;
}

.focus-card b.danger,
.device-row b.danger,
.command-row b.danger {
  border-color: rgba(255, 118, 118, 0.32);
  color: #ffb8b8;
  background: rgba(84, 24, 24, 0.32);
}

.command-row b.pending {
  border-color: rgba(255, 210, 102, 0.32);
  color: #ffe39b;
  background: rgba(92, 64, 16, 0.32);
}

.center-stage {
  display: grid;
  grid-template-rows: minmax(0, 1fr) 154px;
  gap: 12px;
  min-width: 0;
  min-height: 0;
}

.city-map {
  position: relative;
  min-height: 0;
  overflow: hidden;
  border: 1px solid rgba(66, 178, 255, 0.18);
  background:
    radial-gradient(ellipse at center, rgba(78, 168, 210, 0.18), transparent 50%),
    linear-gradient(180deg, rgba(8, 18, 31, 0.4), rgba(2, 7, 14, 0.95));
}

.road {
  position: absolute;
  background: linear-gradient(90deg, transparent, rgba(105, 220, 255, 0.34), transparent);
  box-shadow: 0 0 24px rgba(72, 206, 255, 0.35);
  transform-origin: center;
}

.road-main {
  left: 47%;
  top: -8%;
  width: 58px;
  height: 118%;
  transform: rotate(34deg);
}

.road-branch {
  left: 14%;
  top: 54%;
  width: 54%;
  height: 38px;
  transform: rotate(-26deg);
}

.road-cross {
  right: 10%;
  top: 60%;
  width: 40%;
  height: 30px;
  transform: rotate(20deg);
}

.district {
  position: absolute;
  border: 1px solid rgba(82, 175, 220, 0.12);
  background: rgba(105, 140, 160, 0.08);
  box-shadow: inset 0 0 28px rgba(0, 0, 0, 0.22);
}

.district-a {
  left: 9%;
  top: 18%;
  width: 24%;
  height: 22%;
  transform: skewY(-18deg);
}

.district-b {
  right: 13%;
  top: 16%;
  width: 22%;
  height: 24%;
  transform: skewY(18deg);
}

.district-c {
  left: 18%;
  bottom: 10%;
  width: 30%;
  height: 18%;
  transform: skewY(-16deg);
}

.route-line {
  position: absolute;
  left: 38%;
  top: 18%;
  width: 38%;
  height: 56%;
  border: 2px solid rgba(98, 230, 255, 0.5);
  border-left: 0;
  border-radius: 0 12px 12px 0;
  filter: drop-shadow(0 0 8px rgba(80, 214, 255, 0.58));
  transform: rotate(18deg);
}

.streetlight-node {
  position: absolute;
  width: 42px;
  height: 70px;
  padding: 0;
  border: 0;
  background: transparent;
  transform: translate(-50%, -50%);
}

.streetlight-node i {
  position: absolute;
  left: 19px;
  bottom: 0;
  width: 4px;
  height: 52px;
  border-radius: 999px;
  background: linear-gradient(180deg, #d8f8ff, #3f9eca);
  box-shadow: 0 0 12px rgba(104, 220, 255, 0.56);
}

.streetlight-node span {
  position: absolute;
  left: 18px;
  top: 6px;
  width: 28px;
  height: 8px;
  border-radius: 999px;
  background: #bceeff;
  box-shadow: 0 0 18px rgba(100, 218, 255, 0.82), -14px 18px 28px rgba(110, 220, 255, 0.14);
  transform: rotate(-18deg);
}

.node-offline {
  opacity: 0.48;
  filter: grayscale(0.7);
}

.node-on span {
  background: #f8fdff;
  box-shadow: 0 0 24px rgba(130, 231, 255, 0.95), -18px 22px 38px rgba(130, 231, 255, 0.22);
}

.node-selected::after {
  position: absolute;
  left: 50%;
  bottom: -7px;
  width: 34px;
  height: 8px;
  border: 1px solid rgba(120, 240, 255, 0.72);
  border-radius: 50%;
  content: "";
  transform: translateX(-50%);
  box-shadow: 0 0 14px rgba(100, 230, 255, 0.68);
}

.selected-device {
  position: absolute;
  left: 50%;
  bottom: 28px;
  display: grid;
  gap: 4px;
  min-width: 220px;
  padding: 10px 14px;
  border-left: 3px solid #68e6ff;
  background: rgba(2, 12, 24, 0.72);
  box-shadow: 0 0 22px rgba(54, 205, 255, 0.2);
}

.selected-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.selected-actions button {
  min-height: 24px;
  padding: 0 10px;
  border: 1px solid rgba(80, 203, 255, 0.24);
  color: #dff7ff;
  background: rgba(5, 28, 48, 0.72);
}

.bottom-dock {
  display: grid;
  grid-template-columns: 174px minmax(0, 1fr);
  gap: 12px;
  min-height: 0;
}

.rate-body {
  display: grid;
  justify-items: center;
  gap: 2px;
  padding-top: 4px;
}

.rate-body strong {
  color: #f7fdff;
  font-family: "Consolas", monospace;
  font-size: 32px;
}

.rate-body span {
  color: #72dfff;
  font-size: 13px;
}

.table-card {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
}

.table-scroll,
.scroll-list {
  min-height: 0;
  overflow-x: hidden;
  overflow-y: scroll;
  padding-right: 4px;
  scrollbar-color: rgba(80, 203, 255, 0.68) rgba(4, 17, 30, 0.78);
  scrollbar-width: thin;
}

.table-scroll::-webkit-scrollbar,
.scroll-list::-webkit-scrollbar {
  width: 5px;
  height: 5px;
}

.table-scroll::-webkit-scrollbar-thumb,
.scroll-list::-webkit-scrollbar-thumb {
  background: rgba(80, 203, 255, 0.38);
}

.screen-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

.screen-table th,
.screen-table td {
  max-width: 220px;
  padding: 6px 8px;
  overflow: hidden;
  border-bottom: 1px solid rgba(79, 194, 255, 0.1);
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.screen-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  color: #8ce5ff;
  background: rgba(10, 42, 70, 0.96);
}

.screen-table td {
  color: #c9e9f5;
}

.screen-table tr.active td {
  background: rgba(74, 203, 255, 0.08);
}

.device-panel,
.command-panel,
.detail-panel {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
}

.device-list,
.command-list {
  display: grid;
  gap: 8px;
  align-content: start;
}

.device-row,
.command-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
  width: 100%;
  padding: 7px 8px;
  border: 1px solid rgba(80, 203, 255, 0.12);
  color: inherit;
  background: rgba(3, 15, 28, 0.5);
  text-align: left;
}

.device-row.active {
  border-color: rgba(112, 229, 255, 0.68);
  background: rgba(27, 104, 142, 0.24);
}

.device-row div,
.command-row div {
  min-width: 0;
}

.device-row strong,
.device-row span,
.command-row strong,
.command-row span {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.device-row strong,
.command-row strong {
  color: #edfaff;
  font-size: 12px;
}

.trend-panel {
  display: grid;
  grid-template-rows: auto auto 74px minmax(0, 1fr);
}

.trend-summary,
.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.detail-grid {
  align-content: start;
}

.trend-summary div,
.detail-grid div {
  display: grid;
  gap: 3px;
  min-width: 0;
  padding: 8px;
  border: 1px solid rgba(80, 203, 255, 0.16);
  background: rgba(4, 17, 30, 0.56);
}

.trend-summary strong,
.detail-grid strong {
  overflow: hidden;
  color: #ffd37c;
  font-family: "Consolas", monospace;
  font-size: 16px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bar-chart {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  align-items: end;
  gap: 7px;
  min-height: 0;
  padding: 8px 4px 16px;
}

.bar-chart:empty::before {
  grid-column: 1 / -1;
  align-self: center;
  color: #8eb8ca;
  font-size: 12px;
  text-align: center;
  content: "暂无光照趋势";
}

.bar-chart i {
  position: relative;
  display: block;
  min-height: 16px;
  border-radius: 3px 3px 0 0;
  background: linear-gradient(180deg, #8fedff, #1e9de0);
  box-shadow: 0 0 12px rgba(70, 204, 255, 0.38);
}

.bar-chart span {
  position: absolute;
  left: 50%;
  bottom: -16px;
  color: #82aebe;
  font-size: 9px;
  transform: translateX(-50%);
}

.history-list {
  display: grid;
  gap: 6px;
  align-content: start;
}

.history-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 56px 42px;
  gap: 8px;
  align-items: center;
  padding: 5px 7px;
  border: 1px solid rgba(80, 203, 255, 0.12);
  background: rgba(3, 15, 28, 0.46);
}

.history-row span,
.history-row strong,
.history-row b {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-row span {
  color: #8eb8ca;
  font-size: 10px;
}

.history-row strong {
  color: #ffd37c;
  font-family: "Consolas", monospace;
  font-size: 12px;
}

.history-row b {
  color: #a7ffd6;
  font-size: 10px;
  font-weight: 700;
}

.empty-line {
  padding: 10px;
  text-align: center;
}

@media (max-width: 1180px) {
  .bigscreen-dashboard {
    min-width: 0;
    height: auto;
    min-height: 100vh;
    overflow: auto;
  }

  .screen-grid {
    grid-template-columns: 1fr;
    height: auto;
  }

  .left-column,
  .right-column,
  .center-stage {
    grid-template-rows: none;
  }
}
</style>
