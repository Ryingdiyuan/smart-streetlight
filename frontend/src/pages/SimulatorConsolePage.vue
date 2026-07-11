<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Simulator</p>
        <h3>传感器模拟控制台</h3>
      </div>
      <p class="section-note">
        这里用于模拟传感器的 MQTT 联调。现在心跳发送和数据发送已经分开控制，即使关闭数据发送，也可以继续发送心跳确认传感器仍然在线。
      </p>
    </header>

    <div class="stats-grid">
      <StatCard v-for="item in summaryStats" :key="item.label" :stat="item" />
    </div>

    <div class="content-grid two-columns">
      <PanelCard title="Broker 配置" subtitle="查看并修改当前模拟器连接参数">
        <div class="form-grid">
          <label>
            <span>MQTT Host / IP</span>
            <input v-model="configForm.host" type="text" />
          </label>
          <label>
            <span>MQTT 端口</span>
            <input v-model.number="configForm.port" type="number" min="1" />
          </label>
          <label>
            <span>账号</span>
            <input v-model="configForm.username" type="text" />
          </label>
          <label>
            <span>密码</span>
            <input v-model="configForm.password" type="text" />
          </label>
          <label class="checkbox-field">
            <input v-model="configForm.enabled" type="checkbox" />
            <span>启用 MQTT 模拟发送</span>
          </label>
        </div>

        <div class="detail-tip-grid">
          <div class="summary-box">
            <span>连接状态</span>
            <strong>{{ config.connected ? "已连接" : "未连接" }}</strong>
          </div>
          <div class="summary-box">
            <span>Client ID</span>
            <strong>{{ config.clientId || "--" }}</strong>
          </div>
        </div>

        <div class="button-row simulator-actions-row">
          <button class="primary-button" type="button" :disabled="savingConfig" @click="handleSaveConfig">
            {{ savingConfig ? "保存中..." : "保存配置" }}
          </button>
          <button class="ghost-button" type="button" :disabled="refreshing" @click="loadConsoleData">
            刷新状态
          </button>
        </div>
      </PanelCard>

      <PanelCard title="联调说明" subtitle="软件设备和传感器模拟器分离管理">
        <div class="detail-tip-grid">
          <div class="summary-box">
            <span>软件设备中心</span>
            <strong>负责创建设备档案与绑定关系</strong>
          </div>
          <div class="summary-box">
            <span>模拟控制台</span>
            <strong>负责心跳、数据和 MQTT 联调</strong>
          </div>
        </div>

        <div class="button-row simulator-actions-row">
          <RouterLink class="primary-button" to="/software-devices">前往软件设备中心</RouterLink>
          <RouterLink class="ghost-button" to="/devices">查看设备列表</RouterLink>
          <span class="inline-note">先在软件端完成路灯建档与绑定，再回到这里做传感器联调。</span>
        </div>
      </PanelCard>
    </div>

    <PanelCard title="发送架构" subtitle="前端直接展示心跳类与数据类已拆分管理">
      <div class="detail-tip-grid">
        <div class="summary-box">
          <span>当前查看传感器</span>
          <strong>{{ activeDevice ? activeDevice.deviceCode : "--" }}</strong>
        </div>
        <div class="summary-box">
          <span>运行状态</span>
          <strong>{{ activeDevice ? (activeDevice.running ? "运行中" : "已停止") : "--" }}</strong>
        </div>
      </div>

      <div class="content-grid two-columns">
        <div class="summary-box">
          <span>HeartbeatPublisher</span>
          <strong>只负责 status / 心跳存在性证明</strong>
          <div class="table-cell-stack">
            <span>发送内容：online、lampStatus、timestamp</span>
            <span class="inline-note">
              当前状态：{{ heartbeatStateText }}
            </span>
            <span class="inline-note">
              调度方式：每 {{ activeDevice?.statusEvery ?? "--" }} 轮发送一次心跳
            </span>
            <span class="inline-note">
              最近心跳：{{ activeDevice?.lastStatusAt || "--" }}
            </span>
          </div>
        </div>

        <div class="summary-box">
          <span>TelemetryPublisher</span>
          <strong>只负责 telemetry / 光照电压等业务数据</strong>
          <div class="table-cell-stack">
            <span>发送内容：lightIntensity、lampStatus、voltage、timestamp</span>
            <span class="inline-note">
              当前状态：{{ telemetryStateText }}
            </span>
            <span class="inline-note">
              调度方式：每 {{ activeDevice?.telemetryIntervalSeconds ?? "--" }} 秒尝试发送一次数据
            </span>
            <span class="inline-note">
              最近数据：{{ activeDevice?.lastTelemetryAt || "--" }}
            </span>
          </div>
        </div>
      </div>

      <div class="button-row simulator-actions-row">
        <span class="inline-note">
          页面上的“停数据/开数据”只作用于 TelemetryPublisher；HeartbeatPublisher 仍持续发送心跳，用于确认传感器仍然存在。
        </span>
      </div>
    </PanelCard>

    <PanelCard
      title="传感器模拟列表"
      subtitle="运行状态控制整个模拟器；数据发送可单独关闭；心跳仍会按轮次继续发送。"
    >
      <div v-if="refreshing && !devices.length" class="placeholder-box">正在加载模拟器设备...</div>
      <div v-else class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>传感器编码</th>
              <th>传感器名称</th>
              <th>位置</th>
              <th>运行状态</th>
              <th>数据发送</th>
              <th>心跳发送</th>
              <th>系统状态</th>
              <th>当前光照</th>
              <th>灯状态</th>
              <th>发送间隔</th>
              <th>数据次数</th>
              <th>最近命令</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="device in devices" :key="device.deviceId">
              <td>{{ device.deviceCode }}</td>
              <td>{{ device.deviceName }}</td>
              <td>{{ device.location || "-" }}</td>
              <td>
                <StatusBadge
                  :status="device.running ? 'success' : 'info'"
                  :text="device.running ? '运行中' : '已停止'"
                />
              </td>
              <td>
                <StatusBadge
                  :status="device.running && device.telemetryEnabled ? 'success' : 'info'"
                  :text="device.running ? (device.telemetryEnabled ? '发送中' : '已关闭') : '未运行'"
                />
              </td>
              <td>
                <StatusBadge
                  :status="device.running ? 'online' : 'offline'"
                  :text="device.running ? (device.online ? '发送在线心跳' : '发送离线心跳') : '已停止'"
                />
              </td>
              <td>
                <StatusBadge
                  :status="device.systemStatus"
                  :text="device.systemStatus === 'online' ? '系统在线' : '系统离线'"
                />
              </td>
              <td>{{ device.currentLightIntensity }} lx</td>
              <td>{{ device.lampStatus.toUpperCase() }}</td>
              <td>{{ device.telemetryIntervalSeconds }}s / 每 {{ device.statusEvery }} 轮发心跳</td>
              <td>{{ device.publishCount }}</td>
              <td>
                <div class="table-cell-stack">
                  <span>{{ device.lastCommand || "--" }}</span>
                  <span class="inline-note">{{ device.lastCommandAt || "--" }}</span>
                </div>
              </td>
              <td>
                <div class="button-row simulator-device-actions">
                  <button
                    class="ghost-button"
                    type="button"
                    :disabled="pendingDeviceId === device.deviceId"
                    @click="toggleDevice(device)"
                  >
                    {{ pendingDeviceId === device.deviceId ? "处理中..." : device.running ? "停止" : "启动" }}
                  </button>
                  <button
                    class="ghost-button"
                    type="button"
                    :disabled="pendingDeviceId === device.deviceId"
                    @click="toggleTelemetry(device)"
                  >
                    {{
                      pendingDeviceId === device.deviceId
                        ? "处理中..."
                        : device.telemetryEnabled
                          ? "停数据"
                          : "开数据"
                    }}
                  </button>
                  <button
                    class="ghost-button"
                    type="button"
                    :disabled="pendingDeviceId === device.deviceId"
                    @click="openEditModal(device)"
                  >
                    编辑
                  </button>
                  <button
                    class="ghost-button"
                    type="button"
                    :disabled="pendingDeviceId === device.deviceId"
                    @click="handleDeleteDevice(device)"
                  >
                    删除
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!devices.length">
              <td colspan="13" class="table-empty">当前没有可管理的模拟传感器</td>
            </tr>
          </tbody>
        </table>
      </div>
    </PanelCard>

    <PanelCard title="运行日志" subtitle="显示模拟器连接、心跳、数据发送和命令接收日志">
      <div class="button-row simulator-actions-row simulator-toolbar">
        <label class="simulator-filter">
          <span>级别筛选</span>
          <select v-model="logLevelFilter" @change="handleLogFilterChange">
            <option value="">全部</option>
            <option value="INFO">INFO</option>
            <option value="WARN">WARN</option>
            <option value="ERROR">ERROR</option>
          </select>
        </label>
        <button class="ghost-button" type="button" :disabled="refreshingLogs" @click="loadLogs">
          {{ refreshingLogs ? "刷新中..." : "刷新日志" }}
        </button>
        <button class="ghost-button" type="button" :disabled="clearingLogs" @click="handleClearLogs">
          {{ clearingLogs ? "清空中..." : "清空日志" }}
        </button>
        <span class="inline-note">日志和状态每 5 秒自动刷新一次。</span>
      </div>

      <div class="simulator-log-list scroll-log-panel">
        <div v-for="entry in logs" :key="`${entry.createdAt}-${entry.message}`" class="simulator-log-item">
          <div class="simulator-log-meta">
            <StatusBadge
              :status="entry.level === 'ERROR' ? 'offline' : entry.level === 'WARN' ? 'warning' : 'info'"
              :text="entry.level"
            />
            <span>{{ entry.createdAt }}</span>
          </div>
          <strong>{{ entry.message }}</strong>
        </div>
        <div v-if="!logs.length" class="placeholder-box">暂无运行日志</div>
      </div>
    </PanelCard>

    <div v-if="editingDevice" class="simulator-modal-backdrop" @click.self="closeEditModal">
      <section class="simulator-modal">
        <header class="section-header">
          <div>
            <p class="section-kicker">Sensor Edit</p>
            <h3>编辑 {{ editingDevice.deviceCode }}</h3>
          </div>
          <button class="ghost-button" type="button" @click="closeEditModal">关闭</button>
        </header>

        <div class="form-grid">
          <label>
            <span>传感器名称</span>
            <input v-model="editForm.deviceName" type="text" />
          </label>
          <label>
            <span>安装位置</span>
            <input v-model="editForm.location" type="text" />
          </label>
          <label>
            <span>基础光照</span>
            <input v-model.number="editForm.baseLight" type="number" min="0" />
          </label>
          <label>
            <span>波动范围</span>
            <input v-model.number="editForm.variance" type="number" min="0" />
          </label>
          <label>
            <span>基础电压</span>
            <input v-model.number="editForm.voltageBase" type="number" step="0.1" />
          </label>
          <label>
            <span>数据发送间隔（秒）</span>
            <input v-model.number="editForm.telemetryIntervalSeconds" type="number" min="1" />
          </label>
          <label>
            <span>心跳轮次</span>
            <input v-model.number="editForm.statusEvery" type="number" min="1" />
          </label>
          <label class="checkbox-field">
            <input v-model="editForm.telemetryEnabled" type="checkbox" />
            <span>启用数据发送（关闭后仅保留心跳）</span>
          </label>
          <label class="checkbox-field">
            <input v-model="editForm.online" type="checkbox" />
            <span>心跳上报 online=true</span>
          </label>
          <label class="checkbox-field">
            <input v-model="editForm.running" type="checkbox" />
            <span>保存后保持运行</span>
          </label>
        </div>

        <div class="button-row simulator-actions-row">
          <button class="primary-button" type="button" :disabled="savingEdit" @click="handleSaveEdit">
            {{ savingEdit ? "保存中..." : "保存参数" }}
          </button>
          <button class="ghost-button" type="button" :disabled="savingEdit" @click="closeEditModal">
            取消
          </button>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";

