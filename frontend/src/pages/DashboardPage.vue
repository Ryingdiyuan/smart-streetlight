<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Overview</p>
        <h3>总览大屏</h3>
      </div>
      <p class="section-note">已接入模拟数据、设备快照、最近告警和趋势图，适合作为答辩展示首页。</p>
    </header>

    <div class="stats-grid">
      <StatCard v-for="item in stats" :key="item.label" :stat="item" />
    </div>

    <div class="content-grid two-columns">
      <PanelCard title="重点设备趋势" subtitle="SL-001 / Mock 曲线">
        <div class="chart-header-row">
          <div>
            <strong>{{ featuredDevice.deviceName }}</strong>
            <p class="inline-note">
              {{ featuredDevice.deviceCode }} · {{ featuredDevice.status.toUpperCase() }} ·
              {{ featuredDevice.lampStatus }}
            </p>
          </div>
        </div>
        <TrendLineChart :points="featuredHistory" />
      </PanelCard>

      <PanelCard title="状态分布图" subtitle="在线、离线与路灯状态总览">
        <StatusDonutChart
          :online-count="onlineCount"
          :offline-count="offlineCount"
          :lamp-on-count="lampOnCount"
          :lamp-off-count="lampOffCount"
        />
      </PanelCard>
    </div>

    <div class="content-grid two-columns">
      <PanelCard title="最近告警" subtitle="由 Mock 服务驱动">
        <div v-if="latestAlarms.length" class="alarm-preview-list">
          <div v-for="alarm in latestAlarms" :key="alarm.id" class="alarm-preview-item">
            <div class="list-row">
              <strong>{{ alarm.deviceId }}</strong>
              <StatusBadge
                :status="alarm.handled ? 'info' : 'warning'"
                :text="alarm.handled ? '已处理' : '未处理'"
              />
            </div>
            <span>{{ alarm.alarmContent }}</span>
            <em>{{ alarm.createdAt }}</em>
          </div>
        </div>
        <div v-else class="placeholder-box">当前没有告警数据</div>
      </PanelCard>

      <PanelCard title="设备状态快照" subtitle="总览页快速查看">
        <div class="snapshot-list">
          <div v-for="device in devices" :key="device.id" class="snapshot-item">
            <div>
              <strong>{{ device.deviceName }}</strong>
              <span class="snapshot-meta">{{ device.deviceCode }} · {{ device.location }}</span>
            </div>
            <div class="snapshot-badges">
              <StatusBadge
                :status="device.status"
                :text="device.status === 'online' ? '在线' : '离线'"
              />
              <StatusBadge
                :status="device.lampStatus === 'ON' ? 'success' : 'info'"
                :text="device.lampStatus"
              />
            </div>
          </div>
        </div>
      </PanelCard>
    </div>

    <PanelCard title="最近控制记录" subtitle="便于答辩演示控制闭环">
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>设备编号</th>
              <th>指令</th>
              <th>来源</th>
              <th>结果</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in recentCommands" :key="log.id">
              <td>{{ log.deviceId }}</td>
              <td>{{ log.command }}</td>
              <td>{{ log.source }}</td>
              <td>{{ log.result }}</td>
              <td>{{ log.createdAt }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </PanelCard>

    <PanelCard title="功能规划" subtitle="第一阶段必须完成">
      <ul class="feature-list">
        <li>实时光照监测与状态卡片</li>
        <li>历史趋势图与自动刷新</li>
        <li>设备在线离线统计</li>
        <li>最近告警与控制反馈</li>
      </ul>
    </PanelCard>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import PanelCard from "@/components/PanelCard.vue";
import StatCard from "@/components/StatCard.vue";
import StatusDonutChart from "@/components/StatusDonutChart.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import TrendLineChart from "@/components/TrendLineChart.vue";
import { getDashboardOverview } from "@/services/dashboardService";
import type {
  AlarmRecord,
  CommandLog,
  DashboardStat,
  Device,
  LightHistoryPoint,
} from "@/types/models";

const stats = ref<DashboardStat[]>([]);
const latestAlarms = ref<AlarmRecord[]>([]);
const featuredHistory = ref<LightHistoryPoint[]>([]);
const recentCommands = ref<CommandLog[]>([]);
const devices = ref<Device[]>([]);
const featuredDevice = ref({
  deviceCode: "",
  deviceName: "",
  status: "online",
  lampStatus: "OFF",
} as Pick<Device, "deviceCode" | "deviceName" | "status" | "lampStatus">);

const onlineCount = computed(() => devices.value.filter((item) => item.status === "online").length);
const offlineCount = computed(() => devices.value.filter((item) => item.status === "offline").length);
const lampOnCount = computed(() => devices.value.filter((item) => item.lampStatus === "ON").length);
const lampOffCount = computed(() => devices.value.filter((item) => item.lampStatus === "OFF").length);

onMounted(async () => {
  const overview = await getDashboardOverview();
  stats.value = overview.stats;
  latestAlarms.value = overview.latestAlarms;
  featuredHistory.value = overview.featuredHistory;
  devices.value = overview.devices;
  recentCommands.value = overview.recentCommands;
  featuredDevice.value = overview.featuredDevice;
});
</script>
