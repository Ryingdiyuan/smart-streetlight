<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Alarms</p>
        <h3>告警日志</h3>
      </div>
      <p class="section-note">当前先搭告警列表和处理状态展示，后续联动后端接口。</p>
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
              <th>设备编号</th>
              <th>类型</th>
              <th>级别</th>
              <th>内容</th>
              <th>处理状态</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="alarm in filteredAlarms" :key="alarm.id">
              <td>{{ alarm.id }}</td>
              <td>{{ alarm.deviceId }}</td>
              <td>{{ alarm.alarmType }}</td>
              <td>
                <StatusBadge
                  :status="alarm.alarmLevel === 'CRITICAL' ? 'warning' : alarm.alarmLevel === 'WARN' ? 'warning' : 'info'"
                  :text="alarm.alarmLevel"
                />
              </td>
              <td>{{ alarm.alarmContent }}</td>
              <td>
                <StatusBadge
                  :status="alarm.handled ? 'info' : 'warning'"
                  :text="alarm.handled ? '已处理' : '未处理'"
                />
              </td>
              <td>{{ alarm.createdAt }}</td>
            </tr>
            <tr v-if="!filteredAlarms.length">
              <td colspan="7" class="table-empty">当前没有告警记录</td>
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
import { getAlarmList } from "@/services/alarmService";
import type { AlarmLevel, AlarmRecord, DashboardStat } from "@/types/models";

const alarms = ref<AlarmRecord[]>([]);
const handledFilter = ref<"all" | "handled" | "unhandled">("all");
const levelFilter = ref<"all" | AlarmLevel>("all");

const handledOptions = [
  { label: "全部状态", value: "all" as const },
  { label: "已处理", value: "handled" as const },
  { label: "未处理", value: "unhandled" as const },
];

const levelOptions = [
  { label: "全部级别", value: "all" as const },
  { label: "INFO", value: "INFO" as const },
  { label: "WARN", value: "WARN" as const },
  { label: "CRITICAL", value: "CRITICAL" as const },
];

const summaryStats = computed<DashboardStat[]>(() => [
  { label: "告警总数", value: String(alarms.value.length), helper: "当前模拟告警记录" },
  {
    label: "未处理",
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
    helper: "便于演示处置结果",
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
</script>
