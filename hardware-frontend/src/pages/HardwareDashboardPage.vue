<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Hardware Console</p>
        <h3>硬件联调控制台</h3>
      </div>
      <p class="section-note">
        独立承接后续硬件接入、MQTT 联调与模拟验证，不再与软件业务前端混合展示。
      </p>
    </header>

    <div class="stats-grid">
      <StatCard v-for="item in stats" :key="item.label" :stat="item" />
    </div>

    <div class="content-grid two-columns">
      <PanelCard title="当前职责" subtitle="这个前端只服务硬件接入和设备联调">
        <div class="detail-summary-grid">
          <div class="summary-box">
            <strong>MQTT Broker</strong>
            <span>查看连接状态，修改联调参数。</span>
          </div>
          <div class="summary-box">
            <strong>设备模拟</strong>
            <span>启动、停止、编辑模拟设备的运行参数。</span>
          </div>
          <div class="summary-box">
            <strong>运行日志</strong>
            <span>定位联调异常、指令接收和上报发送问题。</span>
          </div>
        </div>
      </PanelCard>

      <PanelCard title="功能入口" subtitle="后续硬件联调统一在本项目完成">
        <div class="software-entry-list">
          <RouterLink class="software-entry-card" to="/simulator">
            <strong>进入模拟器控制台</strong>
            <span>执行设备模拟、Broker 配置和日志排查。</span>
          </RouterLink>
        </div>
      </PanelCard>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import PanelCard from "@/components/PanelCard.vue";
import StatCard from "@/components/StatCard.vue";
import type { DashboardStat } from "@/types/models";

const stats = computed<DashboardStat[]>(() => [
  { label: "项目定位", value: "硬件联调", helper: "独立于软件业务前端运行" },
  { label: "主要页面", value: "1", helper: "当前保留模拟器控制台" },
  { label: "访问角色", value: "管理员", helper: "与后端模拟器接口权限保持一致" },
]);
</script>

<style scoped>
.software-entry-list {
  display: grid;
  gap: 12px;
}

.software-entry-card {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid rgba(127, 203, 255, 0.12);
  background: rgba(5, 18, 32, 0.42);
  color: inherit;
  text-decoration: none;
  transition: 0.18s ease;
}

.software-entry-card strong {
  color: #e2e8f0;
}

.software-entry-card span {
  color: #94a3b8;
  line-height: 1.6;
}

.software-entry-card:hover {
  transform: translateY(-1px);
  border-color: rgba(56, 213, 255, 0.32);
  background: rgba(10, 34, 56, 0.7);
}
</style>
