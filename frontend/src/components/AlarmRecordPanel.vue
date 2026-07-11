<template>
  <PanelCard title="关联告警" subtitle="设备异常记录">
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>类型</th>
            <th>级别</th>
            <th>内容</th>
            <th>处理进度</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="alarm in alarms" :key="alarm.id">
            <td>{{ alarmTypeText(alarm) }}</td>
            <td>
              <StatusBadge :status="getAlarmBadgeStatus(alarm.alarmLevel)" :text="alarm.alarmLevel" />
            </td>
            <td>{{ alarm.alarmContent }}</td>
            <td>
              <div class="table-cell-stack">
                <span>告警时间：{{ alarm.createdAt }}</span>
                <StatusBadge
                  :status="alarm.handled ? 'info' : 'warning'"
                  :text="alarm.handled ? '已处理' : '待处理'"
                />
                <span v-if="alarm.handled && alarm.handledAt" class="inline-note">处理时间：{{ alarm.handledAt }}</span>
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
