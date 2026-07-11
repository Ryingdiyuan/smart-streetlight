<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Device Detail</p>
        <h3>设备详情</h3>
      </div>
      <div class="button-row">
        <p class="section-note">查看设备详情、阈值配置、控制日志和关联告警。</p>
        <button class="ghost-button" type="button" @click="goBackToList">返回设备列表</button>
        <button
          v-if="canOperateDevices"
          class="danger-button"
          type="button"
          :disabled="deletingDevice"
          @click="handleDeleteDevice"
        >
          {{ deletingDevice ? "删除中..." : "删除路灯" }}
        </button>
      </div>
    </header>

    <div v-if="device" class="stats-grid">
      <StatCard v-for="item in overviewStats" :key="item.label" :stat="item" />
    </div>

    <div v-if="device" class="content-grid two-columns">
      <PanelCard title="基础信息" :subtitle="`设备 ID：${route.params.id}`">
        <dl class="detail-list">
          <div>
            <dt>设备编号</dt>
            <dd>{{ device.deviceCode }}</dd>
          </div>
          <div>
            <dt>在线状态</dt>
            <dd>
              <StatusBadge :status="device.status" :text="device.status === 'online' ? '在线' : '离线'" />
            </dd>
          </div>
          <div>
            <dt>当前光照</dt>
            <dd>{{ device.currentLightIntensity }} lx</dd>
          </div>
          <div>
            <dt>路灯状态</dt>
            <dd>
              <StatusBadge
                :status="device.lampStatus === 'ON' ? 'success' : 'info'"
                :text="device.lampStatus"
              />
            </dd>
          </div>
          <div>
            <dt>安装位置</dt>
            <dd>{{ device.location }}</dd>
          </div>
          <div>
            <dt>最近心跳</dt>
            <dd>{{ device.lastHeartbeatAt }}</dd>
          </div>
        </dl>

        <div v-if="canOperateDevices" class="binding-manager">
          <div class="binding-header">
            <strong>传感器绑定管理</strong>
            <span class="inline-note">
              {{ device.sensorCode ? `${device.sensorCode} - ${device.sensorName ?? "未命名传感器"}` : "当前未绑定传感器" }}
            </span>
          </div>

          <div class="form-grid">
            <label>
              <span>选择传感器</span>
              <select
                v-model="bindingSensorId"
                :disabled="loadingSensors || bindingSaving"
                @focus="bindingInteracting = true"
                @blur="bindingInteracting = false"
              >
                <option :value="undefined">请选择在线且未绑定的传感器</option>
                <option v-for="sensor in selectableSensors" :key="sensor.id" :value="sensor.id">
                  {{ sensor.sensorCode }} - {{ sensor.sensorName }}
                </option>
              </select>
            </label>
          </div>

          <div class="button-row">
            <button
              class="primary-button"
              type="button"
              :disabled="loadingSensors || bindingSaving || bindingSensorId == null"
              @click="handleBindSensor"
            >
              {{ bindingSaving ? "保存中..." : device.sensorId ? "更新绑定" : "绑定传感器" }}
            </button>
            <button
              class="ghost-button"
              type="button"
              :disabled="bindingSaving || !device.sensorId"
              @click="handleUnbindSensor"
            >
              解绑传感器
            </button>
            <button class="ghost-button" type="button" :disabled="loadingSensors || bindingSaving" @click="loadSelectableSensors">
              {{ loadingSensors ? "刷新中..." : "刷新可选传感器" }}
            </button>
          </div>
        </div>
      </PanelCard>

      <PanelCard title="控制与阈值" subtitle="管理员和维修人员可保存阈值并下发控制命令">
        <div v-if="canOperateDevices" class="button-row">
          <button class="primary-button" @click="handleCommand('TURN_ON')">手动开灯</button>
          <button class="ghost-button" @click="handleCommand('TURN_OFF')">手动关灯</button>
        </div>
        <p v-else class="inline-note">当前角色仅可查看阈值配置，不能执行控制或保存修改。</p>

        <div v-if="canOperateDevices" class="button-row">
          <button class="ghost-button" :disabled="sensorControlSaving" @click="toggleSensorControl">
            {{ sensorControlSaving ? "切换中..." : sensorControlButtonText }}
          </button>
          <span class="inline-note">{{ sensorControlHint }}</span>
        </div>

        <div class="detail-tip-grid">
          <div class="summary-box">
            <strong>传感器控制</strong>
            <span>{{ sensorControlStatusText }}</span>
          </div>
          <div class="summary-box">
            <strong>自动控制</strong>
            <span>{{ threshold.enabled ? "已启用" : "未启用" }}</span>
          </div>
          <div class="summary-box">
            <strong>建议动作</strong>
            <span>{{ thresholdSuggestion }}</span>
          </div>
        </div>

        <div class="form-grid">
          <label>
            <span>开灯阈值</span>
            <input v-model.number="threshold.lowThreshold" type="number" :disabled="!canOperateDevices" />
          </label>
          <label>
            <span>关灯阈值</span>
            <input v-model.number="threshold.highThreshold" type="number" :disabled="!canOperateDevices" />
          </label>
          <label class="checkbox-field">
            <input v-model="threshold.enabled" type="checkbox" :disabled="!canOperateDevices" />
            <span>启用自动控制</span>
          </label>
        </div>

        <div class="button-row">
          <button v-if="canOperateDevices" class="primary-button" @click="saveThreshold">保存阈值</button>
          <span class="inline-note">{{ actionMessage }}</span>
        </div>
      </PanelCard>
    </div>

    <div v-if="device" class="content-grid two-columns">
      <PanelCard title="位置地图" subtitle="GPS 坐标定位">
        <div v-if="hasCoords" class="detail-mini-map-wrapper">
          <div ref="miniMapContainer" class="detail-mini-map"></div>
          <div class="detail-coords-bar">
            <span>纬度 {{ device.latitude?.toFixed(4) }}</span>
            <span class="coord-sep">/</span>
            <span>经度 {{ device.longitude?.toFixed(4) }}</span>
          </div>
        </div>
        <div v-else class="placeholder-box">
          该设备暂无 GPS 坐标信息<br />
          <small>请前往「设备地图」页面设置坐标</small>
        </div>
      </PanelCard>

      <PanelCard title="历史光照曲线" subtitle="设备详情页趋势展示">
        <TrendLineChart :points="device.history" />
      </PanelCard>
    </div>

    <div v-if="device" class="content-grid two-columns">
      <PanelCard title="状态摘要" subtitle="当前设备运行情况">
        <div class="detail-summary-grid">
          <div class="summary-box">
            <strong>历史点位</strong>
            <span>{{ device.history.length }} 条</span>
          </div>
          <div class="summary-box">
            <strong>控制日志</strong>
            <span>{{ device.commandLogs.length }} 条</span>
          </div>
          <div class="summary-box">
            <strong>关联告警</strong>
            <span>{{ device.alarms.length }} 条</span>
          </div>
          <div class="summary-box">
            <strong>阈值区间</strong>
            <span>{{ threshold.lowThreshold }} - {{ threshold.highThreshold }} lx</span>
          </div>
          <div class="summary-box">
            <strong>最新趋势</strong>
            <span>{{ trendLabel }}</span>
          </div>
          <div class="summary-box">
            <strong>最后一次控制</strong>
            <span>{{ lastCommandLabel }}</span>
          </div>
        </div>
      </PanelCard>

      <PanelCard title="最近采样记录" subtitle="用于展示上报历史点位">
        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>时间</th>
                <th>光照强度</th>
                <th>路灯状态</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="point in recentHistory" :key="point.timestamp">
                <td>{{ point.timestamp }}</td>
                <td>{{ point.lightIntensity }} lx</td>
                <td>
                  <StatusBadge
                    :status="point.lampStatus === 'ON' ? 'success' : 'info'"
                    :text="point.lampStatus"
                  />
                </td>
              </tr>
              <tr v-if="!recentHistory.length">
                <td colspan="3" class="table-empty">当前没有采样记录</td>
              </tr>
            </tbody>
          </table>
        </div>
      </PanelCard>
    </div>

    <div v-if="device" class="content-grid two-columns">
      <PanelCard title="运维建议" subtitle="结合当前阈值和设备状态给出提示">
        <div class="detail-summary-grid">
          <div class="summary-box">
            <strong>巡检建议</strong>
            <span>{{ maintenanceSuggestion }}</span>
          </div>
          <div class="summary-box">
            <strong>联调建议</strong>
            <span>{{ integrationSuggestion }}</span>
          </div>
        </div>
      </PanelCard>

      <CommandLogPanel :logs="device.commandLogs" />
    </div>

    <div v-if="device" class="content-grid two-columns">
      <AlarmRecordPanel :alarms="device.alarms" />
      <PanelCard title="位置坐标" subtitle="设备经纬度信息">
        <div class="coord-card-body">
          <div v-if="canOperateDevices && !coordEditing" class="coord-card-actions">
            <button class="ghost-button" type="button" @click="startCoordEdit">编辑</button>
          </div>

          <!-- 编辑模式 -->
          <div v-if="coordEditing" class="coord-edit-form">
            <label>
              <span>纬度</span>
              <input v-model.number="editLatitude" class="search-input" type="number" step="any" placeholder="例如 29.531" />
            </label>
            <label>
              <span>经度</span>
              <input v-model.number="editLongitude" class="search-input" type="number" step="any" placeholder="例如 106.528" />
            </label>
            <label>
              <span>位置描述</span>
              <input v-model="editLocation" class="search-input" type="text" placeholder="例如 操场东侧" maxlength="255" />
            </label>

            <p v-if="coordEditError" class="form-error">{{ coordEditError }}</p>

            <div class="button-row">
              <button class="ghost-button" type="button" :disabled="coordSaving" @click="cancelCoordEdit">取消</button>
              <button class="primary-button" type="button" :disabled="coordSaving" @click="saveCoordEdit">
                {{ coordSaving ? '保存中…' : '保存' }}
              </button>
            </div>
          </div>

          <!-- 查看模式 -->
          <div v-else class="detail-summary-grid">
            <div class="summary-box">
              <strong>纬度</strong>
              <span>{{ device.latitude != null ? device.latitude.toFixed(6) : '暂无' }}</span>
            </div>
            <div class="summary-box">
              <strong>经度</strong>
              <span>{{ device.longitude != null ? device.longitude.toFixed(6) : '暂无' }}</span>
            </div>
            <div class="summary-box">
              <strong>安装位置</strong>
              <span>{{ device.location || '暂无描述' }}</span>
            </div>
            <div class="summary-box">
              <strong>最后心跳</strong>
              <span>{{ device.lastHeartbeatAt }}</span>
            </div>
          </div>
        </div>
      </PanelCard>
    </div>

    <PanelCard v-else title="设备详情" subtitle="数据不存在">
      <div class="placeholder-box">未找到对应设备，请返回列表页重新选择。</div>
    </PanelCard>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import AlarmRecordPanel from "@/components/AlarmRecordPanel.vue";
