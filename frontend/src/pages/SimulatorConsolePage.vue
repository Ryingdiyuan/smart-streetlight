<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Simulator</p>
        <h3>传感器模拟控制台</h3>
      </div>
      <p class="section-note">
        页面内直接管理 MQTT 模拟器，支持 Broker 配置、设备启停、参数编辑、新增删除和运行日志查看。
      </p>
    </header>

    <div class="stats-grid">
      <StatCard v-for="item in summaryStats" :key="item.label" :stat="item" />
    </div>

    <div class="content-grid two-columns">
      <PanelCard title="Broker 配置" subtitle="显示并修改当前模拟器连接参数">
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

      <PanelCard title="新增传感器" subtitle="新增设备并立即加入模拟器">
        <div class="form-grid">
          <label>
            <span>设备编码</span>
            <input v-model="createForm.deviceCode" type="text" placeholder="例如 SL-010" />
          </label>
          <label>
            <span>设备名称</span>
            <input v-model="createForm.deviceName" type="text" placeholder="例如 图书馆路灯" />
          </label>
          <label>
            <span>安装位置</span>
            <input v-model="createForm.location" type="text" placeholder="例如 图书馆门口" />
          </label>
          <label>
            <span>基础光照</span>
            <input v-model.number="createForm.baseLight" type="number" min="0" />
          </label>
          <label>
            <span>波动范围</span>
            <input v-model.number="createForm.variance" type="number" min="0" />
          </label>
          <label>
            <span>基础电压</span>
            <input v-model.number="createForm.voltageBase" type="number" step="0.1" />
          </label>
          <label>
            <span>遥测间隔（秒）</span>
            <input v-model.number="createForm.telemetryIntervalSeconds" type="number" min="1" />
          </label>
          <label>
            <span>心跳轮次</span>
            <input v-model.number="createForm.statusEvery" type="number" min="1" />
          </label>
          <label class="checkbox-field">
            <input v-model="createForm.online" type="checkbox" />
            <span>模拟上报 online=true</span>
          </label>
          <label class="checkbox-field">
            <input v-model="createForm.autoStart" type="checkbox" />
            <span>创建后立即开始模拟</span>
          </label>
        </div>

        <div class="button-row simulator-actions-row">
          <button class="primary-button" type="button" :disabled="creatingDevice" @click="handleCreateDevice">
            {{ creatingDevice ? "新增中..." : "新增传感器" }}
          </button>
          <span class="inline-note">设备将同步写入数据库并进入下方控制表。</span>
        </div>
      </PanelCard>
    </div>

    <PanelCard title="设备模拟列表" subtitle="运行状态表示是否发数据；模拟上报状态表示下一次发出的 online 值；系统设备状态来自设备列表的真实状态">
      <div v-if="refreshing && !devices.length" class="placeholder-box">正在加载模拟器设备...</div>
      <div v-else class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>设备编码</th>
              <th>设备名称</th>
              <th>位置</th>
              <th>运行状态</th>
              <th>模拟上报状态</th>
              <th>系统设备状态</th>
              <th>当前光照</th>
              <th>灯状态</th>
              <th>间隔</th>
              <th>发送次数</th>
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
                <StatusBadge :status="device.running ? 'success' : 'info'" :text="device.running ? '运行中' : '已停止'" />
              </td>
              <td>
                <StatusBadge :status="device.online ? 'online' : 'offline'" :text="device.online ? '上报在线' : '上报离线'" />
              </td>
              <td>
                <StatusBadge
                  :status="device.systemStatus"
                  :text="device.systemStatus === 'online' ? '系统在线' : '系统离线'"
                />
              </td>
              <td>{{ device.currentLightIntensity }} lx</td>
              <td>{{ device.lampStatus.toUpperCase() }}</td>
              <td>{{ device.telemetryIntervalSeconds }}s / {{ device.statusEvery }}轮</td>
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
              <td colspan="12" class="table-empty">当前没有可管理的模拟设备</td>
            </tr>
          </tbody>
        </table>
      </div>
    </PanelCard>

    <PanelCard title="运行日志" subtitle="显示模拟器连接、发送、命令接收等日志">
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
        <span class="inline-note">自动每 5 秒刷新一次。</span>
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
            <p class="section-kicker">Device Edit</p>
            <h3>编辑 {{ editingDevice.deviceCode }}</h3>
          </div>
          <button class="ghost-button" type="button" @click="closeEditModal">关闭</button>
        </header>

        <div class="form-grid">
          <label>
            <span>设备名称</span>
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
            <span>遥测间隔（秒）</span>
            <input v-model.number="editForm.telemetryIntervalSeconds" type="number" min="1" />
          </label>
          <label>
            <span>心跳轮次</span>
            <input v-model.number="editForm.statusEvery" type="number" min="1" />
          </label>
          <label class="checkbox-field">
            <input v-model="editForm.online" type="checkbox" />
            <span>模拟上报 online=true</span>
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
  createSimulatorDevice,
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

