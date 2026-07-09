<template>
  <div class="page-stack">
    <SectionCard title="告警筛选" subtitle="优先处理未处理告警">
      <div class="chip-row">
        <button
          v-for="item in filters"
          :key="item.value"
          class="chip-button"
          :class="{ 'chip-button-active': handledFilter === item.value }"
          type="button"
          @click="handledFilter = item.value"
        >
          {{ item.label }}
        </button>
      </div>
    </SectionCard>

    <SectionCard title="告警列表" :subtitle="`共 ${filteredAlarms.length} 条告警`">
      <div v-if="loading" class="mobile-skeleton-grid">
        <div v-for="item in 3" :key="item" class="mobile-skeleton-card"></div>
      </div>
      <div v-else class="compact-list">
        <article v-for="alarm in filteredAlarms" :key="alarm.id" class="compact-item">
          <div class="compact-item-top">
            <strong>{{ alarm.deviceId }}</strong>
            <StatusPill :tone="alarm.handled ? 'neutral' : 'warning'" :text="alarm.handled ? '已处理' : '待处理'" />
          </div>
          <p>{{ alarm.alarmContent }}</p>
          <span>{{ alarm.createdAt }}</span>
          <button
            v-if="canHandleAlarms && !alarm.handled"
            class="action-button"
            type="button"
            @click="handle(alarm.id)"
          >
            标记已处理
          </button>
        </article>
        <p v-if="!filteredAlarms.length" class="placeholder-text">当前没有符合条件的告警。</p>
      </div>
    </SectionCard>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import SectionCard from "@/components/SectionCard.vue";
import StatusPill from "@/components/StatusPill.vue";
import { getAlarmList, handleAlarm } from "@/services/api/alarmService";
import { can } from "@/services/permissions";
import type { AlarmRecord } from "@/types/models";

const alarms = ref<AlarmRecord[]>([]);
const handledFilter = ref<"all" | "pending" | "done">("pending");
const loading = ref(true);
const canHandleAlarms = can("handleAlarms");

const filters = [
  { label: "待处理", value: "pending" as const },
  { label: "全部", value: "all" as const },
  { label: "已处理", value: "done" as const },
];

const filteredAlarms = computed(() =>
  alarms.value.filter((alarm) => {
    if (handledFilter.value === "pending") {
      return !alarm.handled;
    }
    if (handledFilter.value === "done") {
      return alarm.handled;
    }
    return true;
  }),
);

async function loadAlarms() {
  loading.value = true;
  try {
    alarms.value = await getAlarmList();
  } finally {
    loading.value = false;
  }
}

async function handle(alarmId: string) {
  await handleAlarm(alarmId);
  await loadAlarms();
}

onMounted(loadAlarms);
</script>