import PanelCard from "@/components/PanelCard.vue";
import StatCard from "@/components/StatCard.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import {
  clearSimulatorLogs,
  deleteSimulatorDevice,
  getSimulatorConfig,
  getSimulatorDevices,
  getSimulatorLogs,
  startSimulatorDevice,
  stopSimulatorDevice,
  updateSimulatorConfig,
  updateSimulatorDevice,
} from "@/services/api/simulatorService";
import type {
  DashboardStat,
  SimulatorBrokerConfig,
  SimulatorDevice,
  SimulatorLogEntry,
} from "@/types/models";

const config = reactive<SimulatorBrokerConfig>({
  enabled: false,
  host: "",
  port: 1883,
  username: "",
  password: "",
  clientId: "",
  connected: false,
});

const configForm = reactive({
  enabled: false,
  host: "",
  port: 1883,
  username: "",
  password: "",
});

const editForm = reactive({
  deviceName: "",
  location: "",
  baseLight: 120,
  variance: 35,
  voltageBase: 220.5,
  telemetryEnabled: true,
  telemetryIntervalSeconds: 5,
  statusEvery: 1,
  online: true,
  running: true,
});

const devices = ref<SimulatorDevice[]>([]);
const logs = ref<SimulatorLogEntry[]>([]);
const refreshing = ref(false);
const refreshingLogs = ref(false);
const savingConfig = ref(false);
const clearingLogs = ref(false);
const savingEdit = ref(false);
const pendingDeviceId = ref<number | null>(null);
const logLevelFilter = ref("");
const editingDevice = ref<SimulatorDevice | null>(null);
let autoRefreshTimer: number | undefined;