import CommandLogPanel from "@/components/CommandLogPanel.vue";
import PanelCard from "@/components/PanelCard.vue";
import StatCard from "@/components/StatCard.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import TrendLineChart from "@/components/TrendLineChart.vue";
import { deleteDevice, getDeviceDetail, sendDeviceCommand, updateDevice, updateDeviceThreshold } from "@/services/deviceService";
import { getSensorList } from "@/services/sensorService";
import { can } from "@/services/permissions";
import type { CommandLog, DeviceDetail, SensorSummary, ThresholdConfig } from "@/types/models";

const route = useRoute();
const router = useRouter();
const device = ref<DeviceDetail | null>(null);
const actionMessage = ref("可查看真实后端阈值和控制状态");
const sensorControlSaving = ref(false);
const deletingDevice = ref(false);
const bindingSaving = ref(false);
const loadingSensors = ref(false);
const bindingInteracting = ref(false);
const availableSensors = ref<SensorSummary[]>([]);
const bindingSensorId = ref<number | undefined>(undefined);
let refreshTimer: number | undefined;
let commandRefreshTimer: number | undefined;

const threshold = reactive<ThresholdConfig>({
  deviceId: "",
  lowThreshold: 0,
  highThreshold: 0,
  enabled: false,
});

const canOperateDevices = computed(() => can("operateDevices"));
const sensorControlEnabled = computed(() => device.value?.sensorControlEnabled ?? true);
const sensorControlButtonText = computed(() =>
  sensorControlEnabled.value ? "暂停传感器控制" : "启用传感器控制",
);
const sensorControlStatusText = computed(() =>
  sensorControlEnabled.value ? "已启用" : "已暂停",
);
const sensorControlHint = computed(() =>
  sensorControlEnabled.value
    ? "当前允许传感器数据影响路灯状态"
    : "当前仅保留上报、心跳和在线状态，不再影响路灯状态",
);
const selectableSensors = computed(() =>
  availableSensors.value.filter(
    (sensor) =>
      sensor.boundDeviceId === device.value?.id ||
      (sensor.boundDeviceId == null && sensor.status === "online"),
  ),
);

