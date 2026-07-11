<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Devices</p>
        <h3>路灯列表</h3>
      </div>
      <p class="section-note">查看路灯档案、绑定传感器、控制模式与在线状态。</p>
    </header>

    <div class="stats-grid">
      <StatCard v-for="item in summaryStats" :key="item.label" :stat="item" />
    </div>

    <PanelCard title="路灯筛选与列表" subtitle="支持按关键字与在线状态筛选">
      <div class="toolbar-row">
        <input
          v-model="keyword"
          class="search-input"
          type="text"
          placeholder="搜索路灯编码 / 名称 / 位置 / 传感器编码"
        />
        <div class="toolbar-actions">
          <span class="section-note">{{ refreshStatusText }}</span>
          <button class="ghost-button" type="button" :disabled="refreshing" @click="loadDevices()">
            {{ refreshing ? "刷新中..." : "手动刷新" }}
          </button>
          <button
            v-for="option in filterOptions"
            :key="option.value"
            class="ghost-button"
            :class="{ 'ghost-button-active': statusFilter === option.value }"
            @click="statusFilter = option.value"
          >
            {{ option.label }}
          </button>
        </div>
      </div>

      <div v-if="loading && !devices.length" class="placeholder-box">正在加载路灯数据...</div>
      <div v-else-if="loadError && !devices.length" class="placeholder-box">{{ loadError }}</div>
      <div v-else class="table-wrapper">
        <div v-if="loadError" class="placeholder-box">{{ loadError }}</div>
        <div v-if="canOperateDevices" class="bulk-action-bar">
          <div class="bulk-selection-summary">
            <span class="section-note">已选中 {{ selectedCount }} 盏路灯</span>
          </div>
          <div class="bulk-action-buttons">
            <button class="ghost-button" type="button" :disabled="batchSubmitting || !filteredDevices.length" @click="selectAllVisible">
              全选当前列表
            </button>
            <button class="ghost-button" type="button" :disabled="batchSubmitting || !selectedCount" @click="clearSelection">
              清空选择
            </button>
            <button class="primary-button" type="button" :disabled="batchSubmitting || !selectedCount" @click="handleBatchCommand('TURN_ON')">
              {{ batchSubmitting ? "执行中..." : "批量开灯" }}
            </button>
            <button class="ghost-button" type="button" :disabled="batchSubmitting || !selectedCount" @click="handleBatchCommand('TURN_OFF')">
              {{ batchSubmitting ? "执行中..." : "批量关灯" }}
            </button>
            <button class="ghost-button" type="button" :disabled="batchSubmitting || !selectedCount" @click="handleBatchSensorControl(true)">
              {{ batchSubmitting ? "执行中..." : "批量启用传感器控制" }}
            </button>
            <button class="ghost-button" type="button" :disabled="batchSubmitting || !selectedCount" @click="handleBatchSensorControl(false)">
              {{ batchSubmitting ? "执行中..." : "批量暂停传感器控制" }}
            </button>
          </div>
        </div>
        <div
          v-if="batchMessage"
          class="bulk-feedback"
          :class="{ 'bulk-feedback-error': batchMessageTone === 'error' }"
        >
          {{ batchMessage }}
        </div>

        <table>
          <thead>
            <tr>
              <th v-if="canOperateDevices" class="table-checkbox">选择</th>
              <th>路灯编码</th>
              <th>路灯名称</th>
              <th>安装位置</th>
              <th>绑定传感器</th>
              <th>控制模式</th>
              <th>在线状态</th>
              <th>灯状态</th>
              <th>最近心跳</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="device in filteredDevices" :key="device.id">
              <td v-if="canOperateDevices" class="table-checkbox">
                <input v-model="selectedDeviceIds" type="checkbox" :value="device.id" :disabled="batchSubmitting" />
              </td>
              <td>{{ device.deviceCode }}</td>
              <td>{{ device.deviceName }}</td>
              <td>{{ device.location }}</td>
              <td>{{ device.sensorCode || "未绑定" }}</td>
              <td>{{ device.controlMode === "auto" ? "自动" : "手动" }}</td>
              <td>
                <StatusBadge :status="device.status" :text="device.status === 'online' ? '在线' : '离线'" />
              </td>
              <td>
                <StatusBadge :status="device.lampStatus === 'ON' ? 'success' : 'info'" :text="device.lampStatus" />
              </td>
              <td>{{ device.lastHeartbeatAt }}</td>
              <td>
                <RouterLink class="text-link" :to="`/devices/${device.id}`">查看详情</RouterLink>
              </td>
            </tr>
            <tr v-if="!filteredDevices.length">
              <td :colspan="canOperateDevices ? 10 : 9" class="table-empty">没有匹配的路灯</td>
            </tr>
          </tbody>
        </table>
      </div>
    </PanelCard>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import PanelCard from "@/components/PanelCard.vue";