const summaryStats = computed<DashboardStat[]>(() => [
  { label: "模拟传感器数", value: String(devices.value.length), helper: "当前纳入控制台的传感器" },
  {
    label: "运行中",
    value: String(devices.value.filter((item) => item.running).length),
    helper: "会继续发送心跳",
  },
  {
    label: "仅心跳",
    value: String(devices.value.filter((item) => item.running && !item.telemetryEnabled).length),
    helper: "停止数据发送但保留心跳",
  },
  {
    label: "当前日志数",
    value: String(logs.value.length),
    helper: logLevelFilter.value ? `${logLevelFilter.value} 级别日志` : "最近 120 条运行日志",
  },
]);

const activeDevice = computed<SimulatorDevice | null>(() => {
  if (!devices.value.length) {
    return null;
  }
  if (pendingDeviceId.value !== null) {
    return devices.value.find((item) => item.deviceId === pendingDeviceId.value) ?? devices.value[0];
  }
  if (editingDevice.value) {
    return devices.value.find((item) => item.deviceId === editingDevice.value?.deviceId) ?? devices.value[0];
  }
  return devices.value[0];
});

const heartbeatStateText = computed(() => {
  if (!activeDevice.value) {
    return "--";
  }
  if (!activeDevice.value.running) {
    return "未运行";
  }
  return activeDevice.value.online ? "持续发送在线心跳" : "持续发送离线心跳";
});