// ---- 坐标编辑状态 ----
const coordEditing = ref(false);
const coordSaving = ref(false);
const coordEditError = ref<string | null>(null);
const editLatitude = ref(0);
const editLongitude = ref(0);
const editLocation = ref("");

function startCoordEdit() {
  if (!device.value) return;
  editLatitude.value = device.value.latitude ?? 0;
  editLongitude.value = device.value.longitude ?? 0;
  editLocation.value = device.value.location ?? "";
  coordEditing.value = true;
  coordEditError.value = null;
}

function cancelCoordEdit() {
  coordEditing.value = false;
  coordEditError.value = null;
}

async function saveCoordEdit() {
  if (!device.value) return;
  coordSaving.value = true;
  coordEditError.value = null;
  try {
    await updateDevice(device.value.id, {
      latitude: editLatitude.value || undefined,
      longitude: editLongitude.value || undefined,
      location: editLocation.value || undefined,
    });
    coordEditing.value = false;
    await loadDetail();
  } catch (e) {
    coordEditError.value = e instanceof Error ? e.message : "保存失败";
  } finally {
    coordSaving.value = false;
  }
}

async function loadSelectableSensors() {
  if (!device.value) return;
  loadingSensors.value = true;
  const previousSelection = bindingSensorId.value;
  try {
    availableSensors.value = await getSensorList();
    if (device.value.sensorId != null) {
      bindingSensorId.value = device.value.sensorId;
      return;
    }

    if (
      previousSelection != null &&
      availableSensors.value.some(
        (sensor) =>
          sensor.id === previousSelection &&
          (sensor.boundDeviceId === device.value?.id || (sensor.boundDeviceId == null && sensor.status === "online")),
      )
    ) {
      bindingSensorId.value = previousSelection;
      return;
    }

    bindingSensorId.value = undefined;
  } catch (error) {
    actionMessage.value = error instanceof Error ? error.message : "可选传感器加载失败";
  } finally {
    loadingSensors.value = false;
  }
}

