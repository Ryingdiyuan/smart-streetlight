<template>
  <PanelCard title="控制日志" subtitle="最近执行结果">
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>指令</th>
            <th>来源</th>
            <th>结果</th>
            <th>时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in logs" :key="log.id">
            <td>{{ log.command }}</td>
            <td>{{ log.source }}</td>
            <td>
              <StatusBadge :status="getCommandBadgeStatus(log.result)" :text="log.result" />
            </td>
            <td>{{ log.createdAt }}</td>
          </tr>
          <tr v-if="!logs.length">
            <td colspan="4" class="table-empty">当前没有控制日志</td>
          </tr>
        </tbody>
      </table>
    </div>
  </PanelCard>
</template>

<script setup lang="ts">
import PanelCard from "@/components/PanelCard.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import type { CommandLog } from "@/types/models";

defineProps<{
  logs: CommandLog[];
}>();

function getCommandBadgeStatus(result: CommandLog["result"]) {
  switch (result) {
    case "success":
      return "success";
    case "pending":
      return "warning";
    default:
      return "offline";
  }
}
</script>
