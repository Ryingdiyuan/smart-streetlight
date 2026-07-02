<template>
  <PanelCard title="关联告警" subtitle="设备异常记录">
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>类型</th>
            <th>级别</th>
            <th>内容</th>
            <th>时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="alarm in alarms" :key="alarm.id">
            <td>{{ alarm.alarmType }}</td>
            <td>
              <StatusBadge :status="getAlarmBadgeStatus(alarm.alarmLevel)" :text="alarm.alarmLevel" />
            </td>
            <td>{{ alarm.alarmContent }}</td>
            <td>
              <div class="table-cell-stack">
                <span>{{ alarm.createdAt }}</span>
                <StatusBadge
                  :status="alarm.handled ? 'info' : 'warning'"
                  :text="alarm.handled ? '已处理' : '待处理'"
                />
              </div>
            </td>
          </tr>
          <tr v-if="!alarms.length">
            <td colspan="4" class="table-empty">当前没有关联告警</td>
          </tr>
        </tbody>
      </table>
    </div>
  </PanelCard>
</template>

<script setup lang="ts">
import PanelCard from "@/components/PanelCard.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import type { AlarmLevel, AlarmRecord } from "@/types/models";

defineProps<{
  alarms: AlarmRecord[];
}>();

function getAlarmBadgeStatus(level: AlarmLevel) {
  switch (level) {
    case "CRITICAL":
    case "WARN":
      return "warning";
    default:
      return "info";
  }
}
</script>