const telemetryStateText = computed(() => {
  if (!activeDevice.value) {
    return "--";
  }
  if (!activeDevice.value.running) {
    return "未运行";
  }
  return activeDevice.value.telemetryEnabled ? "按间隔发送业务数据" : "已关闭，仅保留心跳";
});

function syncConfigForm() {
  configForm.enabled = config.enabled;
  configForm.host = config.host;
  configForm.port = config.port;
  configForm.username = config.username;
  configForm.password = config.password;
}

function fillEditForm(device: SimulatorDevice) {
  editForm.deviceName = device.deviceName;
  editForm.location = device.location;
  editForm.baseLight = device.baseLight;
  editForm.variance = device.variance;
  editForm.voltageBase = device.voltageBase;
  editForm.telemetryEnabled = device.telemetryEnabled;
  editForm.telemetryIntervalSeconds = device.telemetryIntervalSeconds;
  editForm.statusEvery = device.statusEvery;
  editForm.online = device.online;
  editForm.running = device.running;
}

function buildUpdatePayload(device: SimulatorDevice, overrides?: Partial<typeof editForm>) {
  return {
    deviceName: overrides?.deviceName ?? device.deviceName,
    location: overrides?.location ?? device.location,
    baseLight: overrides?.baseLight ?? device.baseLight,
    variance: overrides?.variance ?? device.variance,
    voltageBase: overrides?.voltageBase ?? device.voltageBase,
    telemetryEnabled: overrides?.telemetryEnabled ?? device.telemetryEnabled,
    telemetryIntervalSeconds: overrides?.telemetryIntervalSeconds ?? device.telemetryIntervalSeconds,
    statusEvery: overrides?.statusEvery ?? device.statusEvery,
    online: overrides?.online ?? device.online,
    running: overrides?.running ?? device.running,
  };
}

async function loadLogs() {
  refreshingLogs.value = true;
  try {
    logs.value = await getSimulatorLogs(120, logLevelFilter.value || undefined);
  } finally {
    refreshingLogs.value = false;
  }
}

