<template>
  <div class="page-stack">
    <SectionCard title="筛选设备" subtitle="支持名称、编号与状态筛选">
      <div class="filter-stack">
        <input v-model.trim="keyword" type="text" placeholder="搜索设备编号 / 名称 / 位置" />
        <div class="chip-row">
          <button
            v-for="item in filterOptions"
            :key="item.value"
            class="chip-button"
            :class="{ 'chip-button-active': statusFilter === item.value }"
            type="button"
            @click="statusFilter = item.value"
          >
            {{ item.label }}
          </button>
        </div>
      </div>
    </SectionCard>

    <div v-if="loading" class="mobile-skeleton-grid">
      <div v-for="item in 4" :key="item" class="mobile-skeleton-card"></div>
    </div>

    <SectionCard v-else title="设备卡片" :subtitle="`共 ${filteredDevices.length} 台设备`">
      <div v-if="loadError" class="placeholder-text">{{ loadError }}</div>
      <div v-else class="page-stack">
        <DeviceListItem
          v-for="device in filteredDevices"
          :key="device.id"
          :device="device"
          :can-operate="canOperateDevices"
          @view="goDetail(device.id)"
          @toggle="toggleDevice(device)"
        />
        <p v-if="!filteredDevices.length" class="placeholder-text">没有匹配的设备。</p>
      </div>
    </SectionCard>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import DeviceListItem from "@/components/DeviceListItem.vue";
import SectionCard from "@/components/SectionCard.vue";
import { getDeviceList, sendDeviceCommand } from "@/services/api/deviceService";
import { can } from "@/services/permissions";
import type { Device } from "@/types/models";

const router = useRouter();
const devices = ref<Device[]>([]);
const keyword = ref("");
const statusFilter = ref<"all" | "online" | "offline">("all");
const loading = ref(true);
const loadError = ref("");
const canOperateDevices = can("operateDevices");

const filterOptions = [
  { label: "全部", value: "all" as const },
  { label: "在线", value: "online" as const },
  { label: "离线", value: "offline" as const },
];

const filteredDevices = computed(() => {
  const normalized = keyword.value.trim().toLowerCase();
  return devices.value.filter((device) => {
    const keywordMatched =
      !normalized ||
      [device.deviceCode, device.deviceName, device.location].join(" ").toLowerCase().includes(normalized);
    const statusMatched = statusFilter.value === "all" || device.status === statusFilter.value;
    return keywordMatched && statusMatched;
  });
});

function getErrorMessage(error: unknown) {
  if (!(error instanceof Error)) {
    return "操作失败，请稍后重试。";
  }
  try {
    const parsed = JSON.parse(error.message) as { detail?: string };
    return parsed.detail || error.message;
  } catch {
    return error.message;
  }
}

async function loadDevices() {
  loading.value = true;
  loadError.value = "";
  try {
    devices.value = await getDeviceList();
  } catch (error) {
    loadError.value = `设备数据加载失败：${getErrorMessage(error)}`;
  } finally {
    loading.value = false;
  }
}

async function toggleDevice(device: Device) {
  try {
    await sendDeviceCommand(device.id, device.lampStatus === "ON" ? "TURN_OFF" : "TURN_ON");
    await loadDevices();
  } catch (error) {
    loadError.value = `控制失败：${getErrorMessage(error)}`;
  }
}

function goDetail(id: number) {
  router.push(`/devices/${id}`);
}

onMounted(loadDevices);
</script>