const createForm = reactive({
  deviceCode: "",
  deviceName: "",
  location: "",
  baseLight: 120,
  variance: 35,
  voltageBase: 220.5,
  telemetryIntervalSeconds: 5,
  statusEvery: 1,
  online: true,
  autoStart: true,
});

const editForm = reactive({
  deviceName: "",
  location: "",
  baseLight: 120,
  variance: 35,
  voltageBase: 220.5,
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
const creatingDevice = ref(false);
const clearingLogs = ref(false);
const savingEdit = ref(false);
const pendingDeviceId = ref<number | null>(null);
const logLevelFilter = ref("");
const editingDevice = ref<SimulatorDevice | null>(null);
let autoRefreshTimer: number | undefined;

const summaryStats = computed<DashboardStat[]>(() => [
  { label: "模拟设备数", value: String(devices.value.length), helper: "当前纳入控制台的设备" },
  {
    label: "运行中设备",
    value: String(devices.value.filter((item) => item.running).length),
    helper: "正在持续发送 telemetry/status",
  },
  {
    label: "Broker 连接",
    value: config.connected ? "已连接" : "未连接",
    helper: `${config.host || "--"}:${config.port || 0}`,
  },
  {
    label: "当前日志数",
    value: String(logs.value.length),
    helper: logLevelFilter.value ? `${logLevelFilter.value} 级别日志` : "最近 120 条运行日志",
  },
]);

function syncConfigForm() {
  configForm.enabled = config.enabled;
  configForm.host = config.host;
  configForm.port = config.port;
  configForm.username = config.username;
  configForm.password = config.password;
}

function resetCreateForm() {
  createForm.deviceCode = "";
  createForm.deviceName = "";
  createForm.location = "";
  createForm.baseLight = 120;
  createForm.variance = 35;
  createForm.voltageBase = 220.5;
  createForm.telemetryIntervalSeconds = 5;
  createForm.statusEvery = 1;
  createForm.online = true;
  createForm.autoStart = true;
}

function fillEditForm(device: SimulatorDevice) {
  editForm.deviceName = device.deviceName;
  editForm.location = device.location;
  editForm.baseLight = device.baseLight;
  editForm.variance = device.variance;
  editForm.voltageBase = device.voltageBase;
  editForm.telemetryIntervalSeconds = device.telemetryIntervalSeconds;
  editForm.statusEvery = device.statusEvery;
  editForm.online = device.online;
  editForm.running = device.running;
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
    const [nextConfig, nextDevices] = await Promise.all([
      getSimulatorConfig(),
      getSimulatorDevices(),
    ]);

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

async function handleCreateDevice() {
  if (!createForm.deviceCode.trim() || !createForm.deviceName.trim()) {
    window.alert("设备编码和设备名称不能为空");
    return;
  }

  creatingDevice.value = true;
  try {
    await createSimulatorDevice({
      deviceCode: createForm.deviceCode.trim(),
      deviceName: createForm.deviceName.trim(),
      location: createForm.location.trim(),
      baseLight: Number(createForm.baseLight),
      variance: Number(createForm.variance),
      voltageBase: Number(createForm.voltageBase),
      telemetryIntervalSeconds: Number(createForm.telemetryIntervalSeconds),
      statusEvery: Number(createForm.statusEvery),
      online: createForm.online,
      autoStart: createForm.autoStart,
    });
    resetCreateForm();
    await loadConsoleData();
  } catch (error) {
    window.alert(error instanceof Error ? error.message : "新增传感器失败");
  } finally {
    creatingDevice.value = false;
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
      telemetryIntervalSeconds: Number(editForm.telemetryIntervalSeconds),
      statusEvery: Number(editForm.statusEvery),
      online: editForm.online,
      running: editForm.running,
    });
    closeEditModal();
    await loadConsoleData();
  } catch (error) {
    window.alert(error instanceof Error ? error.message : "保存设备参数失败");
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
    window.alert(error instanceof Error ? error.message : "切换设备运行状态失败");
  } finally {
    pendingDeviceId.value = null;
  }
}

async function handleDeleteDevice(device: SimulatorDevice) {
  if (!window.confirm(`确认删除设备 ${device.deviceCode} 吗？这会同步删除数据库中的设备记录。`)) {
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
    window.alert(error instanceof Error ? error.message : "删除设备失败");
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
