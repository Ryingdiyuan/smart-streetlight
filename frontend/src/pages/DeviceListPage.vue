<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Devices</p>
        <h3>设备列表</h3>
      </div>
      <p class="section-note">已接入真实设备列表接口，支持按关键词与状态筛选。</p>
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

      <div v-if="loading" class="placeholder-box">正在加载真实设备数据...</div>
      <div v-else-if="loadError" class="placeholder-box">{{ loadError }}</div>
      <div v-else class="table-wrapper">
        <table>
          <thead>
            <tr>
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
              <td colspan="7" class="table-empty">没有匹配的设备</td>
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
import { getDeviceList } from "@/services/deviceService";
import type { DashboardStat, Device } from "@/types/models";

const devices = ref<Device[]>([]);
const keyword = ref("");
const statusFilter = ref<"all" | "online" | "offline">("all");
const loading = ref(true);
const loadError = ref("");
let refreshTimer: number | undefined;

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

async function loadDevices() {
  loading.value = true;
  loadError.value = "";

  try {
    devices.value = await getDeviceList();
  } catch (error) {
    devices.value = [];
    loadError.value =
      error instanceof Error ? `设备列表加载失败：${error.message}` : "设备列表加载失败";
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  await loadDevices();
  refreshTimer = window.setInterval(() => {
    void loadDevices();
  }, 3000);
});

onBeforeUnmount(() => {
  if (refreshTimer !== undefined) {
    window.clearInterval(refreshTimer);
  }
});
</script>
