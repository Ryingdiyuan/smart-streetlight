<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Devices</p>
        <h3>设备列表</h3>
      </div>
      <p class="section-note">已接入真实设备列表接口，支持按关键词与状态筛选，后台静默同步。</p>
    </header>

    <div class="stats-grid">
      <StatCard v-for="item in summaryStats" :key="item.label" :stat="item" />
    </div>

    <PanelCard title="设备筛选与列表" subtitle="支持关键词与状态筛选">
      <div class="toolbar-row">
        <input
          v-model="keyword"
          class="search-input"
          type="text"
          placeholder="搜索设备编号 / 名称 / 位置"
        />
        <div class="toolbar-actions">
          <span class="section-note">{{ refreshStatusText }}</span>
          <button class="ghost-button" type="button" :disabled="refreshing" @click="loadDevices()">
            {{ refreshing ? "同步中..." : "手动刷新" }}
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

      <div v-if="loading && !devices.length" class="placeholder-box">正在加载真实设备数据...</div>
      <div v-else-if="loadError && !devices.length" class="placeholder-box">{{ loadError }}</div>
      <div v-else class="table-wrapper">
        <div v-if="loadError" class="placeholder-box">{{ loadError }}</div>
        <div v-if="canOperateDevices" class="bulk-action-bar">
          <div class="bulk-selection-summary">
            <span class="section-note">已选中 {{ selectedCount }} 台设备</span>
            <span v-if="areAllVisibleSelected && filteredDevices.length" class="inline-note">
              当前筛选结果已全部选中
            </span>
          </div>
          <div class="bulk-action-buttons">
            <button
              class="ghost-button"
              type="button"
              :disabled="batchSubmitting || !filteredDevices.length"
              @click="selectAllVisible"
            >
              全选当前列表
            </button>
            <button
              class="ghost-button"
              type="button"
              :disabled="batchSubmitting || !selectedCount"
              @click="clearSelection"
            >
              清空选择
            </button>
            <button
              class="primary-button"
              type="button"
              :disabled="batchSubmitting || !selectedCount"
              @click="handleBatchCommand('TURN_ON')"
            >
              {{ batchSubmitting ? "执行中..." : "批量开灯" }}
            </button>
            <button
              class="ghost-button"
              type="button"
              :disabled="batchSubmitting || !selectedCount"
              @click="handleBatchCommand('TURN_OFF')"
            >
              {{ batchSubmitting ? "执行中..." : "批量关灯" }}
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
              <th>设备编号</th>
              <th>设备名称</th>
              <th>安装位置</th>
              <th>在线状态</th>
              <th>路灯状态</th>
              <th>最近心跳</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="device in filteredDevices" :key="device.id">
              <td v-if="canOperateDevices" class="table-checkbox">
                <input
                  v-model="selectedDeviceIds"
                  type="checkbox"
                  :value="device.id"
                  :disabled="batchSubmitting"
                />
              </td>
              <td>{{ device.deviceCode }}</td>
              <td>{{ device.deviceName }}</td>
              <td>{{ device.location }}</td>
              <td>
                <StatusBadge
                  :status="device.status"
                  :text="device.status === 'online' ? '在线' : '离线'"
                />
              </td>
              <td>
                <StatusBadge
                  :status="device.lampStatus === 'ON' ? 'success' : 'info'"
                  :text="device.lampStatus"
                />
              </td>
              <td>{{ device.lastHeartbeatAt }}</td>
              <td>
                <RouterLink class="text-link" :to="`/devices/${device.id}`">查看详情</RouterLink>
              </td>
            </tr>
            <tr v-if="!filteredDevices.length">
              <td :colspan="canOperateDevices ? 8 : 7" class="table-empty">没有匹配的设备</td>
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
import { getDeviceList, sendBatchDeviceCommand } from "@/services/deviceService";
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
  { label: "设备总数", value: String(devices.value.length), helper: "当前列表中的设备数量" },
  {
    label: "在线设备",
    value: String(devices.value.filter((device) => device.status === "online").length),
    helper: "心跳正常设备",
  },
  {
    label: "离线设备",
    value: String(devices.value.filter((device) => device.status === "offline").length),
    helper: "需重点排查",
  },
  {
    label: "当前开灯",
    value: String(devices.value.filter((device) => device.lampStatus === "ON").length),
    helper: "方便答辩展示",
  },
]);

const filteredDevices = computed(() => {
  const normalized = keyword.value.trim().toLowerCase();
  return devices.value.filter((device) => {
    const matchKeyword =
      !normalized ||
      [device.deviceCode, device.deviceName, device.location]
        .join(" ")
        .toLowerCase()
        .includes(normalized);

    const matchStatus =
      statusFilter.value === "all" || device.status === statusFilter.value;

    return matchKeyword && matchStatus;
  });
});

const selectedCount = computed(() => selectedDeviceIds.value.length);

const visibleDeviceIds = computed(() => filteredDevices.value.map((device) => device.id));

const areAllVisibleSelected = computed(
  () =>
    Boolean(visibleDeviceIds.value.length) &&
    visibleDeviceIds.value.every((id) => selectedDeviceIds.value.includes(id)),
);

const refreshStatusText = computed(() => {
  if (refreshing.value) {
    return "正在后台同步...";
  }
  if (!lastUpdatedAt.value) {
    return "首次加载中";
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
    // Keep the original message when it is not a JSON payload.
  }

  return error.message;
}

function syncSelectedDeviceIds() {
  const validIds = new Set(devices.value.map((device) => device.id));
  selectedDeviceIds.value = selectedDeviceIds.value.filter((id) => validIds.has(id));
}

function selectAllVisible() {
  const merged = new Set([...selectedDeviceIds.value, ...visibleDeviceIds.value]);
  selectedDeviceIds.value = [...merged];
}

function clearSelection() {
  selectedDeviceIds.value = [];
}

function applyBatchLampStatus(command: Extract<CommandType, "TURN_ON" | "TURN_OFF">, summary: BatchCommandSummary) {
  const successIds = new Set(
    summary.results.filter((item) => item.result === "success").map((item) => item.deviceId),
  );
  if (!successIds.size) {
    return;
  }

  const nextStatus = command === "TURN_ON" ? "ON" : "OFF";
  devices.value = devices.value.map((device) =>
    successIds.has(device.id) ? { ...device, lampStatus: nextStatus } : device,
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
    batchMessage.value = `已发送${command === "TURN_ON" ? "批量开灯" : "批量关灯"}指令，共 ${summary.total} 台，成功 ${summary.successCount} 台，失败 ${summary.failedCount} 台，跳过 ${summary.skippedCount} 台。`;
    void loadDevices({ silent: true });
  } catch (error) {
    batchMessageTone.value = "error";
    batchMessage.value = `批量操作失败：${getErrorMessage(error)}`;
  } finally {
    batchSubmitting.value = false;
  }
}

async function loadDevices(options: { silent?: boolean } = {}) {
  const shouldLoadSilently = Boolean(options.silent && devices.value.length);
  if (shouldLoadSilently) {
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
    loadError.value = `设备列表加载失败：${getErrorMessage(error)}`;
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
