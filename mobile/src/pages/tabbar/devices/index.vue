<template>
  <view class="devices-page">
    <!-- Search bar -->
    <view class="search-bar">
      <input
        class="search-input"
        v-model="searchQuery"
        placeholder="搜索设备编号/名称/位置"
        placeholder-class="placeholder"
        @input="onSearch"
      />
    </view>

    <!-- Status filter -->
    <scroll-view class="filter-row" scroll-x>
      <view
        v-for="filter in statusFilters"
        :key="filter.value"
        class="filter-chip"
        :class="{ active: activeFilter === filter.value }"
        @tap="activeFilter = filter.value"
      >
        <text>{{ filter.label }}</text>
      </view>
    </scroll-view>

    <!-- Batch actions -->
    <view v-if="canOperate && selectedIds.length > 0" class="batch-bar">
      <text class="batch-info">已选 {{ selectedIds.length }} 台</text>
      <view class="batch-actions">
        <view class="batch-btn on" @tap="batchCommand('TURN_ON')">批量开灯</view>
        <view class="batch-btn off" @tap="batchCommand('TURN_OFF')">批量关灯</view>
      </view>
    </view>

    <!-- Device list -->
    <LoadingSpinner v-if="loading" text="加载设备..." />
    <scroll-view
      v-else
      class="device-scroll"
      scroll-y
      refresher-enabled
      :refresher-triggered="refreshing"
      @refresherrefresh="onRefresh"
      @refresherrestore="refreshing = false"
    >
      <DeviceCard
        v-for="device in filteredDevices"
        :key="device.id"
        :device="device"
        :selected="canOperate ? selectedIds.includes(device.id) : undefined"
        @tap="canOperate ? toggleSelect(device.id) : goToDetail(device.id)"
      />
      <EmptyState v-if="filteredDevices.length === 0" message="没有匹配的设备" />
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { onShow, onHide } from "@dcloudio/uni-app";
import type { Device } from "@/types/models";
import { getDeviceList, sendBatchDeviceCommand } from "@/services/api/deviceService";
import { can } from "@/services/permissions";
import DeviceCard from "@/components/DeviceCard.vue";
import LoadingSpinner from "@/components/LoadingSpinner.vue";
import EmptyState from "@/components/EmptyState.vue";

const loading = ref(true);
const refreshing = ref(false);
const devices = ref<Device[]>([]);
const searchQuery = ref("");
const activeFilter = ref("all");
const selectedIds = ref<number[]>([]);
const canOperate = can("operateDevices");
let refreshTimer: ReturnType<typeof setInterval> | null = null;

const statusFilters = [
  { label: "全部", value: "all" },
  { label: "在线", value: "online" },
  { label: "离线", value: "offline" },
];

const filteredDevices = computed(() => {
  let list = devices.value;

  if (activeFilter.value !== "all") {
    list = list.filter((d) => d.status === activeFilter.value);
  }

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    list = list.filter(
      (d) =>
        d.deviceCode.toLowerCase().includes(q) ||
        d.deviceName.toLowerCase().includes(q) ||
        d.location.toLowerCase().includes(q),
    );
  }

  return list;
});

async function loadData() {
  try {
    devices.value = await getDeviceList();
  } catch (err) {
    console.error("加载设备列表失败", err);
  } finally {
    loading.value = false;
  }
}

function onSearch() {
  // reactive search
}

function toggleSelect(id: number) {
  const idx = selectedIds.value.indexOf(id);
  if (idx >= 0) {
    selectedIds.value.splice(idx, 1);
  } else {
    selectedIds.value.push(id);
  }
}

function goToDetail(id: number) {
  uni.navigateTo({ url: `/pages/subpages/device-detail/index?id=${id}` });
}

async function batchCommand(command: "TURN_ON" | "TURN_OFF") {
  try {
    const result = await sendBatchDeviceCommand(selectedIds.value, command);
    uni.showToast({
      title: `成功: ${result.successCount}, 失败: ${result.failedCount}`,
      icon: "none",
    });
    selectedIds.value = [];
    loadData();
  } catch (err) {
    uni.showToast({ title: "批量操作失败", icon: "error" });
  }
}

async function onRefresh() {
  refreshing.value = true;
  await loadData();
  refreshing.value = false;
}

onShow(() => {
  loading.value = true;
  loadData();
  refreshTimer = setInterval(loadData, 30000);
});

onHide(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
});
</script>

<style scoped>
.devices-page {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.search-bar {
  margin-bottom: 12px;
}

.search-input {
  width: 100%;
  height: 42px;
  background: rgba(10, 26, 45, 0.8);
  border: 1px solid rgba(56, 213, 255, 0.15);
  border-radius: 10px;
  padding: 0 14px;
  color: #e8edf3;
  font-size: 14px;
}

.filter-row {
  display: flex;
  white-space: nowrap;
  margin-bottom: 12px;
  padding-bottom: 4px;
}

.filter-chip {
  display: inline-flex;
  padding: 6px 16px;
  border-radius: 20px;
  background: rgba(10, 26, 45, 0.6);
  border: 1px solid rgba(56, 213, 255, 0.1);
  margin-right: 8px;
  font-size: 13px;
  color: #9fb4c8;
}

.filter-chip.active {
  background: rgba(56, 213, 255, 0.15);
  border-color: #38d5ff;
  color: #38d5ff;
}

.batch-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: rgba(56, 213, 255, 0.08);
  border: 1px solid rgba(56, 213, 255, 0.2);
  border-radius: 10px;
  margin-bottom: 12px;
}

.batch-info {
  font-size: 13px;
  color: #38d5ff;
}

.batch-actions {
  display: flex;
  gap: 8px;
}

.batch-btn {
  padding: 6px 16px;
  border-radius: 8px;
  font-size: 13px;
}

.batch-btn.on {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
  border: 1px solid rgba(255, 193, 7, 0.3);
}

.batch-btn.off {
  background: rgba(158, 180, 200, 0.2);
  color: #9fb4c8;
  border: 1px solid rgba(158, 180, 200, 0.3);
}

.device-scroll {
  flex: 1;
  overflow-y: auto;
}
</style>