async function loadConsoleData() {
  refreshing.value = true;
  try {
    const [nextConfig, nextDevices] = await Promise.all([getSimulatorConfig(), getSimulatorDevices()]);
    Object.assign(config, nextConfig);
    syncConfigForm();
    devices.value = nextDevices;
    await loadLogs();
  } finally {
    refreshing.value = false;
  }
}

async function handleSaveConfig() {
  savingConfig.value = true;
  try {
    const nextConfig = await updateSimulatorConfig({
      enabled: configForm.enabled,
      host: configForm.host.trim(),
      port: Number(configForm.port),
      username: configForm.username.trim(),
      password: configForm.password,
    });
    Object.assign(config, nextConfig);
    syncConfigForm();
    await loadLogs();
  } catch (error) {
    window.alert(error instanceof Error ? error.message : "保存 Broker 配置失败");
  } finally {
    savingConfig.value = false;
  }
}

function openEditModal(device: SimulatorDevice) {
  editingDevice.value = device;
  fillEditForm(device);
}

function closeEditModal() {
  editingDevice.value = null;
}

async function handleSaveEdit() {
  if (!editingDevice.value) {
    return;
  }

  savingEdit.value = true;
  try {
    await updateSimulatorDevice(editingDevice.value.deviceId, {
      deviceName: editForm.deviceName.trim(),
      location: editForm.location.trim(),
      baseLight: Number(editForm.baseLight),
      variance: Number(editForm.variance),
      voltageBase: Number(editForm.voltageBase),
      telemetryEnabled: editForm.telemetryEnabled,
      telemetryIntervalSeconds: Number(editForm.telemetryIntervalSeconds),
      statusEvery: Number(editForm.statusEvery),
      online: editForm.online,
      running: editForm.running,
    });
    closeEditModal();
    await loadConsoleData();
  } catch (error) {
    window.alert(error instanceof Error ? error.message : "保存传感器参数失败");
  } finally {
    savingEdit.value = false;
  }
}

async function toggleDevice(device: SimulatorDevice) {
  pendingDeviceId.value = device.deviceId;
  try {
    if (device.running) {
      await stopSimulatorDevice(device.deviceId);
    } else {
      await startSimulatorDevice(device.deviceId);
    }
    await loadConsoleData();
  } catch (error) {
    window.alert(error instanceof Error ? error.message : "切换传感器运行状态失败");
  } finally {
    pendingDeviceId.value = null;
  }
}

async function toggleTelemetry(device: SimulatorDevice) {
  pendingDeviceId.value = device.deviceId;
  try {
    await updateSimulatorDevice(
      device.deviceId,
      buildUpdatePayload(device, { telemetryEnabled: !device.telemetryEnabled }),
    );
    await loadConsoleData();
  } catch (error) {
    window.alert(error instanceof Error ? error.message : "切换数据发送状态失败");
  } finally {
    pendingDeviceId.value = null;
  }
}

async function handleDeleteDevice(device: SimulatorDevice) {
  if (!window.confirm(`确认删除传感器 ${device.deviceCode} 吗？这会同步删除数据库中的记录。`)) {
    return;
  }

  pendingDeviceId.value = device.deviceId;
  try {
    await deleteSimulatorDevice(device.deviceId);
    if (editingDevice.value?.deviceId === device.deviceId) {
      closeEditModal();
    }
    await loadConsoleData();
  } catch (error) {
    window.alert(error instanceof Error ? error.message : "删除传感器失败");
  } finally {
    pendingDeviceId.value = null;
  }
}

async function handleClearLogs() {
  if (!window.confirm("确认清空当前运行日志吗？")) {
    return;
  }

  clearingLogs.value = true;
  try {
    await clearSimulatorLogs();
    await loadLogs();
  } catch (error) {
    window.alert(error instanceof Error ? error.message : "清空日志失败");
  } finally {
    clearingLogs.value = false;
  }
}

async function handleLogFilterChange() {
  await loadLogs();
}

onMounted(async () => {
  await loadConsoleData();
  autoRefreshTimer = window.setInterval(() => {
    void loadConsoleData();
  }, 5000);
});

onBeforeUnmount(() => {
  if (autoRefreshTimer) {
    window.clearInterval(autoRefreshTimer);
  }
});
</script>
