<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Sensor Simulator</p>
        <h3>传感器接入控制台</h3>
      </div>
      <p class="section-note">
        在这里创建和运行硬件传感器模拟。路灯档案与绑定关系由业务前端维护，未绑定传感器上报会被后端丢弃。
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

      <PanelCard title="新增传感器" subtitle="在硬件模拟器创建传感器档案，并可直接启动模拟上报">
        <div class="form-grid">
          <label>
            <span>传感器编码</span>
            <input v-model="createForm.sensorCode" type="text" placeholder="例如 SR-001" />
          </label>
          <label>
            <span>传感器名称</span>
            <input v-model="createForm.sensorName" type="text" placeholder="例如 北门光照传感器" />
          </label>
          <label>
            <span>安装位置</span>
            <input v-model="createForm.location" type="text" placeholder="例如 北门路口" />
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
          <label class="checkbox-field">
            <input v-model="createForm.telemetryEnabled" type="checkbox" />
            <span>启用数据发送（关闭后仅保留心跳）</span>
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
            <span>创建后立即启动</span>
          </label>
        </div>

        <div class="button-row simulator-actions-row">
          <button class="primary-button" type="button" :disabled="creatingSensor" @click="handleCreateSensor">
            {{ creatingSensor ? "创建中..." : "注册传感器" }}
          </button>
        </div>
        <p v-if="createMessage" class="inline-note">{{ createMessage }}</p>
      </PanelCard>
    </div>

    <PanelCard title="发送架构" subtitle="前端直接展示心跳类与数据类已拆分管理">
      <div class="detail-tip-grid">
        <div class="summary-box">
          <span>当前查看传感器</span>
          <strong>{{ activeSensor ? activeSensor.sensorCode : "--" }}</strong>
        </div>
        <div class="summary-box">
          <span>运行状态</span>
          <strong>{{ activeSensor ? (activeSensor.running ? "运行中" : "已停止") : "--" }}</strong>
        </div>
      </div>

      <div class="content-grid two-columns">
        <div class="summary-box">
          <span>HeartbeatPublisher</span>
          <strong>只负责 status / 心跳存在性证明</strong>
          <div class="table-cell-stack">
            <span>发送内容：online、lampStatus、timestamp</span>
            <span class="inline-note">当前状态：{{ heartbeatStateText }}</span>
            <span class="inline-note">调度方式：每 {{ activeSensor?.statusEvery ?? "--" }} 轮发送一次心跳</span>
            <span class="inline-note">最近心跳：{{ activeSensor?.lastStatusAt || "--" }}</span>
          </div>
        </div>

        <div class="summary-box">
          <span>TelemetryPublisher</span>
          <strong>只负责 telemetry / 光照电压等业务数据</strong>
          <div class="table-cell-stack">
            <span>发送内容：lightIntensity、lampStatus、voltage、timestamp</span>
            <span class="inline-note">当前状态：{{ telemetryStateText }}</span>
            <span class="inline-note">调度方式：每 {{ activeSensor?.telemetryIntervalSeconds ?? "--" }} 秒尝试发送一次数据</span>
            <span class="inline-note">最近数据：{{ activeSensor?.lastTelemetryAt || "--" }}</span>
          </div>
        </div>
      </div>

      <div class="button-row simulator-actions-row">
        <span class="inline-note">
          页面上的“停数据/开数据”只作用于 TelemetryPublisher；HeartbeatPublisher 仍持续发送心跳，用于确认传感器仍然存在。
        </span>
      </div>
    </PanelCard>

    <PanelCard title="传感器模拟列表" subtitle="运行状态控制整个模拟器；数据发送可单独关闭；心跳仍会按轮次继续发送。">
      <div v-if="refreshing && !sensors.length" class="placeholder-box">正在加载模拟器传感器...</div>
      <div v-else class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>传感器编码</th>
              <th>传感器名称</th>
              <th>位置</th>
              <th>绑定路灯</th>
              <th>控制模式</th>
              <th>运行状态</th>
              <th>数据发送</th>
              <th>心跳发送</th>
              <th>当前光照</th>
              <th>灯状态</th>
              <th>间隔</th>
              <th>发送次数</th>
              <th>最近命令</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="sensor in sensors" :key="sensor.sensorId">
              <td>{{ sensor.sensorCode }}</td>
              <td>{{ sensor.sensorName }}</td>
              <td>{{ sensor.location || "-" }}</td>
              <td>
                <div class="table-cell-stack">
                  <span>{{ sensor.boundDeviceCode || "未绑定" }}</span>
                  <span class="inline-note">{{ sensor.boundDeviceName || "需在业务前端绑定" }}</span>
                </div>
              </td>
              <td>{{ sensor.controlMode === "auto" ? "自动" : sensor.controlMode === "manual" ? "手动" : "--" }}</td>
              <td>
                <StatusBadge :status="sensor.running ? 'success' : 'info'" :text="sensor.running ? '运行中' : '已停止'" />
              </td>
              <td>
                <StatusBadge
                  :status="sensor.running && sensor.telemetryEnabled ? 'success' : 'info'"
                  :text="sensor.running ? (sensor.telemetryEnabled ? '发送中' : '已关闭') : '未运行'"
                />
              </td>
              <td>
                <StatusBadge
                  :status="sensor.running ? 'online' : 'offline'"
                  :text="sensor.running ? (sensor.online ? '发送在线心跳' : '发送离线心跳') : '已停止'"
                />
              </td>
              <td>{{ sensor.currentLightIntensity }} lx</td>
              <td>{{ sensor.lampStatus.toUpperCase() }}</td>
              <td>{{ sensor.telemetryIntervalSeconds }}s / 每 {{ sensor.statusEvery }} 轮</td>
              <td>{{ sensor.publishCount }}</td>
              <td>
                <div class="table-cell-stack">
                  <span>{{ sensor.lastCommand || "--" }}</span>
                  <span class="inline-note">{{ sensor.lastCommandAt || "--" }}</span>
                </div>
              </td>
              <td>
                <div class="button-row simulator-device-actions">
                  <button
                    class="ghost-button"
                    type="button"
                    :disabled="pendingSensorId === sensor.sensorId"
                    @click="toggleSensor(sensor)"
                  >
                    {{ pendingSensorId === sensor.sensorId ? "处理中..." : sensor.running ? "停止" : "启动" }}
                  </button>
                  <button
                    class="ghost-button"
                    type="button"
                    :disabled="pendingSensorId === sensor.sensorId"
                    @click="toggleTelemetry(sensor)"
                  >
                    {{
                      pendingSensorId === sensor.sensorId
                        ? "处理中..."
                        : sensor.telemetryEnabled
                          ? "停数据"
                          : "开数据"
                    }}
                  </button>
                  <button
                    class="ghost-button"
                    type="button"
                    :disabled="pendingSensorId === sensor.sensorId"
                    @click="openEditModal(sensor)"
                  >
                    编辑
                  </button>
                  <button
                    class="ghost-button"
                    type="button"
                    :disabled="pendingSensorId === sensor.sensorId"
                    @click="handleDeleteSensor(sensor)"
                  >
                    删除
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!sensors.length">
              <td colspan="13" class="table-empty">当前没有可管理的模拟传感器</td>
            </tr>
          </tbody>
        </table>
      </div>
    </PanelCard>

    <PanelCard title="运行日志" subtitle="显示模拟器连接、心跳、数据发送和命令接收等日志">
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

    <div v-if="editingSensor" class="simulator-modal-backdrop" @click.self="closeEditModal">
      <section class="simulator-modal">
        <header class="section-header">
          <div>
            <p class="section-kicker">Sensor Edit</p>
            <h3>编辑 {{ editingSensor.sensorCode }}</h3>
          </div>
          <button class="ghost-button" type="button" @click="closeEditModal">关闭</button>
        </header>

        <div class="form-grid">
          <label>
            <span>传感器名称</span>
            <input v-model="editForm.sensorName" type="text" />
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
          <label class="checkbox-field">
            <input v-model="editForm.telemetryEnabled" type="checkbox" />
            <span>启用数据发送（关闭后仅保留心跳）</span>
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
  deleteSimulatorSensor,
  getSimulatorConfig,
  getSimulatorLogs,
  getSimulatorSensors,
  registerSimulatorSensor,
  startSimulatorSensor,
  stopSimulatorSensor,
  updateSimulatorConfig,
  updateSimulatorSensor,
} from "@/services/api/simulatorService";
import type {
  DashboardStat,
  SimulatorBrokerConfig,
  SimulatorLogEntry,
  SimulatorSensor,
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
  sensorCode: "",
  sensorName: "",
  location: "",
  baseLight: 120,
  variance: 35,
  voltageBase: 220.5,
  telemetryEnabled: true,
  telemetryIntervalSeconds: 5,
  statusEvery: 1,
  online: true,
  autoStart: true,
});

