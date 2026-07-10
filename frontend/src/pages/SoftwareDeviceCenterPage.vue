<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Software Module</p>
        <h3>路灯管理中心</h3>
      </div>
      <p class="section-note">
        业务前端仅维护路灯档案。传感器需先在硬件模拟器注册，再在这里绑定到路灯后，系统才会接收该传感器数据。
      </p>
    </header>

    <div class="stats-grid">
      <StatCard v-for="item in summaryStats" :key="item.label" :stat="item" />
    </div>

    <div class="content-grid two-columns">
      <PanelCard title="新增路灯档案" subtitle="创建路灯并可直接绑定已注册传感器">
        <div class="form-grid">
          <label>
            <span>路灯编码</span>
            <input v-model="createForm.deviceCode" type="text" placeholder="例如 SL-010" />
          </label>
          <label>
            <span>路灯名称</span>
            <input v-model="createForm.deviceName" type="text" placeholder="例如 图书馆路灯" />
          </label>
          <label>
            <span>安装位置</span>
            <input v-model="createForm.location" type="text" placeholder="例如 图书馆门口" />
          </label>
          <label>
            <span>纬度</span>
            <input v-model.number="createForm.latitude" type="number" step="any" placeholder="例如 29.531000" />
          </label>
          <label>
            <span>经度</span>
            <input v-model.number="createForm.longitude" type="number" step="any" placeholder="例如 106.528000" />
          </label>
          <label>
            <span>绑定传感器</span>
            <select v-model="createForm.sensorId">
              <option :value="undefined">暂不绑定</option>
              <option v-for="sensor in availableSensors" :key="sensor.id" :value="sensor.id">
                {{ sensor.sensorCode }} - {{ sensor.sensorName }}
              </option>
            </select>
          </label>
          <label>
            <span>控制模式</span>
            <select v-model="createForm.controlMode">
              <option value="manual">手动控制</option>
              <option value="auto">自动控制</option>
            </select>
          </label>
        </div>

        <div class="button-row software-device-actions">
          <button class="primary-button" type="button" :disabled="saving" @click="handleCreateDevice">
            {{ saving ? "创建中..." : "创建路灯档案" }}
          </button>
          <button class="ghost-button" type="button" :disabled="loadingSensors" @click="loadSensors">
            {{ loadingSensors ? "刷新中..." : "刷新传感器" }}
          </button>
          <RouterLink class="ghost-button" to="/map">去地图选点</RouterLink>
        </div>

        <p class="inline-note">
          说明：未绑定传感器的路灯不会接收硬件数据；自动模式会根据阈值自动下发开关灯命令。
        </p>
        <p v-if="message" class="software-device-message">{{ message }}</p>
      </PanelCard>

      <PanelCard title="业务入口" subtitle="保留路灯业务管理，不承担硬件模拟职责">
        <div class="software-entry-list">
          <RouterLink class="software-entry-card" to="/devices">
            <strong>路灯列表</strong>
            <span>查看路灯状态、绑定关系、批量控制与详情。</span>
          </RouterLink>
          <RouterLink class="software-entry-card" to="/map">
            <strong>路灯地图</strong>
            <span>查看 GIS 分布与维护坐标信息。</span>
          </RouterLink>
          <RouterLink class="software-entry-card" to="/realtime-light">
            <strong>实时光照监测</strong>
            <span>查看绑定传感器生效后的实时上报数据。</span>
          </RouterLink>
        </div>
      </PanelCard>
    </div>

    <PanelCard title="最近路灯档案" subtitle="优先显示最近创建的路灯与当前绑定状态">
      <div v-if="loading" class="placeholder-box">正在加载路灯档案...</div>
      <div v-else-if="loadError" class="placeholder-box">{{ loadError }}</div>
      <div v-else class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>路灯编码</th>
              <th>路灯名称</th>
              <th>安装位置</th>
              <th>绑定传感器</th>
              <th>控制模式</th>
              <th>在线状态</th>
              <th>灯状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="device in recentDevices" :key="device.id">
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
              <td>
                <div class="button-row software-table-actions">
                  <RouterLink class="text-link" :to="`/devices/${device.id}`">查看详情</RouterLink>
                  <RouterLink class="text-link" to="/map">地图维护</RouterLink>
                </div>
              </td>
            </tr>
            <tr v-if="!recentDevices.length">
              <td colspan="8" class="table-empty">暂无路灯档案</td>
            </tr>
          </tbody>
        </table>
      </div>
    </PanelCard>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";

