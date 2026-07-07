<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Software Module</p>
        <h3>软件设备中心</h3>
      </div>
      <p class="section-note">
        面向实际软件功能的设备建档入口。这里负责设备档案创建、坐标录入和业务页面跳转，不承担模拟器运行与 MQTT 联调职责。
      </p>
    </header>

    <div class="stats-grid">
      <StatCard v-for="item in summaryStats" :key="item.label" :stat="item" />
    </div>

    <div class="content-grid two-columns">
      <PanelCard title="新增设备档案" subtitle="创建后写入数据库，可在设备列表、地图和详情页使用">
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
            <span>纬度</span>
            <input v-model.number="createForm.latitude" type="number" step="any" placeholder="例如 29.531000" />
          </label>
          <label>
            <span>经度</span>
            <input v-model.number="createForm.longitude" type="number" step="any" placeholder="例如 106.528000" />
          </label>
        </div>

        <div class="button-row software-device-actions">
          <button class="primary-button" type="button" :disabled="saving" @click="handleCreateDevice">
            {{ saving ? "创建中..." : "创建设备档案" }}
          </button>
          <RouterLink class="ghost-button" to="/map">去地图选点</RouterLink>
          <span class="inline-note">硬件联调能力已拆分为独立前端项目，不再和软件业务前端混合展示。</span>
        </div>

        <p v-if="message" class="software-device-message">{{ message }}</p>
      </PanelCard>

      <PanelCard title="业务入口" subtitle="当前只保留软件业务功能入口">
        <div class="software-entry-list">
          <RouterLink class="software-entry-card" to="/devices">
            <strong>设备列表</strong>
            <span>查看设备档案、状态、批量控制与详情页。</span>
          </RouterLink>
          <RouterLink class="software-entry-card" to="/map">
            <strong>设备地图</strong>
            <span>查看 GIS 分布、录入或修正设备坐标。</span>
          </RouterLink>
          <RouterLink class="software-entry-card" to="/realtime-light">
            <strong>实时光照监测</strong>
            <span>查看传感器实时上报和当前灯状态。</span>
          </RouterLink>
        </div>
      </PanelCard>
    </div>

    <PanelCard title="最近设备档案" subtitle="优先展示最近创建或编号较新的设备">
      <div v-if="loading" class="placeholder-box">正在加载设备档案...</div>
      <div v-else-if="loadError" class="placeholder-box">{{ loadError }}</div>
      <div v-else class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>设备编码</th>
              <th>设备名称</th>
              <th>安装位置</th>
              <th>坐标状态</th>
              <th>在线状态</th>
              <th>路灯状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="device in recentDevices" :key="device.id">
              <td>{{ device.deviceCode }}</td>
              <td>{{ device.deviceName }}</td>
              <td>{{ device.location }}</td>
              <td>
                <StatusBadge
                  :status="device.latitude != null && device.longitude != null ? 'success' : 'warning'"
                  :text="device.latitude != null && device.longitude != null ? '已录坐标' : '待补坐标'"
                />
              </td>
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
              <td>
                <div class="button-row software-table-actions">
                  <RouterLink class="text-link" :to="`/devices/${device.id}`">查看详情</RouterLink>
                  <RouterLink class="text-link" to="/map">地图维护</RouterLink>
                </div>
              </td>
            </tr>
            <tr v-if="!recentDevices.length">
              <td colspan="7" class="table-empty">暂无设备档案</td>
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
import type { DashboardStat, Device } from "@/types/models";

const router = useRouter();
const devices = ref<Device[]>([]);
const loading = ref(true);
const saving = ref(false);
const loadError = ref("");
const message = ref("");

const createForm = reactive({
  deviceCode: "",
  deviceName: "",
  location: "",
  latitude: undefined as number | undefined,
  longitude: undefined as number | undefined,
});

const summaryStats = computed<DashboardStat[]>(() => [
  { label: "设备总数", value: String(devices.value.length), helper: "当前数据库中的设备档案" },
  {
    label: "已录坐标",
    value: String(devices.value.filter((device) => device.latitude != null && device.longitude != null).length),
    helper: "已可用于地图展示",
  },
  {
    label: "待补坐标",
    value: String(devices.value.filter((device) => device.latitude == null || device.longitude == null).length),
    helper: "建议在地图页继续完善位置",
  },
  {
    label: "在线设备",
    value: String(devices.value.filter((device) => device.status === "online").length),
    helper: "来自系统当前设备状态",
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
}

async function loadDevices() {
  loading.value = true;
  loadError.value = "";
  try {
    devices.value = await getDeviceList();
  } catch (error) {
    devices.value = [];
    loadError.value = `设备档案加载失败：${getErrorMessage(error)}`;
  } finally {
    loading.value = false;
  }
}

async function handleCreateDevice() {
  if (!createForm.deviceCode.trim() || !createForm.deviceName.trim()) {
    message.value = "设备编码和设备名称不能为空";
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
    });
    resetCreateForm();
    message.value = "设备档案已创建，可继续去地图或详情页完善信息";
    await loadDevices();
    await router.push(`/devices/${createdDevice.id}`);
  } catch (error) {
    message.value = getErrorMessage(error);
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  void loadDevices();
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
