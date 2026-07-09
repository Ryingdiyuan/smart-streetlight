<template>
  <div class="page-stack">
    <div v-if="loading" class="mobile-skeleton-grid">
      <div v-for="item in 4" :key="item" class="mobile-skeleton-card"></div>
    </div>

    <template v-else>
      <div class="stats-grid">
        <MetricCard v-for="item in stats" :key="item.label" :stat="item" />
      </div>

      <SectionCard title="快捷入口" subtitle="单手操作优先">
        <div class="quick-grid">
          <RouterLink v-for="item in quickLinks" :key="item.to" :to="item.to" class="quick-link">
            <strong>{{ item.title }}</strong>
            <span>{{ item.description }}</span>
          </RouterLink>
        </div>
      </SectionCard>

      <SectionCard title="重点设备" subtitle="默认展示第一台设备趋势">
        <div class="featured-device">
          <div>
            <p>{{ featuredDevice.deviceCode }}</p>
            <h3>{{ featuredDevice.deviceName }}</h3>
          </div>
          <StatusPill
            :tone="featuredDevice.status === 'online' ? 'success' : 'danger'"
            :text="featuredDevice.status === 'online' ? '在线' : '离线'"
          />
        </div>
        <LightTrendChart :points="featuredHistory" />
      </SectionCard>

      <SectionCard title="最近告警" subtitle="未处理告警优先展示">
        <div v-if="latestAlarms.length" class="compact-list">
          <article v-for="alarm in latestAlarms" :key="alarm.id" class="compact-item">
            <div class="compact-item-top">
              <strong>{{ alarm.deviceId }}</strong>
              <StatusPill :tone="alarm.handled ? 'neutral' : 'warning'" :text="alarm.handled ? '已处理' : '待处理'" />
            </div>
            <p>{{ alarm.alarmContent }}</p>
            <span>{{ alarm.createdAt }}</span>
          </article>
        </div>
        <p v-else class="placeholder-text">当前没有告警数据。</p>
      </SectionCard>

      <SectionCard title="最近控制记录" subtitle="展示闭环联动情况">
        <div v-if="recentCommands.length" class="compact-list">
          <article v-for="log in recentCommands" :key="log.id" class="compact-item">
            <div class="compact-item-top">
              <strong>{{ log.deviceId }}</strong>
              <StatusPill
                :tone="log.result === 'success' ? 'success' : log.result === 'failed' ? 'danger' : 'warning'"
                :text="log.result"
              />
            </div>
            <p>{{ log.command }} · {{ log.source === "manual" ? "人工" : "自动" }}</p>
            <span>{{ log.createdAt }}</span>
          </article>
        </div>
        <p v-else class="placeholder-text">当前没有控制记录。</p>
      </SectionCard>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import LightTrendChart from "@/components/LightTrendChart.vue";
import MetricCard from "@/components/MetricCard.vue";
import SectionCard from "@/components/SectionCard.vue";
import StatusPill from "@/components/StatusPill.vue";
import { getDashboardOverview } from "@/services/api/dashboardService";
import type {
  AlarmRecord,
  CommandLog,
  DashboardStat,
  Device,
  LightHistoryPoint,
} from "@/types/models";

const loading = ref(true);
const stats = ref<DashboardStat[]>([]);
const latestAlarms = ref<AlarmRecord[]>([]);
const featuredHistory = ref<LightHistoryPoint[]>([]);
const recentCommands = ref<CommandLog[]>([]);
const featuredDevice = ref({
  deviceCode: "--",
  deviceName: "暂无设备",
  status: "offline",
  lampStatus: "OFF",
} as Pick<Device, "deviceCode" | "deviceName" | "status" | "lampStatus">);

const quickLinks = [
  { to: "/devices", title: "设备列表", description: "查看状态与控制" },
  { to: "/map", title: "设备地图", description: "快速定位在线情况" },
  { to: "/alarms", title: "告警中心", description: "处理异常与离线" },
  { to: "/agent", title: "智能问答", description: "获取运维建议" },
];

onMounted(async () => {
  try {
    const overview = await getDashboardOverview();
    stats.value = overview.stats;
    latestAlarms.value = overview.latestAlarms;
    featuredHistory.value = overview.featuredHistory;
    recentCommands.value = overview.recentCommands.slice(0, 4);
    featuredDevice.value = overview.featuredDevice;
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.stats-grid,
.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.quick-link {
  display: grid;
  gap: 6px;
  min-height: 104px;
  padding: 16px;
  border-radius: 20px;
  color: inherit;
  text-decoration: none;
  background: var(--surface-subtle);
  border: 1px solid var(--border-soft);
}

.quick-link strong {
  color: var(--text-primary);
  font-size: 15px;
}

.quick-link span {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.featured-device,
.compact-item-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.featured-device p,
.featured-device h3,
.compact-item p,
.compact-item span {
  margin: 0;
}

.featured-device p {
  font-size: 11px;
  color: var(--accent);
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.featured-device h3 {
  margin-top: 4px;
  font-size: 18px;
}

.compact-list {
  display: grid;
  gap: 10px;
}

.compact-item {
  display: grid;
  gap: 8px;
  padding: 14px;
  border-radius: 18px;
  background: var(--surface-inner);
  border: 1px solid var(--border-soft);
}

.compact-item p {
  color: var(--text-primary);
  line-height: 1.6;
}

.compact-item span {
  font-size: 12px;
  color: var(--text-muted);
}
</style>
