<template>
  <view class="alarms-page">
    <!-- Filters -->
    <view class="filter-section">
      <scroll-view class="filter-row" scroll-x>
        <view
          v-for="f in handledFilters"
          :key="f.value"
          class="filter-chip"
          :class="{ active: activeHandled === f.value }"
          @tap="activeHandled = f.value"
        >
          <text>{{ f.label }}</text>
        </view>
      </scroll-view>
      <scroll-view class="filter-row" scroll-x>
        <view
          v-for="f in levelFilters"
          :key="f.value"
          class="filter-chip"
          :class="{ active: activeLevel === f.value }"
          @tap="activeLevel = f.value"
        >
          <text>{{ f.label }}</text>
        </view>
      </scroll-view>
    </view>

    <!-- Summary -->
    <view class="stats-row">
      <view class="stat-item">
        <text class="stat-num">{{ alarms.length }}</text>
        <text class="stat-lbl">总告警</text>
      </view>
      <view class="stat-item">
        <text class="stat-num warn">{{ unhandledCount }}</text>
        <text class="stat-lbl">未处理</text>
      </view>
      <view class="stat-item">
        <text class="stat-num critical">{{ criticalCount }}</text>
        <text class="stat-lbl">严重</text>
      </view>
      <view class="stat-item">
        <text class="stat-num success">{{ handledCount }}</text>
        <text class="stat-lbl">已处理</text>
      </view>
    </view>

    <!-- Alarm list -->
    <LoadingSpinner v-if="loading" text="加载告警..." />
    <scroll-view
      v-else
      class="alarm-scroll"
      scroll-y
      refresher-enabled
      :refresher-triggered="refreshing"
      @refresherrefresh="onRefresh"
      @refresherrestore="refreshing = false"
    >
      <AlarmItem
        v-for="alarm in filteredAlarms"
        :key="alarm.id"
        :alarm="alarm"
        :show-handle="canHandle"
        @handle="onHandleAlarm"
      />
      <EmptyState v-if="filteredAlarms.length === 0" message="没有匹配的告警" icon="🔔" />
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { onShow } from "@dcloudio/uni-app";
import type { AlarmRecord } from "@/types/models";
import { getAlarmList, handleAlarm } from "@/services/api/alarmService";
import { can } from "@/services/permissions";
import AlarmItem from "@/components/AlarmItem.vue";
import LoadingSpinner from "@/components/LoadingSpinner.vue";
import EmptyState from "@/components/EmptyState.vue";

const loading = ref(true);
const refreshing = ref(false);
const alarms = ref<AlarmRecord[]>([]);
const activeHandled = ref("all");
const activeLevel = ref("all");
const canHandle = can("handleAlarms");

const handledFilters = [
  { label: "全部", value: "all" },
  { label: "未处理", value: "unhandled" },
  { label: "已处理", value: "handled" },
];

const levelFilters = [
  { label: "全部级别", value: "all" },
  { label: "INFO", value: "INFO" },
  { label: "WARN", value: "WARN" },
  { label: "CRITICAL", value: "CRITICAL" },
];

const unhandledCount = computed(() => alarms.value.filter((a) => !a.handled).length);
const handledCount = computed(() => alarms.value.filter((a) => a.handled).length);
const criticalCount = computed(() => alarms.value.filter((a) => a.alarmLevel === "CRITICAL").length);

const filteredAlarms = computed(() => {
  let list = alarms.value;

  if (activeHandled.value === "handled") list = list.filter((a) => a.handled);
  else if (activeHandled.value === "unhandled") list = list.filter((a) => !a.handled);

  if (activeLevel.value !== "all") {
    list = list.filter((a) => a.alarmLevel === activeLevel.value);
  }

  return list;
});

async function loadData() {
  try {
    alarms.value = await getAlarmList();
  } catch (err) {
    console.error("加载告警失败", err);
  } finally {
    loading.value = false;
  }
}

async function onHandleAlarm(alarm: AlarmRecord) {
  try {
    await handleAlarm(alarm.id);
    uni.showToast({ title: "告警已确认", icon: "success" });
    loadData();
  } catch (err) {
    uni.showToast({ title: "操作失败", icon: "error" });
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
});
</script>

<style scoped>
.alarms-page {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.filter-section {
  margin-bottom: 12px;
}

.filter-row {
  display: flex;
  white-space: nowrap;
  margin-bottom: 8px;
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

.stats-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 8px;
  margin-bottom: 16px;
}

.stat-item {
  background: rgba(10, 26, 45, 0.6);
  border: 1px solid rgba(56, 213, 255, 0.1);
  border-radius: 10px;
  padding: 10px 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-num {
  font-size: 22px;
  font-weight: 700;
  color: #38d5ff;
}

.stat-num.warn {
  color: #ffc107;
}

.stat-num.critical {
  color: #ff5252;
}

.stat-num.success {
  color: #00c853;
}

.stat-lbl {
  font-size: 11px;
  color: #6a8299;
}

.alarm-scroll {
  flex: 1;
  overflow-y: auto;
}
</style>
