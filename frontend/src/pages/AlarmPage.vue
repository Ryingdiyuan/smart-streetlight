<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Alarms</p>
        <h3>告警日志</h3>
      </div>
      <p class="section-note">将告警标记为“已处理”仅表示人工已知晓或已处置，不会直接改变设备在线状态；设备在线状态仍由心跳自动判断。</p>
    </header>

    <div class="stats-grid">
      <StatCard v-for="item in summaryStats" :key="item.label" :stat="item" />
    </div>

    <PanelCard title="告警筛选与列表" subtitle="支持按处理状态和级别查看">
      <div class="toolbar-row">
        <div class="toolbar-actions">
          <button
            v-for="option in handledOptions"
            :key="option.value"
            class="ghost-button"
            :class="{ 'ghost-button-active': handledFilter === option.value }"
            @click="handledFilter = option.value"
          >
            {{ option.label }}
          </button>
        </div>
        <div class="toolbar-actions">
          <button
            v-for="option in levelOptions"
            :key="option.value"
            class="ghost-button"
            :class="{ 'ghost-button-active': levelFilter === option.value }"
            @click="levelFilter = option.value"
          >
            {{ option.label }}
          </button>
        </div>
      </div>

      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>告警编号</th>
              <th>告警对象</th>
              <th>类型</th>
              <th>级别</th>
              <th>内容</th>
              <th>处理状态</th>
              <th>进度时间</th>
              <th v-if="canHandleAlarms">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="alarm in filteredAlarms" :key="alarm.id">
              <td>{{ alarm.id }}</td>
              <td>
                <div class="table-cell-stack">
                  <span>{{ alarm.sensorCode || alarm.deviceId }}</span>
                  <span v-if="alarm.sensorName" class="inline-note">{{ alarm.sensorName }}</span>
                </div>
              </td>
              <td>{{ alarmTypeText(alarm) }}</td>
              <td>
                <StatusBadge
                  :status="alarm.alarmLevel === 'INFO' ? 'info' : 'warning'"
                  :text="alarm.alarmLevel"
                />
              </td>
              <td>{{ alarm.alarmContent }}</td>
              <td>
                <StatusBadge
                  :status="alarm.handled ? 'info' : 'warning'"
                  :text="alarm.handled ? '已处理' : '待处理'"
                />
              </td>
              <td>
                <div class="table-cell-stack">
                  <span>告警：{{ alarm.createdAt }}</span>
                  <span v-if="alarm.handled && alarm.handledAt" class="inline-note">处理：{{ alarm.handledAt }}</span>
                  <span v-else class="inline-note">处理：待处理</span>
                </div>
              </td>
              <td v-if="canHandleAlarms">
                <button
                  class="ghost-button"
                  type="button"
                  :disabled="alarm.handled || handlingAlarmId === alarm.id"
                  @click="handleAlarmRecord(alarm.id)"
                >
                  {{ alarm.handled ? "已处理" : handlingAlarmId === alarm.id ? "处理中..." : "标记已处理" }}
                </button>
              </td>
            </tr>
            <tr v-if="!filteredAlarms.length">
              <td :colspan="canHandleAlarms ? 8 : 7" class="table-empty">当前没有告警记录</td>
            </tr>
          </tbody>
        </table>
      </div>
    </PanelCard>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import PanelCard from "@/components/PanelCard.vue";
import StatCard from "@/components/StatCard.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import { getAlarmList, handleAlarm } from "@/services/alarmService";
import { can } from "@/services/permissions";
import type { AlarmLevel, AlarmRecord, DashboardStat } from "@/types/models";

const alarms = ref<AlarmRecord[]>([]);
const handledFilter = ref<"all" | "handled" | "unhandled">("all");
const levelFilter = ref<"all" | AlarmLevel>("all");
const handlingAlarmId = ref<string | null>(null);
const canHandleAlarms = computed(() => can("handleAlarms"));

const handledOptions = [
  { label: "全部状态", value: "all" as const },
  { label: "已确认", value: "handled" as const },
  { label: "未确认", value: "unhandled" as const },
];

const levelOptions = [
  { label: "全部级别", value: "all" as const },
  { label: "INFO", value: "INFO" as const },
  { label: "WARN", value: "WARN" as const },
  { label: "CRITICAL", value: "CRITICAL" as const },
];

const summaryStats = computed<DashboardStat[]>(() => [
  { label: "告警总数", value: String(alarms.value.length), helper: "当前告警记录" },
  {
    label: "待处理",
    value: String(alarms.value.filter((alarm) => !alarm.handled).length),
    helper: "建议优先关注",
  },
  {
    label: "WARN 告警",
    value: String(alarms.value.filter((alarm) => alarm.alarmLevel === "WARN").length),
    helper: "离线和异常提示",
  },
  {
    label: "已处理",
    value: String(alarms.value.filter((alarm) => alarm.handled).length),
    helper: "人工处理完成数量",
  },
  {
    label: "处理进度",
    value: alarms.value.length ? `${Math.round((alarms.value.filter((alarm) => alarm.handled).length / alarms.value.length) * 100)}%` : "0%",
    helper: "已处理占全部告警比例",
  },
]);

const filteredAlarms = computed(() =>
  alarms.value.filter((alarm) => {
    const matchHandled =
      handledFilter.value === "all" ||
      (handledFilter.value === "handled" && alarm.handled) ||
      (handledFilter.value === "unhandled" && !alarm.handled);

    const matchLevel = levelFilter.value === "all" || alarm.alarmLevel === levelFilter.value;

    return matchHandled && matchLevel;
  }),
);

onMounted(async () => {
  alarms.value = await getAlarmList();
});

async function handleAlarmRecord(alarmId: string) {
  if (handlingAlarmId.value || !canHandleAlarms.value) {
    return;
  }

  handlingAlarmId.value = alarmId;
  try {
    const updatedAlarm = await handleAlarm(alarmId);
    alarms.value = alarms.value.map((alarm) => (alarm.id === alarmId ? updatedAlarm : alarm));
  } finally {
    handlingAlarmId.value = null;
  }
}

function alarmTypeText(alarm: AlarmRecord) {
  if (alarm.alarmType === "SENSOR_OFFLINE") {
    return "传感器离线";
  }
  if (alarm.alarmType === "DEVICE_OFFLINE") {
    return "设备离线";
  }
  if (alarm.alarmType === "COMMAND_FAILED") {
    return "命令失败";
  }
  return "光照异常";
}
</script>