const editForm = reactive({
  sensorName: "",
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

const sensors = ref<SimulatorSensor[]>([]);
const logs = ref<SimulatorLogEntry[]>([]);
const refreshing = ref(false);
const refreshingLogs = ref(false);
const savingConfig = ref(false);
const clearingLogs = ref(false);
const creatingSensor = ref(false);
const savingEdit = ref(false);
const pendingSensorId = ref<number | null>(null);
const logLevelFilter = ref("");
const createMessage = ref("");
const editingSensor = ref<SimulatorSensor | null>(null);
let autoRefreshTimer: number | undefined;

const summaryStats = computed<DashboardStat[]>(() => [
  { label: "模拟传感器数", value: String(sensors.value.length), helper: "当前纳入控制台的传感器" },
  {
    label: "运行中传感器",
    value: String(sensors.value.filter((item) => item.running).length),
    helper: "正在持续发送心跳",
  },
  {
    label: "仅心跳",
    value: String(sensors.value.filter((item) => item.running && !item.telemetryEnabled).length),
    helper: "停止数据发送但保留心跳",
  },
  {
    label: "已绑定路灯",
    value: String(sensors.value.filter((item) => item.boundDeviceId != null).length),
    helper: "绑定后数据才会生效",
  },
  {
    label: "Broker 连接",
    value: config.connected ? "已连接" : "未连接",
    helper: `${config.host || "--"}:${config.port || 0}`,
  },
]);

const activeSensor = computed<SimulatorSensor | null>(() => {
  if (!sensors.value.length) {
    return null;
  }
  if (pendingSensorId.value !== null) {
    return sensors.value.find((item) => item.sensorId === pendingSensorId.value) ?? sensors.value[0];
  }
  if (editingSensor.value) {
    return sensors.value.find((item) => item.sensorId === editingSensor.value?.sensorId) ?? sensors.value[0];
  }
  return sensors.value[0];
});

const heartbeatStateText = computed(() => {
  if (!activeSensor.value) {
    return "--";
  }
  if (!activeSensor.value.running) {
    return "未运行";
  }
  return activeSensor.value.online ? "持续发送在线心跳" : "持续发送离线心跳";
});

const telemetryStateText = computed(() => {
  if (!activeSensor.value) {
    return "--";
  }
  if (!activeSensor.value.running) {
    return "未运行";
  }
  return activeSensor.value.telemetryEnabled ? "按间隔发送业务数据" : "已关闭，仅保留心跳";
});

function syncConfigForm() {
  configForm.enabled = config.enabled;
  configForm.host = config.host;
  configForm.port = config.port;
  configForm.username = config.username;
  configForm.password = config.password;
}

function resetCreateForm() {
  createForm.sensorCode = "";
  createForm.sensorName = "";
  createForm.location = "";
  createForm.baseLight = 120;
  createForm.variance = 35;
  createForm.voltageBase = 220.5;
  createForm.telemetryEnabled = true;
  createForm.telemetryIntervalSeconds = 5;
  createForm.statusEvery = 1;
  createForm.online = true;
  createForm.autoStart = true;
}

function fillEditForm(sensor: SimulatorSensor) {
  editForm.sensorName = sensor.sensorName;
  editForm.location = sensor.location;
  editForm.baseLight = sensor.baseLight;
  editForm.variance = sensor.variance;
  editForm.voltageBase = sensor.voltageBase;
  editForm.telemetryEnabled = sensor.telemetryEnabled;
  editForm.telemetryIntervalSeconds = sensor.telemetryIntervalSeconds;
  editForm.statusEvery = sensor.statusEvery;
  editForm.online = sensor.online;
  editForm.running = sensor.running;
}

function buildUpdatePayload(sensor: SimulatorSensor, overrides?: Partial<typeof editForm>) {
  return {
    sensorName: overrides?.sensorName ?? sensor.sensorName,
    location: overrides?.location ?? sensor.location,
    baseLight: overrides?.baseLight ?? sensor.baseLight,
    variance: overrides?.variance ?? sensor.variance,
    voltageBase: overrides?.voltageBase ?? sensor.voltageBase,
    telemetryEnabled: overrides?.telemetryEnabled ?? sensor.telemetryEnabled,
    telemetryIntervalSeconds: overrides?.telemetryIntervalSeconds ?? sensor.telemetryIntervalSeconds,
    statusEvery: overrides?.statusEvery ?? sensor.statusEvery,
    online: overrides?.online ?? sensor.online,
    running: overrides?.running ?? sensor.running,
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
    const [nextConfig, nextSensors] = await Promise.all([getSimulatorConfig(), getSimulatorSensors()]);
    Object.assign(config, nextConfig);
    syncConfigForm();
    sensors.value = nextSensors;
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

async function handleCreateSensor() {
  if (!createForm.sensorCode.trim() || !createForm.sensorName.trim()) {
    createMessage.value = "请先填写传感器编码和名称";
    return;
  }

  creatingSensor.value = true;
  createMessage.value = "";
  try {
    await registerSimulatorSensor({
      sensorCode: createForm.sensorCode.trim(),
      sensorName: createForm.sensorName.trim(),
      location: createForm.location.trim(),
      baseLight: Number(createForm.baseLight),
      variance: Number(createForm.variance),
      voltageBase: Number(createForm.voltageBase),
      telemetryEnabled: createForm.telemetryEnabled,
      telemetryIntervalSeconds: Number(createForm.telemetryIntervalSeconds),
      statusEvery: Number(createForm.statusEvery),
      online: createForm.online,
      autoStart: createForm.autoStart,
    });
    resetCreateForm();
    createMessage.value = "传感器已注册。绑定路灯前，其上报数据不会被系统接收。";
    await loadConsoleData();
  } catch (error) {
    createMessage.value = error instanceof Error ? error.message : "传感器注册失败";
  } finally {
    creatingSensor.value = false;
  }
}

function openEditModal(sensor: SimulatorSensor) {
  editingSensor.value = sensor;
  fillEditForm(sensor);
}

function closeEditModal() {
  editingSensor.value = null;
}

async function handleSaveEdit() {
  if (!editingSensor.value) {
    return;
  }

  savingEdit.value = true;
  try {
    await updateSimulatorSensor(editingSensor.value.sensorId, {
      sensorName: editForm.sensorName.trim(),
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

async function toggleSensor(sensor: SimulatorSensor) {
  pendingSensorId.value = sensor.sensorId;
  try {
    if (sensor.running) {
      await stopSimulatorSensor(sensor.sensorId);
    } else {
      await startSimulatorSensor(sensor.sensorId);
    }
    await loadConsoleData();
  } catch (error) {
    window.alert(error instanceof Error ? error.message : "切换传感器运行状态失败");
  } finally {
    pendingSensorId.value = null;
  }
}

async function toggleTelemetry(sensor: SimulatorSensor) {
  pendingSensorId.value = sensor.sensorId;
  try {
    await updateSimulatorSensor(
      sensor.sensorId,
      buildUpdatePayload(sensor, { telemetryEnabled: !sensor.telemetryEnabled }),
    );
    await loadConsoleData();
  } catch (error) {
    window.alert(error instanceof Error ? error.message : "切换数据发送状态失败");
  } finally {
    pendingSensorId.value = null;
  }
}

async function handleDeleteSensor(sensor: SimulatorSensor) {
  if (!window.confirm(`确认删除传感器 ${sensor.sensorCode} 吗？`)) {
    return;
  }

  pendingSensorId.value = sensor.sensorId;
  try {
    await deleteSimulatorSensor(sensor.sensorId);
    if (editingSensor.value?.sensorId === sensor.sensorId) {
      closeEditModal();
    }
    await loadConsoleData();
  } catch (error) {
    window.alert(error instanceof Error ? error.message : "删除传感器失败");
  } finally {
    pendingSensorId.value = null;
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

<style scoped>
.simulator-actions-row,
.simulator-device-actions {
  flex-wrap: wrap;
}

.table-cell-stack {
  display: grid;
  gap: 4px;
}

.simulator-log-list {
  display: grid;
  gap: 12px;
}

.simulator-log-item {
  display: grid;
  gap: 8px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.simulator-log-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #94a3b8;
  font-size: 12px;
}

.simulator-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(2, 6, 23, 0.62);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 40;
}

.simulator-modal {
  width: min(760px, 100%);
  max-height: calc(100vh - 48px);
  overflow: auto;
  padding: 24px;
  border-radius: 18px;
  background: #0f172a;
  border: 1px solid rgba(148, 163, 184, 0.2);
}
</style>