import PanelCard from "@/components/PanelCard.vue";
import StatCard from "@/components/StatCard.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import { createDevice, getDeviceList } from "@/services/deviceService";
import { getSensorList } from "@/services/sensorService";
import type { DashboardStat, Device, SensorSummary } from "@/types/models";

const router = useRouter();
const devices = ref<Device[]>([]);
const availableSensors = ref<SensorSummary[]>([]);
const loading = ref(true);
const loadingSensors = ref(false);
const saving = ref(false);
const loadError = ref("");
const message = ref("");

const createForm = reactive({
  deviceCode: "",
  deviceName: "",
  location: "",
  latitude: undefined as number | undefined,
  longitude: undefined as number | undefined,
  sensorId: undefined as number | undefined,
  controlMode: "manual" as "manual" | "auto",
});

const summaryStats = computed<DashboardStat[]>(() => [
  { label: "路灯总数", value: String(devices.value.length), helper: "当前数据库中的路灯档案" },
  {
    label: "已绑定传感器",
    value: String(devices.value.filter((device) => device.sensorId != null).length),
    helper: "绑定后才会接收硬件数据",
  },
  {
    label: "自动模式",
    value: String(devices.value.filter((device) => device.controlMode === "auto").length),
    helper: "达到阈值会自动控制开关灯",
  },
  {
    label: "在线路灯",
    value: String(devices.value.filter((device) => device.status === "online").length),
    helper: "来自已绑定传感器的实时状态",
  },
]);

const recentDevices = computed(() => devices.value.slice().sort((a, b) => b.id - a.id).slice(0, 8));

function getErrorMessage(error: unknown) {
  if (!(error instanceof Error)) {
    return "操作失败，请稍后重试";
  }

  try {
    const parsed = JSON.parse(error.message) as { detail?: string };
    return parsed.detail || error.message;
  } catch {
    return error.message || "操作失败，请稍后重试";
  }
}

function resetCreateForm() {
  createForm.deviceCode = "";
  createForm.deviceName = "";
  createForm.location = "";
  createForm.latitude = undefined;
  createForm.longitude = undefined;
  createForm.sensorId = undefined;
  createForm.controlMode = "manual";
}

async function loadDevices() {
  loading.value = true;
  loadError.value = "";
  try {
    devices.value = await getDeviceList();
  } catch (error) {
    devices.value = [];
    loadError.value = `路灯档案加载失败：${getErrorMessage(error)}`;
  } finally {
    loading.value = false;
  }
}

async function loadSensors() {
  loadingSensors.value = true;
  try {
    availableSensors.value = await getSensorList({ onlyUnbound: true, onlyOnline: true });
  } catch (error) {
    message.value = `传感器列表加载失败：${getErrorMessage(error)}`;
  } finally {
    loadingSensors.value = false;
  }
}

async function handleCreateDevice() {
  if (!createForm.deviceCode.trim() || !createForm.deviceName.trim()) {
    message.value = "路灯编码和路灯名称不能为空";
    return;
  }

  saving.value = true;
  message.value = "";
  try {
    const createdDevice = await createDevice({
      device_code: createForm.deviceCode.trim(),
      device_name: createForm.deviceName.trim(),
      location: createForm.location.trim() || undefined,
      latitude: createForm.latitude,
      longitude: createForm.longitude,
      sensor_id: createForm.sensorId,
      control_mode: createForm.controlMode,
    });
    resetCreateForm();
    message.value = "路灯档案已创建。若已绑定传感器，后续该传感器上报会立即生效。";
    await Promise.all([loadDevices(), loadSensors()]);
    await router.push(`/devices/${createdDevice.id}`);
  } catch (error) {
    message.value = getErrorMessage(error);
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  void Promise.all([loadDevices(), loadSensors()]);
});
</script>

<style scoped>
.software-device-actions,
.software-table-actions {
  flex-wrap: wrap;
}

.software-device-message {
  margin-top: 14px;
  margin-bottom: 0;
  color: #2563eb;
  line-height: 1.6;
}

.software-entry-list {
  display: grid;
  gap: 12px;
}

.software-entry-card {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid rgba(127, 203, 255, 0.12);
  background: rgba(5, 18, 32, 0.42);
  color: inherit;
  text-decoration: none;
  transition: 0.18s ease;
}

.software-entry-card strong {
  color: #e2e8f0;
}

.software-entry-card span {
  color: #94a3b8;
  line-height: 1.6;
}

.software-entry-card:hover {
  transform: translateY(-1px);
  border-color: rgba(56, 213, 255, 0.32);
  background: rgba(10, 34, 56, 0.7);
}
</style>