import StatCard from "@/components/StatCard.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import { getDeviceList, sendBatchDeviceCommand, updateDevice } from "@/services/deviceService";
import { can } from "@/services/permissions";
import type { BatchCommandSummary, CommandType, DashboardStat, Device } from "@/types/models";

const devices = ref<Device[]>([]);
const keyword = ref("");
const statusFilter = ref<"all" | "online" | "offline">("all");
const loading = ref(true);
const refreshing = ref(false);
const loadError = ref("");
const lastUpdatedAt = ref<Date | null>(null);
const selectedDeviceIds = ref<number[]>([]);
const batchSubmitting = ref(false);
const batchMessage = ref("");
const batchMessageTone = ref<"success" | "error">("success");
let refreshTimer: number | undefined;

const canOperateDevices = computed(() => can("operateDevices"));

const filterOptions = [
  { label: "全部", value: "all" as const },
  { label: "在线", value: "online" as const },
  { label: "离线", value: "offline" as const },
];

const summaryStats = computed<DashboardStat[]>(() => [
  { label: "路灯总数", value: String(devices.value.length), helper: "当前列表中的路灯数量" },
  {
    label: "已绑定传感器",
    value: String(devices.value.filter((device) => device.sensorId != null).length),
    helper: "绑定后才可接收传感器数据",
  },
  {
    label: "自动模式",
    value: String(devices.value.filter((device) => device.controlMode === "auto").length),
    helper: "按阈值自动控制",
  },
  {
    label: "当前开灯",
    value: String(devices.value.filter((device) => device.lampStatus === "ON").length),
    helper: "便于展示运行效果",
  },
]);

const filteredDevices = computed(() => {
  const normalized = keyword.value.trim().toLowerCase();
  return devices.value.filter((device) => {
    const matchKeyword =
      !normalized ||
      [device.deviceCode, device.deviceName, device.location, device.sensorCode ?? ""]
        .join(" ")
        .toLowerCase()
        .includes(normalized);

    const matchStatus = statusFilter.value === "all" || device.status === statusFilter.value;
    return matchKeyword && matchStatus;
  });
});

const selectedCount = computed(() => selectedDeviceIds.value.length);
const visibleDeviceIds = computed(() => filteredDevices.value.map((device) => device.id));

const refreshStatusText = computed(() => {
  if (refreshing.value) {
    return "正在后台同步...";
  }
  if (!lastUpdatedAt.value) {
    return "首次加载中...";
  }
  return `最近更新：${lastUpdatedAt.value.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  })}`;
});

function getErrorMessage(error: unknown) {
  if (!(error instanceof Error)) {
    return "操作失败";
  }

  try {
    const parsed = JSON.parse(error.message) as { detail?: string };
    if (parsed.detail) {
      return parsed.detail;
    }
  } catch {
    // noop
  }

  return error.message;
}

function syncSelectedDeviceIds() {
  const validIds = new Set(devices.value.map((device) => device.id));
  selectedDeviceIds.value = selectedDeviceIds.value.filter((id) => validIds.has(id));
}

function selectAllVisible() {
  selectedDeviceIds.value = [...new Set([...selectedDeviceIds.value, ...visibleDeviceIds.value])];
}

function clearSelection() {
  selectedDeviceIds.value = [];
}

function applyBatchLampStatus(command: Extract<CommandType, "TURN_ON" | "TURN_OFF">, summary: BatchCommandSummary) {
  const successIds = new Set(summary.results.filter((item) => item.result === "success").map((item) => item.deviceId));
  if (!successIds.size) {
    return;
  }

  const nextStatus = command === "TURN_ON" ? "ON" : "OFF";
  devices.value = devices.value.map((device) => (successIds.has(device.id) ? { ...device, lampStatus: nextStatus } : device));
}