// ---- Mini map ----
const AMAP_KEY = import.meta.env.VITE_AMAP_KEY || "";
const miniMapContainer = ref<HTMLDivElement | null>(null);
let miniMap: AMapMap | null = null;
let miniMarker: AMapMarker | null = null;

const hasCoords = computed(() => {
  const d = device.value;
  return d && d.latitude != null && d.longitude != null;
});

async function loadAmap(): Promise<void> {
  if (window.AMap) return;
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_KEY}`;
    script.async = true;
    script.onload = () => {
      window.AMap.plugin(["AMap.MoveAnimation"], () => resolve());
    };
    script.onerror = () => reject(new Error("高德地图 API 加载失败"));
    document.head.appendChild(script);
  });
}

async function initMiniMap(): Promise<void> {
  if (!miniMapContainer.value || !hasCoords.value) return;
  try {
    await loadAmap();
  } catch {
    return;
  }
  const d = device.value!;
  miniMap = new window.AMap.Map(miniMapContainer.value, {
    zoom: 16,
    center: [d.longitude!, d.latitude!],
    mapStyle: "amap://styles/light",
    resizeEnable: true,
    zoomEnable: false,
    dragEnable: false,
  });
  miniMarker = new window.AMap.Marker({
    position: [d.longitude!, d.latitude!],
  });
  miniMarker.setMap(miniMap);
}

function destroyMiniMap(): void {
  if (miniMarker) {
    miniMarker.setMap(null);
    miniMarker = null;
  }
  if (miniMap) {
    miniMap.destroy();
    miniMap = null;
  }
}

const overviewStats = computed(() => {
  if (!device.value) return [];
  return [
    {
      label: "当前光照",
      value: `${device.value.currentLightIntensity}`,
      helper: "单位 lx",
    },
    {
      label: "在线状态",
      value: device.value.status === "online" ? "在线" : "离线",
      helper: "基于最近心跳判断",
    },
    {
      label: "自动控制",
      value: threshold.enabled ? "开启" : "关闭",
      helper: "当前阈值策略状态",
    },
    {
      label: "告警数量",
      value: String(device.value.alarms.length),
      helper: "设备关联异常记录",
    },
  ];
});

const recentHistory = computed(() => device.value?.history.slice().reverse().slice(0, 5) ?? []);
const lastCommand = computed<CommandLog | null>(() => device.value?.commandLogs[0] ?? null);

const lastCommandLabel = computed(() => {
  if (!lastCommand.value) return "暂无控制记录";
  return `${lastCommand.value.command} / ${lastCommand.value.result}`;
});

const trendLabel = computed(() => {
  const history = device.value?.history ?? [];
  if (history.length < 2) return "数据不足";
  const latest = history[history.length - 1].lightIntensity;
  const previous = history[history.length - 2].lightIntensity;
  if (latest > previous) return `较上一周期上升 ${latest - previous} lx`;
  if (latest < previous) return `较上一周期下降 ${previous - latest} lx`;
  return "与上一周期持平";
});

const thresholdSuggestion = computed(() => {
  if (!device.value) return "等待设备数据";
  if (!threshold.enabled) return "建议先启用自动控制后再观察效果";
  if (device.value.currentLightIntensity < threshold.lowThreshold) return "当前偏暗，建议保持开灯";
  if (device.value.currentLightIntensity > threshold.highThreshold) return "当前偏亮，可考虑关灯";
  return "当前处于阈值区间内，保持现状即可";
});

const maintenanceSuggestion = computed(() => {
  if (!device.value) return "等待设备数据";
  if (device.value.status === "offline") return "设备离线，优先检查供电、网络和 MQTT 心跳。";
  if (device.value.alarms.length > 0) return "存在历史告警，建议结合日志核查控制链路。";
  return "设备运行平稳，可继续观察趋势数据。";
});

const integrationSuggestion = computed(() => {
  if (!device.value) return "等待设备数据";
  if (!device.value.commandLogs.length) return "联调时优先确认控制日志回写。";
  if (device.value.commandLogs.some((log) => log.result === "pending")) {
    return "存在 pending 指令，建议补充执行结果轮询。";
  }
  return "可继续联调设备详情聚合接口与告警接口。";
});

async function loadDetail() {
  const currentId = Number(route.params.id);
  device.value = await getDeviceDetail(currentId);
  if (device.value) {
    Object.assign(threshold, device.value.threshold);
    await loadSelectableSensors();
  } else {
    availableSensors.value = [];
    bindingSensorId.value = undefined;
  }
  // 延迟等 DOM 渲染后再初始化 mini map
  await nextTick();
  destroyMiniMap();
  if (hasCoords.value) {
    await initMiniMap();
  }
}

async function saveThreshold() {
  if (!device.value || !canOperateDevices.value) return;
  const saved = await updateDeviceThreshold(device.value.id, { ...threshold });
  Object.assign(threshold, saved);
  actionMessage.value = "阈值已保存到真实后端";
}

async function toggleSensorControl() {
  if (!device.value || !canOperateDevices.value || sensorControlSaving.value) return;

  const nextEnabled = !sensorControlEnabled.value;
  sensorControlSaving.value = true;
  try {
    await updateDevice(device.value.id, {
      sensor_control_enabled: nextEnabled,
    });
    actionMessage.value = nextEnabled
      ? "已启用传感器控制，路灯会重新受模拟器数据影响"
      : "已暂停传感器控制，后续上报不会再改写路灯状态";
    await loadDetail();
  } catch (error) {
    actionMessage.value = error instanceof Error ? error.message : "传感器控制切换失败";
  } finally {
    sensorControlSaving.value = false;
  }
}

async function handleBindSensor() {
  if (!device.value || !canOperateDevices.value || bindingSaving.value || bindingSensorId.value == null) return;
  bindingSaving.value = true;
  try {
    await updateDevice(device.value.id, { sensor_id: bindingSensorId.value });
    actionMessage.value = "传感器绑定已更新";
    bindingInteracting.value = false;
    await loadDetail();
  } catch (error) {
    actionMessage.value = error instanceof Error ? error.message : "更新传感器绑定失败";
  } finally {
    bindingSaving.value = false;
  }
}

async function handleUnbindSensor() {
  if (!device.value || !canOperateDevices.value || bindingSaving.value || device.value.sensorId == null) return;
  bindingSaving.value = true;
  try {
    await updateDevice(device.value.id, { sensor_id: null });
    actionMessage.value = "传感器已解绑";
    bindingInteracting.value = false;
    await loadDetail();
  } catch (error) {
    actionMessage.value = error instanceof Error ? error.message : "解绑传感器失败";
  } finally {
    bindingSaving.value = false;
  }
}

async function handleCommand(command: "TURN_ON" | "TURN_OFF") {
  if (!device.value || !canOperateDevices.value) return;
  const log = await sendDeviceCommand(device.value.id, command);
  actionMessage.value = `已发送 ${log.command} 指令，结果：${log.result}`;
  await loadDetail();
  if (commandRefreshTimer !== undefined) {
    window.clearTimeout(commandRefreshTimer);
  }
  commandRefreshTimer = window.setTimeout(() => {
    void loadDetail();
  }, 1200);
}

async function handleDeleteDevice() {
  const deviceId = device.value?.id ?? Number(route.params.id);
  if (!canOperateDevices.value || deletingDevice.value || !Number.isFinite(deviceId)) return;
  const deviceLabel = device.value?.deviceCode ?? `ID ${deviceId}`;
  if (!window.confirm(`确认删除路灯 ${deviceLabel} 吗？此操作不可恢复。`)) {
    return;
  }

  deletingDevice.value = true;
  try {
    await deleteDevice(deviceId);
    await router.push("/devices");
  } catch (error) {
    actionMessage.value = error instanceof Error ? error.message : "删除路灯失败";
  } finally {
    deletingDevice.value = false;
  }
}

async function goBackToList() {
  await router.push("/devices");
}

onMounted(() => {
  void loadDetail();
  refreshTimer = window.setInterval(() => {
    if (bindingInteracting.value || bindingSaving.value || loadingSensors.value) {
      return;
    }
    void loadDetail();
  }, 3000);
});

onBeforeUnmount(() => {
  if (refreshTimer !== undefined) {
    window.clearInterval(refreshTimer);
  }
  if (commandRefreshTimer !== undefined) {
    window.clearTimeout(commandRefreshTimer);
  }
  destroyMiniMap();
});

watch(() => route.params.id, loadDetail);
</script>

<style scoped>
/* ---- Mini map ---- */
.detail-mini-map-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.detail-mini-map {
  width: 100%;
  height: 200px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border-color, #e2e8f0);
}

.detail-coords-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-secondary, #64748b);
  font-family: "SF Mono", "Fira Code", monospace;
}

.coord-sep {
  color: var(--border-color, #e2e8f0);
}

.placeholder-box {
  text-align: center;
  padding: 2rem 1rem;
  color: var(--text-secondary, #64748b);
  font-size: 0.9rem;
}

.placeholder-box small {
  display: inline-block;
  margin-top: 0.35rem;
  opacity: 0.7;
}

.binding-manager {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.binding-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}

/* ---- 坐标编辑 ---- */
.coord-card-body {
  position: relative;
}

.coord-card-actions {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 1;
}

.coord-edit-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.coord-edit-form label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: var(--text-secondary, #64748b);
}

.danger-button {
  border: 1px solid rgba(239, 68, 68, 0.35);
  background: rgba(127, 29, 29, 0.18);
  color: #fecaca;
}

.danger-button:hover:not(:disabled) {
  background: rgba(127, 29, 29, 0.28);
}

.danger-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.coord-edit-form .button-row {
  margin-top: 0.25rem;
}
</style>
