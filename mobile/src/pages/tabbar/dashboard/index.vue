<template>
  <view class="dashboard-page">
    <LoadingSpinner v-if="loading" text="加载中..." />
    <template v-else>
      <!-- Stat cards -->
      <view class="stats-grid">
        <StatCard
          label="设备总数"
          :value="totalDevices"
          helper="全部设备"
        />
        <StatCard
          label="在线设备"
          :value="onlineDevices"
          :helper="`离线 ${offlineDevices}`"
          value-color="#00c853"
        />
        <StatCard
          label="未处理告警"
          :value="unhandledAlarmCount"
          :helper="`告警共 ${alarmTotal}`"
          value-color="#ff5252"
        />
        <StatCard
          label="灯亮数量"
          :value="lampOnCount"
          :helper="`灯灭 ${lampOffCount}`"
          value-color="#ffc107"
        />
      </view>

      <!-- Device status summary -->
      <view class="section">
        <text class="section-title">设备状态快照</text>
        <view v-if="devices.length" class="device-mini-list">
          <view
            v-for="device in devices"
            :key="device.id"
            class="device-mini-row"
          >
            <view class="mini-left">
              <text class="mini-name">{{ device.deviceName }}</text>
              <text class="mini-code">{{ device.deviceCode }}</text>
            </view>
            <view class="mini-right">
              <StatusBadge
                :type="device.status === 'online' ? 'online' : 'offline'"
              >
                {{ device.status === "online" ? "在线" : "离线" }}
              </StatusBadge>
              <StatusBadge
                :type="device.lampStatus === 'ON' ? 'on' : 'off'"
              >
                {{ device.lampStatus === "ON" ? "灯亮" : "灯灭" }}
              </StatusBadge>
            </view>
          </view>
        </view>
        <EmptyState v-else message="暂无设备数据" />
      </view>

      <!-- Recent alarms -->
      <view class="section">
        <text class="section-title">最近告警</text>
        <AlarmItem
          v-for="alarm in latestAlarms"
          :key="alarm.id"
          :alarm="alarm"
          :show-handle="false"
        />
        <EmptyState
          v-if="!latestAlarms.length"
          message="暂无告警"
        />
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { onShow, onHide } from "@dcloudio/uni-app";
import type { Device, AlarmRecord } from "@/types/models";
import { getDeviceList } from "@/services/api/deviceService";
import { getAlarmList } from "@/services/api/alarmService";
import StatCard from "@/components/StatCard.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import AlarmItem from "@/components/AlarmItem.vue";
import LoadingSpinner from "@/components/LoadingSpinner.vue";
import EmptyState from "@/components/EmptyState.vue";

const loading = ref(true);
const devices = ref<Device[]>([]);
const alarms = ref<AlarmRecord[]>([]);
let refreshTimer: ReturnType<typeof setInterval> | null = null;

const totalDevices = computed(() => String(devices.value.length));
const onlineDevices = computed(() => String(devices.value.filter((d) => d.status === "online").length));
const offlineDevices = computed(() => devices.value.filter((d) => d.status === "offline").length);
const lampOnCount = computed(() => String(devices.value.filter((d) => d.lampStatus === "ON").length));
const lampOffCount = computed(() => devices.value.filter((d) => d.lampStatus === "OFF").length);
const alarmTotal = computed(() => alarms.value.length);
const unhandledAlarmCount = computed(() => String(alarms.value.filter((a) => !a.handled).length));
const latestAlarms = computed(() => alarms.value.slice(0, 5));

async function loadData() {
  try {
    const [deviceList, alarmList] = await Promise.all([
      getDeviceList(),
      getAlarmList(),
    ]);
    devices.value = deviceList;
    alarms.value = alarmList;
  } catch (err) {
    console.error("加载总览数据失败", err);
  } finally {
    loading.value = false;
  }
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
.dashboard-page {
  padding: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 20px;
}

.section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #e8edf3;
  margin-bottom: 12px;
  display: block;
  border-left: 3px solid #38d5ff;
  padding-left: 10px;
}

.device-mini-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.device-mini-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: rgba(10, 26, 45, 0.6);
  border-radius: 8px;
  margin-bottom: 4px;
}

.mini-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mini-name {
  font-size: 14px;
  color: #e8edf3;
  font-weight: 500;
}

.mini-code {
  font-size: 12px;
  color: #6a8299;
}

.mini-right {
  display: flex;
  gap: 6px;
}
</style>