function applyBatchSensorControl(enabled: boolean, successIds: number[]) {
  if (!successIds.length) {
    return;
  }

  const successIdSet = new Set(successIds);
  devices.value = devices.value.map((device) =>
    successIdSet.has(device.id) ? { ...device, sensorControlEnabled: enabled } : device,
  );
}

async function handleBatchCommand(command: Extract<CommandType, "TURN_ON" | "TURN_OFF">) {
  if (!selectedCount.value || batchSubmitting.value || !canOperateDevices.value) {
    return;
  }

  batchSubmitting.value = true;
  batchMessage.value = "";

  try {
    const summary = await sendBatchDeviceCommand(selectedDeviceIds.value, command);
    applyBatchLampStatus(command, summary);
    selectedDeviceIds.value = [];
    batchMessageTone.value = summary.failedCount > 0 ? "error" : "success";
    batchMessage.value = `已下发${command === "TURN_ON" ? "批量开灯" : "批量关灯"}指令，共 ${summary.total} 盏，成功 ${summary.successCount} 盏，失败 ${summary.failedCount} 盏，跳过 ${summary.skippedCount} 盏。`;
    void loadDevices({ silent: true });
  } catch (error) {
    batchMessageTone.value = "error";
    batchMessage.value = `批量操作失败：${getErrorMessage(error)}`;
  } finally {
    batchSubmitting.value = false;
  }
}

async function handleBatchSensorControl(enabled: boolean) {
  if (!selectedCount.value || batchSubmitting.value || !canOperateDevices.value) {
    return;
  }

  batchSubmitting.value = true;
  batchMessage.value = "";

  try {
    const selectedDevices = devices.value.filter((device) => selectedDeviceIds.value.includes(device.id));
    const results = await Promise.allSettled(
      selectedDevices.map(async (device) => {
        await updateDevice(device.id, { sensor_control_enabled: enabled });
        return device;
      }),
    );

    const successDevices = results
      .filter((result): result is PromiseFulfilledResult<Device> => result.status === "fulfilled")
      .map((result) => result.value);
    const failedDeviceCodes = results
      .map((result, index) => ({ result, device: selectedDevices[index] }))
      .filter((item) => item.result.status === "rejected")
      .map((item) => item.device.deviceCode);

    applyBatchSensorControl(enabled, successDevices.map((device) => device.id));
    selectedDeviceIds.value = [];
    batchMessageTone.value = failedDeviceCodes.length > 0 ? "error" : "success";
    batchMessage.value = `${enabled ? "已批量启用" : "已批量暂停"}传感器控制，共 ${selectedDevices.length} 盏，成功 ${successDevices.length} 盏，失败 ${failedDeviceCodes.length} 盏${failedDeviceCodes.length ? `，失败设备：${failedDeviceCodes.join("、")}` : ""}。`;
    void loadDevices({ silent: true });
  } catch (error) {
    batchMessageTone.value = "error";
    batchMessage.value = `批量传感器控制失败：${getErrorMessage(error)}`;
  } finally {
    batchSubmitting.value = false;
  }
}

async function loadDevices(options: { silent?: boolean } = {}) {
  const silent = Boolean(options.silent && devices.value.length);
  if (silent) {
    refreshing.value = true;
  } else {
    loading.value = true;
  }
  loadError.value = "";

  try {
    devices.value = await getDeviceList();
    syncSelectedDeviceIds();
    lastUpdatedAt.value = new Date();
  } catch (error) {
    loadError.value = `路灯列表加载失败：${getErrorMessage(error)}`;
    if (!devices.value.length) {
      devices.value = [];
    }
  } finally {
    loading.value = false;
    refreshing.value = false;
  }
}

onMounted(async () => {
  await loadDevices();
  refreshTimer = window.setInterval(() => {
    void loadDevices({ silent: true });
  }, 30000);
});

onBeforeUnmount(() => {
  if (refreshTimer !== undefined) {
    window.clearInterval(refreshTimer);
  }
});
</script>

<style scoped>
.bulk-action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.bulk-selection-summary,
.bulk-action-buttons {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.bulk-selection-summary .section-note {
  text-align: left;
}

.bulk-feedback {
  margin-bottom: 16px;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid rgba(66, 211, 146, 0.28);
  background: rgba(15, 118, 110, 0.16);
  color: #d1fae5;
  line-height: 1.6;
}

.bulk-feedback-error {
  border-color: rgba(248, 113, 113, 0.28);
  background: rgba(127, 29, 29, 0.18);
  color: #fecaca;
}
</style>
